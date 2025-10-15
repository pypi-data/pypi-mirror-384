#!/usr/bin/env python3
"""
MEMG Core MCP Server - Production Implementation
Clean, efficient server with singleton client management and FastMCP compatibility.
"""

import logging
import os
from typing import Any, Dict, Optional
from pydantic import Field

from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from memg_core import __version__
from memg_core.api.public import MemgClient
from memg_core.core.yaml_translator import YamlTranslator

# Import result_cleaner from same directory
try:
    from .result_cleaner import clean_and_format
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from result_cleaner import clean_and_format

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================= GLOBAL CLIENT SINGLETON =========================

# Global instances - initialized once at module level
_client: Optional[MemgClient] = None
_yaml_translator: Optional[YamlTranslator] = None

def _initialize_client() -> None:
    """Initialize the global MemgClient and YamlTranslator singletons."""
    global _client, _yaml_translator

    if _client is not None:
        logger.info("Client already initialized, skipping")
        return

    # Get configuration from environment
    yaml_path = os.getenv("MEMG_YAML_SCHEMA")
    db_path = os.getenv("MEMG_DB_PATH")

    if not yaml_path:
        raise RuntimeError("MEMG_YAML_SCHEMA environment variable is required")
    if not db_path:
        raise RuntimeError("MEMG_DB_PATH environment variable is required")

    logger.info(f"Initializing MemgClient: yaml={yaml_path}, db={db_path}")

    try:
        # Ensure database path exists
        os.makedirs(db_path, exist_ok=True)

        # Initialize client and YAML translator
        _client = MemgClient(yaml_path=yaml_path, db_path=db_path)
        _yaml_translator = YamlTranslator(yaml_path)

        logger.info("✅ MemgClient and YamlTranslator initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize client: {e}", exc_info=True)
        raise RuntimeError(f"Client initialization failed: {e}")

def get_client() -> MemgClient:
    """Get the global MemgClient singleton."""
    if _client is None:
        raise RuntimeError("Client not initialized - call _initialize_client() first")
    return _client

def get_yaml_translator() -> YamlTranslator:
    """Get the global YamlTranslator singleton."""
    if _yaml_translator is None:
        raise RuntimeError("YamlTranslator not initialized - call _initialize_client() first")
    return _yaml_translator

def close_client() -> None:
    """Close the global client singleton."""
    global _client, _yaml_translator
    if _client:
        try:
            _client.close()
            logger.info("✅ Client closed successfully")
        except Exception as e:
            logger.error(f"⚠️ Error closing client: {e}")
        finally:
            _client = None
            _yaml_translator = None

# ========================= YAML SCHEMA HELPERS =========================

def _get_entity_description(memory_type: str, yaml_translator: YamlTranslator) -> str:
    """Get entity description from YAML schema."""
    try:
        entities_map = yaml_translator._entities_map()
        entity_spec = entities_map.get(memory_type.lower())
        if entity_spec and "description" in entity_spec:
            return f"Add a {memory_type}: {entity_spec['description']}"
    except Exception:
        pass
    return f"Add a {memory_type} memory"

def _get_entity_field_info(memory_type: str, yaml_translator: YamlTranslator) -> str:
    """Get field information for entity from YAML schema."""
    try:
        entities_map = yaml_translator._entities_map()
        entity_spec = entities_map.get(memory_type.lower())
        if not entity_spec:
            return f"Data fields for {memory_type}"

        # Get all fields including inherited ones
        all_fields = yaml_translator._resolve_inherited_fields(entity_spec)
        system_fields = yaml_translator._get_system_fields(entity_spec)

        # Filter out system fields for user payload
        user_fields = []
        for field_name, field_def in all_fields.items():
            if field_name not in system_fields:
                field_info = f"{field_name}"
                if isinstance(field_def, dict):
                    field_type = field_def.get("type", "string")
                    required = field_def.get("required", False)
                    choices = field_def.get("choices")
                    default = field_def.get("default")

                    # Build field description
                    parts = [f"({field_type}"]
                    if required:
                        parts.append("required")
                    if choices:
                        parts.append(f"choices: {choices}")
                    if default is not None:
                        parts.append(f"default: {default}")
                    parts.append(")")

                    field_info += " " + "".join(parts)

                user_fields.append(field_info)

        if user_fields:
            return f"Data fields for {memory_type}: {', '.join(user_fields)}"
    except Exception as e:
        logger.warning(f"Failed to get field info for {memory_type}: {e}")

    return f"Data fields for {memory_type}"

