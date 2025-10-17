"""
Filtering operations for pipeline data.

Date filtering, privacy filtering, and other data filters.
"""

from datetime import datetime, timedelta
from typing import List, Any, Dict, Set
from rebrain.schemas.observation import PrivacyLevel


class DateFilter:
    """Filter conversations or items by date."""
    
    @staticmethod
    def filter_by_cutoff(
        items: List[Dict[str, Any]],
        cutoff_days: int,
        date_field: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """
        Filter items to only include those within cutoff days.
        
        Args:
            items: List of items with date field
            cutoff_days: Number of days to keep (e.g., 180 = 6 months)
            date_field: Name of date field in items
        
        Returns:
            Filtered list of items
        """
        cutoff_date = datetime.now() - timedelta(days=cutoff_days)
        
        filtered = []
        for item in items:
            item_date = item.get(date_field)
            
            # Handle different date formats
            if isinstance(item_date, str):
                item_date = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
            elif isinstance(item_date, (int, float)):
                item_date = datetime.fromtimestamp(item_date)
            
            if item_date and item_date >= cutoff_date:
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def filter_by_date_range(
        items: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        date_field: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """
        Filter items to date range.
        
        Args:
            items: List of items
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)
            date_field: Name of date field
        
        Returns:
            Filtered list
        """
        filtered = []
        for item in items:
            item_date = item.get(date_field)
            
            # Handle different date formats
            if isinstance(item_date, str):
                item_date = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
            elif isinstance(item_date, (int, float)):
                item_date = datetime.fromtimestamp(item_date)
            
            if item_date and start_date <= item_date <= end_date:
                filtered.append(item)
        
        return filtered


class PrivacyFilter:
    """Filter items by privacy level (observations, learnings, etc.)."""
    
    @staticmethod
    def filter_by_privacy(
        items: List[Dict[str, Any]],
        exclude_levels: List[str],
        privacy_field: str = "privacy"
    ) -> List[Dict[str, Any]]:
        """
        Filter out items with specified privacy levels.
        
        Args:
            items: List of items (observations, learnings, etc.)
            exclude_levels: Privacy levels to exclude (e.g., ["high"])
            privacy_field: Name of privacy field
        
        Returns:
            Filtered list without excluded privacy levels
        """
        exclude_set = set(exclude_levels)
        
        filtered = []
        for item in items:
            privacy = item.get(privacy_field, "low")
            if privacy not in exclude_set:
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def filter_by_category_and_privacy(
        items: List[Dict[str, Any]],
        exclusion_rules: Dict[str, List[str]],
        category_field: str = "category",
        privacy_field: str = "privacy"
    ) -> List[Dict[str, Any]]:
        """
        Filter items by category-specific privacy exclusion rules.
        
        Args:
            items: List of items (observations)
            exclusion_rules: Dict mapping category to list of privacy levels to exclude
                            e.g., {"technical": ["high"], "personal": ["medium", "high"]}
            category_field: Name of category field
            privacy_field: Name of privacy field
        
        Returns:
            Filtered list excluding items matching category+privacy rules
        """
        filtered = []
        for item in items:
            category = item.get(category_field, "").lower()
            privacy = item.get(privacy_field, "low")
            
            # Get exclusion rules for this category
            exclude_levels = exclusion_rules.get(category, [])
            
            # Keep item if privacy level NOT in exclusion list
            if privacy not in exclude_levels:
                filtered.append(item)
        
        return filtered


class ContentFilter:
    """Filter by content characteristics."""
    
    @staticmethod
    def filter_by_keywords(
        items: List[Dict[str, Any]],
        keywords: List[str],
        content_field: str = "content",
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter items containing any of the keywords.
        
        Args:
            items: List of items
            keywords: Keywords to search for
            content_field: Field to search in
            case_sensitive: Whether search is case-sensitive
        
        Returns:
            Filtered list containing keywords
        """
        if not case_sensitive:
            keywords = [k.lower() for k in keywords]
        
        filtered = []
        for item in items:
            content = str(item.get(content_field, ""))
            if not case_sensitive:
                content = content.lower()
            
            if any(keyword in content for keyword in keywords):
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def filter_by_category(
        items: List[Dict[str, Any]],
        categories: List[str],
        category_field: str = "category"
    ) -> List[Dict[str, Any]]:
        """
        Filter items by category.
        
        Args:
            items: List of items
            categories: Categories to include
            category_field: Name of category field
        
        Returns:
            Filtered list
        """
        category_set = set(categories)
        
        filtered = []
        for item in items:
            if item.get(category_field) in category_set:
                filtered.append(item)
        
        return filtered