def _get_valid_predicates_for_relationship(from_type: str, to_type: str, yaml_translator: YamlTranslator) -> list[str]:
    """Get valid predicates between two entity types from YAML schema."""
    try:
        relations = yaml_translator.get_relations_for_source(from_type)
        valid_predicates = []
        for rel in relations:
            if rel['target'] == to_type.lower():
                valid_predicates.append(rel['predicate'])
        return valid_predicates
    except Exception as e:
        logger.warning(f"Failed to get valid predicates for {from_type} -> {to_type}: {e}")
        return []

def _get_all_valid_predicates_for_entity(entity_type: str, yaml_translator: YamlTranslator) -> Dict[str, list[str]]:
    """Get all valid predicates for an entity type, organized by target type."""
    try:
        relations = yaml_translator.get_relations_for_source(entity_type)
        predicates_by_target = {}
        for rel in relations:
            target = rel['target']
            predicate = rel['predicate']
            if target not in predicates_by_target:
                predicates_by_target[target] = []
            predicates_by_target[target].append(predicate)
        return predicates_by_target
    except Exception as e:
        logger.warning(f"Failed to get all predicates for {entity_type}: {e}")
        return {}

# ========================= TOOL REGISTRATION =========================

def register_search_tools(app: FastMCP) -> None:
    """Register search-related tools."""

    @app.tool("search_memories", description="Search memories using semantic vector search with graph expansion.")
    def search_memories(
        query: str = Field(..., description="Search query text"),
        user_id: str = Field(..., description="User identifier (required for data isolation)"),
        limit: int = Field(3, description="Maximum results (default: 3, max: 50)"),
        memory_type: Optional[str] = Field(None, description="Filter by memory type (optional)"),
        neighbor_limit: int = Field(3, description="Max graph neighbors per result (default: 3)"),
        hops: int = Field(1, description="Graph traversal depth (default: 1)"),
        score_threshold: Optional[float] = Field(None, description="Minimum similarity score threshold (0.0-1.0)"),
        decay_rate: Optional[float] = Field(None, description="Score decay factor per hop (1.0 = no decay)"),
        decay_threshold: Optional[float] = Field(None, description="Explicit neighbor score threshold"),
        include_details: str = Field("self", description="Detail level: 'self' (seeds full, neighbors anchor), 'all' (both full), 'none' (both anchor)"),
        datetime_format: Optional[str] = Field(None, description="Datetime format string (e.g., '%Y-%m-%d %H:%M:%S')")
    ) -> Dict[str, Any]:
        """Search memories - direct API call."""

        logger.info(f"SEARCH: query='{query}', user_id='{user_id}', limit={limit}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required", "memories": []}
        if not query or not query.strip():
            return {"error": "query cannot be empty", "memories": []}

        # Limit protection
        limit = min(limit, 50)

        try:
            client = get_client()
            result = client.search(
                query=query.strip(),
                user_id=user_id.strip(),
                memory_type=memory_type.lower().strip() if memory_type else None,
                limit=limit,
                neighbor_limit=neighbor_limit,
                hops=hops,
                score_threshold=score_threshold,
                decay_rate=decay_rate,
                decay_threshold=decay_threshold,
                include_details=include_details,
                datetime_format=datetime_format
            )

            logger.info(f"Search result: {len(result.memories)} memories, {len(result.neighbors)} neighbors")

            # Convert to JSON-serializable format then clean and format to markdown
            result_dict = result.model_dump(mode='json')
            result_dict["query"] = query  # Ensure query is in the dict
            
            markdown = clean_and_format(result_dict, neighbor_limit=neighbor_limit)
            
            # Return as dict for MCP compatibility
            return {"result": markdown}

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return {
                "error": f"Search failed: {str(e)}",
                "memories": [],
                "query": query,
                "user_id": user_id
            }

def register_get_tools(app: FastMCP) -> None:
    """Register get-related tools."""

    @app.tool("get_memory_by_hrid", description="Get a single memory by HRID with optional neighbor expansion.")
    def get_memory_by_hrid(
        hrid: str = Field(..., description="Memory HRID (human readable identifier)"),
        user_id: str = Field(..., description="User identifier (for ownership verification)"),
        memory_type: Optional[str] = Field(None, description="Memory type (optional)"),
        include_neighbors: bool = Field(False, description="Include graph neighbors (default: false)"),
        hops: int = Field(1, description="Graph traversal depth when include_neighbors=true (default: 1)"),
        neighbor_limit: int = Field(5, description="Maximum neighbors to return per hop (default: 5)"),
        relation_types: Optional[list[str]] = Field(None, description="Filter by specific relationship types")
    ) -> Dict[str, Any]:
        """Get memory by HRID - direct API call."""

        logger.info(f"GET_MEMORY: hrid='{hrid}', user_id='{user_id}', include_neighbors={include_neighbors}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required"}
        if not hrid or not hrid.strip():
            return {"error": "hrid is required"}

        try:
            client = get_client()
            result = client.get_memory(
                hrid=hrid.strip(),
                user_id=user_id.strip(),
                memory_type=memory_type,
                include_neighbors=include_neighbors,
                hops=hops,
                relation_types=relation_types,
                neighbor_limit=neighbor_limit
            )

            if result is None:
                return {
                    "result": "Memory not found",
                    "hrid": hrid,
                    "memory": None
                }

            # Convert to JSON-serializable format
            result_dict = result.model_dump(mode='json')
            memories = result_dict.get("memories", [])
            neighbors = result_dict.get("neighbors", [])

            if not memories:
                return {
                    "result": "Memory not found",
                    "hrid": hrid,
                    "memory": None
                }

            # Clean and format to markdown
            markdown = clean_and_format(result_dict, neighbor_limit=neighbor_limit)
            return {"result": markdown}

        except Exception as e:
            logger.error(f"Get memory failed: {e}", exc_info=True)
            return {
                "error": f"Get memory failed: {str(e)}",
                "hrid": hrid,
                "memory": None
            }

    @app.tool("list_memories_by_type", description="List multiple memories with filtering and optional graph expansion.")
    def list_memories_by_type(
        user_id: str = Field(..., description="User identifier"),
        memory_type: Optional[str] = Field(None, description="Filter by memory type (optional)"),
        limit: int = Field(50, description="Maximum results (default: 50)"),
        offset: int = Field(0, description="Skip first N results for pagination (default: 0)"),
        include_neighbors: bool = Field(False, description="Include graph neighbors (default: false)"),
        hops: int = Field(1, description="Graph traversal depth when include_neighbors=true (default: 1)"),
        filters: Optional[Dict[str, Any]] = Field(None, description="Additional field-based filters (optional)")
    ) -> Dict[str, Any]:
        """List memories by type - direct API call."""

        logger.info(f"LIST_MEMORIES: user_id='{user_id}', memory_type='{memory_type}', limit={limit}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required", "memories": []}

        try:
            client = get_client()
            result = client.get_memories(
                user_id=user_id.strip(),
                memory_type=memory_type,
                filters=filters,
                limit=limit,
                offset=offset,
                include_neighbors=include_neighbors,
                hops=hops
            )

            # Convert to JSON-serializable format
            result_dict = result.model_dump(mode='json')
            memories = result_dict.get("memories", [])
            neighbors = result_dict.get("neighbors", [])

            # Clean and format to markdown (use default neighbor_limit=3)
            markdown = clean_and_format(result_dict, neighbor_limit=3)
            return {"result": markdown}

        except Exception as e:
            logger.error(f"List memories failed: {e}", exc_info=True)
            return {
                "error": f"List memories failed: {str(e)}",
                "memories": [],
                "user_id": user_id
            }

def register_add_tools(app: FastMCP) -> None:
    """Register dynamic add_* tools for each memory type."""

    try:
        yaml_translator = get_yaml_translator()
        entity_types = yaml_translator.get_entity_types()

        # Skip memo - it's a base type for inheritance only
        filtered_types = [t for t in entity_types if t != "memo"]
        logger.info(f"Registering add tools for types: {filtered_types}")

        for memory_type in filtered_types:
            _register_add_tool(app, memory_type, yaml_translator)

    except Exception as e:
        logger.error(f"Failed to register add tools: {e}", exc_info=True)
        raise

def _register_add_tool(app: FastMCP, memory_type: str, yaml_translator: YamlTranslator) -> None:
    """Register a single add_* tool for a memory type."""

    tool_name = f"add_{memory_type}"

    # Get dynamic description and field info from YAML
    description = _get_entity_description(memory_type, yaml_translator)
    field_info = _get_entity_field_info(memory_type, yaml_translator)

    @app.tool(tool_name, description=description)
    def add_tool(
        user_id: str = Field(..., description="User identifier - separates user's memories from each other"),
        data: Dict[str, Any] = Field(..., description=field_info)
    ) -> Dict[str, Any]:
        """Add memory - direct API call."""

        logger.info(f"ADD_{memory_type.upper()}: user_id='{user_id}', data={data}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {
                "error": "user_id is required",
                "memory_type": memory_type
            }

        try:
            client = get_client()
            hrid = client.add_memory(
                memory_type=memory_type,
                payload=data,
                user_id=user_id.strip()
            )

            logger.info(f"Successfully added {memory_type} with HRID: {hrid}")

            return {
                "result": f"{memory_type.title()} added successfully",
                "hrid": hrid,
                "memory_type": memory_type
            }

        except Exception as e:
            logger.error(f"Add {memory_type} failed: {e}", exc_info=True)
            return {
                "error": f"Failed to add {memory_type}: {str(e)}",
                "memory_type": memory_type,
                "user_id": user_id
            }

def register_other_tools(app: FastMCP) -> None:
    """Register other tools (delete, update, relationships, system info)."""

    @app.tool("delete_memory", description="Delete a memory by HRID.")
    def delete_memory(
        memory_id: str = Field(..., description="Memory HRID (human readable identifier)"),
        user_id: str = Field(..., description="User identifier (for ownership verification)")
    ) -> Dict[str, Any]:
        """Delete memory - direct API call."""

        logger.info(f"DELETE_MEMORY: hrid='{memory_id}', user_id='{user_id}'")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required"}
        if not memory_id or not memory_id.strip():
            return {"error": "memory_id is required"}

        try:
            client = get_client()
            success = client.delete_memory(
                hrid=memory_id.strip(),
                user_id=user_id.strip()
            )

            return {
                "result": "Memory deleted" if success else "Delete failed",
                "hrid": memory_id,
                "deleted": success
            }

        except Exception as e:
            logger.error(f"Delete memory failed: {e}", exc_info=True)
            return {
                "error": f"Failed to delete memory: {str(e)}",
                "hrid": memory_id
            }

    @app.tool("update_memory", description="Update memory with partial payload changes (patch-style update).")
    def update_memory(
        hrid: str = Field(..., description="Memory HRID (human readable identifier)"),
        payload_updates: Dict[str, Any] = Field(..., description="Payload updates (only fields you want to change)"),
        user_id: str = Field(..., description="User identifier"),
        memory_type: Optional[str] = Field(None, description="Memory type (optional)")
    ) -> Dict[str, Any]:
        """Update memory - direct API call."""

        logger.info(f"UPDATE_MEMORY: hrid='{hrid}', user_id='{user_id}', updates={payload_updates}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required"}
        if not hrid or not hrid.strip():
            return {"error": "hrid is required"}
        if not payload_updates:
            return {"error": "payload_updates cannot be empty"}

        try:
            client = get_client()
            success = client.update_memory(
                hrid=hrid.strip(),
                payload_updates=payload_updates,
                user_id=user_id.strip(),
                memory_type=memory_type
            )

            return {
                "result": "Memory updated successfully" if success else "Update failed",
                "hrid": hrid,
                "updated": success
            }

        except Exception as e:
            logger.error(f"Update memory failed: {e}", exc_info=True)
            return {
                "error": f"Failed to update memory: {str(e)}",
                "hrid": hrid
            }

    @app.tool("add_relationship", description="Add a relationship between two memories.")
    def add_relationship(
        from_memory_hrid: str = Field(..., description="Source memory HRID"),
        to_memory_hrid: str = Field(..., description="Target memory HRID"),
        relation_type: str = Field(..., description="Relationship type"),
        from_memory_type: str = Field(..., description="Source entity type"),
        to_memory_type: str = Field(..., description="Target entity type"),
        user_id: str = Field(..., description="User identifier"),
    ) -> Dict[str, Any]:
        """Add relationship - direct API call."""

        logger.info(f"ADD_RELATIONSHIP: {from_memory_hrid} -[{relation_type}]-> {to_memory_hrid}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required"}

        required_fields = [from_memory_hrid, to_memory_hrid, relation_type, from_memory_type, to_memory_type]
        if not all(field and field.strip() for field in required_fields):
            return {"error": "All relationship fields are required"}

        try:
            client = get_client()
            client.add_relationship(
                from_memory_hrid=from_memory_hrid.strip(),
                to_memory_hrid=to_memory_hrid.strip(),
                relation_type=relation_type.strip(),
                from_memory_type=from_memory_type.strip(),
                to_memory_type=to_memory_type.strip(),
                user_id=user_id.strip(),
            )

            return {
                "result": "Relationship added successfully",
                "from_hrid": from_memory_hrid,
                "to_hrid": to_memory_hrid,
                "relation_type": relation_type
            }

        except Exception as e:
            logger.error(f"Add relationship failed: {e}", exc_info=True)

            # Enhanced error message with valid predicates
            error_msg = str(e)
            enhanced_error = {
                "error": f"Failed to add relationship: {error_msg}",
                "from_hrid": from_memory_hrid,
                "to_hrid": to_memory_hrid,
                "relation_type": relation_type
            }

            # If it's a validation error, provide helpful suggestions
            if "Invalid relationship predicate" in error_msg or "predicate" in error_msg.lower():
                try:
                    yaml_translator = get_yaml_translator()

                    # Get valid predicates for this specific relationship
                    valid_predicates = _get_valid_predicates_for_relationship(
                        from_memory_type.strip(), to_memory_type.strip(), yaml_translator
                    )

                    if valid_predicates:
                        enhanced_error["valid_predicates_for_this_relationship"] = valid_predicates
                        enhanced_error["suggestion"] = f"Valid predicates from {from_memory_type} to {to_memory_type}: {', '.join(valid_predicates)}"
                    else:
                        # No direct relationship exists, show all possible relationships for source type
                        all_predicates = _get_all_valid_predicates_for_entity(from_memory_type.strip(), yaml_translator)
                        if all_predicates:
                            enhanced_error["valid_relationships_for_source"] = all_predicates
                            enhanced_error["suggestion"] = f"No direct relationship allowed from {from_memory_type} to {to_memory_type}. Valid relationships for {from_memory_type}: {dict(all_predicates)}"
                        else:
                            enhanced_error["suggestion"] = f"Entity type '{from_memory_type}' has no outgoing relationships defined in the schema"

                except Exception as schema_error:
                    logger.warning(f"Failed to get relationship suggestions: {schema_error}")
                    enhanced_error["suggestion"] = "Check the YAML schema for valid relationship types between these entity types"

            return enhanced_error

    @app.tool("delete_relationship", description="Delete a relationship between two memories.")
    def delete_relationship(
        from_memory_hrid: str = Field(..., description="Source memory HRID"),
        to_memory_hrid: str = Field(..., description="Target memory HRID"),
        relation_type: str = Field(..., description="Relationship type"),
        user_id: str = Field(..., description="User identifier"),
        from_memory_type: Optional[str] = Field(None, description="Source entity type (optional)"),
        to_memory_type: Optional[str] = Field(None, description="Target entity type (optional)")
    ) -> Dict[str, Any]:
        """Delete relationship - direct API call."""

        logger.info(f"DELETE_RELATIONSHIP: {from_memory_hrid} -[{relation_type}]-> {to_memory_hrid}")

        # Basic validation
        if not user_id or not user_id.strip():
            return {"error": "user_id is required"}

        required_fields = [from_memory_hrid, to_memory_hrid, relation_type]
        if not all(field and field.strip() for field in required_fields):
            return {"error": "from_memory_hrid, to_memory_hrid, and relation_type are required"}

        try:
            client = get_client()
            success = client.delete_relationship(
                from_memory_hrid=from_memory_hrid.strip(),
                to_memory_hrid=to_memory_hrid.strip(),
                relation_type=relation_type.strip(),
                from_memory_type=from_memory_type.strip() if from_memory_type else None,
                to_memory_type=to_memory_type.strip() if to_memory_type else None,
                user_id=user_id.strip()
            )

            return {
                "result": "Relationship deleted successfully" if success else "Relationship not found",
                "from_hrid": from_memory_hrid,
                "to_hrid": to_memory_hrid,
                "relation_type": relation_type,
                "deleted": success
            }

        except Exception as e:
            logger.error(f"Delete relationship failed: {e}", exc_info=True)
            return {
                "error": f"Failed to delete relationship: {str(e)}",
                "from_hrid": from_memory_hrid,
                "to_hrid": to_memory_hrid,
                "relation_type": relation_type
            }

    @app.tool("get_system_info", description="Get system information and available tools.")
    def get_system_info(random_string: str = "") -> Dict[str, Any]:
        """Get system info."""

        try:
            from memg_core.core.types import get_entity_type_enum

            entity_enum = get_entity_type_enum()
            entity_types = [e.value for e in entity_enum]

            yaml_schema = os.getenv("MEMG_YAML_SCHEMA", "not configured")

            return {
                "system_type": "MEMG Core (Production)",
                "version": __version__,
                "functions": [
                    "search_memories", "get_memory_by_hrid", "list_memories_by_type",
                    "delete_memory", "update_memory", "add_relationship", "delete_relationship",
                    "get_system_info"
                ] + [f"add_{t}" for t in entity_types if t != "memo"],
                "memory_types": entity_types,
                "yaml_schema": yaml_schema,
                "note": "Production server with singleton client management"
            }

        except Exception as e:
            logger.error(f"Get system info failed: {e}", exc_info=True)
            return {
                "system_type": "MEMG Core (Production)",
                "version": __version__,
                "error": f"Failed to get schema info: {str(e)}",
                "yaml_schema": os.getenv("MEMG_YAML_SCHEMA", "not configured")
            }

# ========================= APP CREATION =========================

def create_app() -> FastMCP:
    """Create and configure the FastMCP app."""

    # Initialize client singleton ONCE at app creation
    _initialize_client()

    app = FastMCP()

    # Register all tools
    try:
        register_search_tools(app)
        register_get_tools(app)
        register_add_tools(app)
        register_other_tools(app)
        logger.info("✅ All tools registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register tools: {e}")
        raise

    # Health endpoint for Docker
    @app.custom_route("/health", methods=["GET"])
    async def health(_req):
        return JSONResponse({
            "service": "MEMG Core MCP Server (Production)",
            "version": __version__,
            "status": "healthy",
            "yaml_schema": os.getenv("MEMG_YAML_SCHEMA", "not configured"),
            "db_path": os.getenv("MEMG_DB_PATH", "not configured")
        }, status_code=200)

    return app

# ========================= DATABASE SETUP HELPERS =========================

def get_data_path_from_args() -> str:
    """Get data path from CLI arguments or auto-detect."""
    import sys
    from pathlib import Path
    
    # Check for --data-path argument
    if "--data-path" in sys.argv:
        idx = sys.argv.index("--data-path")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    
    # Auto-detect: look for data/ in current directory
    cwd_data = Path.cwd() / "data"
    if cwd_data.exists() and cwd_data.is_dir():
        return str(cwd_data)
    
    # Check parent directory
    parent_data = Path.cwd().parent / "data"
    if parent_data.exists() and parent_data.is_dir():
        return str(parent_data)
    
    # Fallback to user home
    home_data = Path.home() / ".rebrain" / "data"
    home_data.mkdir(parents=True, exist_ok=True)
    return str(home_data)


def setup_database_from_jsons(data_path: str, force_reload: bool = False) -> str:
    """
    Setup memg-core database, loading from JSONs if needed.
    
    Args:
        data_path: Path to data directory containing JSONs
        force_reload: Force reload even if database exists
        
    Returns:
        Path to database directory
    """
    from pathlib import Path
    import json
    import shutil
    
    data_path_obj = Path(data_path)
    db_path = data_path_obj / "memory_db"
    
    # Check if database exists and has data
    qdrant_path = db_path / "qdrant"
    kuzu_path = db_path / "kuzu"
    
    has_db = (
        qdrant_path.exists() 
        and kuzu_path.exists()
        and any(qdrant_path.iterdir())  # Not empty
    )
    
    if has_db and not force_reload:
        logger.info("✅ Using existing database")
        return str(db_path)
    
    # Need to load from JSONs
    logger.info("🔄 Loading JSONs into memg-core database (~6 sec)...")
    
    cognitions_path = data_path_obj / "cognitions" / "cognitions.json"
    learnings_path = data_path_obj / "learnings" / "learnings.json"
    
    if not cognitions_path.exists():
        logger.error(f"❌ Cognitions file not found: {cognitions_path}")
        logger.error("💡 Run 'rebrain pipeline run' first to generate data")
        raise FileNotFoundError(f"Missing {cognitions_path}")
    
    if not learnings_path.exists():
        logger.error(f"❌ Learnings file not found: {learnings_path}")
        logger.error("💡 Run 'rebrain pipeline run' first to generate data")
        raise FileNotFoundError(f"Missing {learnings_path}")
    
    # Clear existing database if force reload
    if force_reload and db_path.exists():
        logger.info("🗑️  Removing existing database...")
        shutil.rmtree(db_path)
    
    # Load using the existing load_memg.py logic
    # Import here to avoid circular dependencies
    from pathlib import Path as P
    import sys
    
    # Add scripts to path
    scripts_path = P(__file__).parent.parent.parent / "scripts"
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))
    
    # Import load functions
    from load_memg import (
        load_json_data,
        validate_learnings,
        initialize_database,
        import_cognitions,
        import_learnings,
        create_relationships,
    )
    
    # Get YAML schema path
    yaml_path = data_path_obj.parent / "integrations" / "mcp" / "rebrain" / "rebrain.yaml"
    if not yaml_path.exists():
        # Try alternative location
        yaml_path = P(__file__).parent / "rebrain" / "rebrain.yaml"
    
    if not yaml_path.exists():
        logger.error(f"❌ YAML schema not found")
        raise FileNotFoundError("rebrain.yaml schema file not found")
    
    # Load data
    cognitions, learnings = load_json_data(cognitions_path, learnings_path)
    valid_learnings = validate_learnings(learnings, cognitions)
    
    # Initialize database
    client = initialize_database(yaml_path, db_path)
    
    try:
        # Import data
        cognition_map = import_cognitions(client, cognitions, "rebrain")
        learning_map = import_learnings(client, valid_learnings, "rebrain")
        relationship_count = create_relationships(client, cognition_map, learning_map, "rebrain")
        
        logger.info(f"✅ Loaded {len(cognition_map)} cognitions, {len([l for ls in learning_map.values() for l in ls])} learnings")
        logger.info(f"✅ Created {relationship_count} relationships")
    finally:
        client.close()
    
    return str(db_path)


# ========================= CLI ENTRY POINT =========================

def main_cli():
    """
    Main entry point for rebrain-mcp command with CLI argument parsing.
    
    Supports both stdio (default) and HTTP modes.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="rebrain-mcp",
        description="ReBrain MCP Server - Serve your memory to AI",
    )
    parser.add_argument(
        "--data-path",
        help="Path to data directory (default: auto-detect)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Run as HTTP server on port (default: stdio mode)",
    )
    parser.add_argument(
        "--force-reload",
        action="store_true",
        help="Force reload database from JSONs",
    )
    
    args = parser.parse_args()
    
    # Get data path
    if args.data_path:
        data_path = args.data_path
    else:
        data_path = get_data_path_from_args()
    
    logger.info(f"📁 Data directory: {data_path}")
    
    # Setup database
    try:
        db_path = setup_database_from_jsons(data_path, args.force_reload)
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return 1
    
    # Set environment variables for the existing server code
    from pathlib import Path
    yaml_path = Path(__file__).parent / "rebrain" / "rebrain.yaml"
    os.environ["MEMG_YAML_SCHEMA"] = str(yaml_path)
    os.environ["MEMG_DB_PATH"] = db_path
    
    # Create the app
    app = create_app()
    
    # Run in appropriate mode
    if args.port:
        logger.info(f"🚀 Starting HTTP server on port {args.port}")
        logger.info(f"🔗 SSE endpoint: http://localhost:{args.port}/sse")
        logger.info(f"🔗 Messages endpoint: http://localhost:{args.port}/messages/")
        app.run(transport="sse", port=args.port, host="0.0.0.0", path="/mcp")
    else:
        logger.info("🚀 Starting stdio server (for uvx/Claude Desktop)")
        app.run(transport="stdio")
    
    return 0


# ========================= FASTMCP EXPORT =========================

# Entry point for CLI
def main():
    """Entry point wrapper for rebrain-mcp command."""
    import sys
    sys.exit(main_cli())


# Create the app instance for FastMCP to run (Docker mode)
# This will only run if env vars are set (Docker deployment)
if __name__ != "__main__":
    try:
        mcp_app = create_app()
    except RuntimeError:
        # Environment not configured, skip app creation
        # Will be created by main() when called via CLI
        mcp_app = None
