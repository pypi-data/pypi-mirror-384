#!/bin/bash
################################################################################
# Rebrain Pipeline CLI
# Flexible command-line interface for running pipeline steps
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

################################################################################
# Helper functions
################################################################################

print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

usage() {
    cat << EOF
${GREEN}Rebrain Pipeline CLI${NC}

Usage: ./cli.sh <command> [options]

${YELLOW}Commands:${NC}

  ${GREEN}step1${NC}  - Transform & Filter Conversations
    Transform raw ChatGPT JSON to clean, AI-ready format
    
    Options:
      -i, --input   <path>   Input file (default: data/raw/conversations.json)
      -o, --output  <path>   Output file (default: data/preprocessed/conversations_clean.json)
    
    Example:
      ./cli.sh step1
      ./cli.sh step1 -i data/raw/my_convos.json -o data/test/clean.json

  ${GREEN}step2${NC}  - Extract & Cluster Observations
    Extract observations → filter privacy → embed → cluster
    
    Options:
      -i, --input      <path>   Input file (default: data/preprocessed/conversations_clean.json)
      -o, --output     <path>   Output file (default: data/observations/observations.json)
      --cluster-only            Only run clustering on existing observations (skip AI extraction)
      --skip-cluster            Run extraction only, skip clustering (for testing)
    
    Example:
      ./cli.sh step2                    # Full: extract + cluster
      ./cli.sh step2 --cluster-only     # Only cluster existing observations
      ./cli.sh step2 --skip-cluster     # Only extract, review before clustering

  ${GREEN}step3${NC}  - Synthesize & Cluster Learnings
    Synthesize observation clusters → learnings → embed → cluster
    
    Options:
      -i, --input      <path>   Input file (default: data/observations/observations.json)
      -o, --output     <path>   Output file (default: data/learnings/learnings.json)
      --cluster-only            Only run clustering on existing learnings
      --skip-cluster            Run synthesis only, skip clustering
    
    Example:
      ./cli.sh step3
      ./cli.sh step3 --cluster-only

  ${GREEN}step4${NC}  - Synthesize Cognitions
    Synthesize learning clusters → final cognitions
    
    Options:
      -i, --input   <path>   Input file (default: data/learnings/learnings.json)
      -o, --output  <path>   Output file (default: data/cognitions/cognitions.json)
    
    Example:
      ./cli.sh step4

  ${GREEN}step5${NC}  - Build Persona
    Synthesize cognitions → persona (3 plain text sections)
    
    Options:
      -i, --input   <path>   Input file (default: data/cognitions/cognitions.json)
      -o, --output  <path>   Output file (default: data/persona/persona.json)
    
    Example:
      ./cli.sh step5

  ${GREEN}all${NC}    - Run entire pipeline (steps 1-5)
    
    Example:
      ./cli.sh all

  ${GREEN}clean${NC}  - Clean intermediate outputs
    
    Options:
      --all           Remove all generated data (including final output)
      --observations  Remove observations only
      --learnings     Remove learnings only
    
    Example:
      ./cli.sh clean --observations
      ./cli.sh clean --all

  ${GREEN}status${NC} - Show pipeline status (what files exist)

  ${GREEN}help${NC}   - Show this help message

EOF
}

check_file_exists() {
    if [[ ! -f "$1" ]]; then
        print_error "Input file not found: $1"
        exit 1
    fi
}

################################################################################
# Step 1: Transform & Filter
################################################################################

step1() {
    local data_path="${1:-}"
    
    print_header "STEP 1: Transform & Filter Conversations"
    [[ -n "$data_path" ]] && print_info "Data path: $data_path"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$data_path" ]]; then
        check_file_exists "$PROJECT_ROOT/$data_path/raw/conversations.json"
        python scripts/pipeline/01_transform_filter.py --data-path "$data_path"
    else
        check_file_exists "$PROJECT_ROOT/data/raw/conversations.json"
        python scripts/pipeline/01_transform_filter.py
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Step 1 complete"
    else
        print_error "Step 1 failed"
        exit 1
    fi
}

################################################################################
# Step 2: Extract & Cluster Observations
################################################################################

step2() {
    local data_path="${1:-}"
    local mode="${2:-full}"  # full, cluster-only, skip-cluster
    
    print_header "STEP 2: Extract & Cluster Observations"
    [[ -n "$data_path" ]] && print_info "Data path: $data_path"
    print_info "Mode:   $mode"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$data_path" ]]; then
        check_file_exists "$PROJECT_ROOT/$data_path/preprocessed/conversations_clean.json"
    else
        check_file_exists "$PROJECT_ROOT/data/preprocessed/conversations_clean.json"
    fi
    
    local cmd="python scripts/pipeline/02_extract_cluster_observations.py"
    [[ -n "$data_path" ]] && cmd="$cmd --data-path $data_path"
    
    case "$mode" in
        cluster-only)
            $cmd --cluster-only
            ;;
        skip-cluster)
            $cmd --skip-cluster
            ;;
        *)
            $cmd
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        print_success "Step 2 complete"
    else
        print_error "Step 2 failed"
        exit 1
    fi
}

################################################################################
# Step 3: Synthesize & Cluster Learnings
################################################################################

step3() {
    local data_path="${1:-}"
    
    print_header "STEP 3: Synthesize & Cluster Learnings"
    [[ -n "$data_path" ]] && print_info "Data path: $data_path"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$data_path" ]]; then
        check_file_exists "$PROJECT_ROOT/$data_path/observations/observations.json"
        python scripts/pipeline/03_synthesize_cluster_learnings.py --data-path "$data_path"
    else
        check_file_exists "$PROJECT_ROOT/data/observations/observations.json"
        python scripts/pipeline/03_synthesize_cluster_learnings.py
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Step 3 complete"
    else
        print_error "Step 3 failed"
        exit 1
    fi
}

################################################################################
# Step 4: Synthesize Cognitions
################################################################################

step4() {
    local data_path="${1:-}"
    
    print_header "STEP 4: Synthesize Cognitions"
    [[ -n "$data_path" ]] && print_info "Data path: $data_path"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$data_path" ]]; then
        check_file_exists "$PROJECT_ROOT/$data_path/learnings/learnings.json"
        python scripts/pipeline/04_synthesize_cognitions.py --data-path "$data_path"
    else
        check_file_exists "$PROJECT_ROOT/data/learnings/learnings.json"
        python scripts/pipeline/04_synthesize_cognitions.py
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Step 4 complete"
    else
        print_error "Step 4 failed"
        exit 1
    fi
}

################################################################################
# Step 5: Build Persona
################################################################################

step5() {
    local data_path="${1:-}"
    
    print_header "STEP 5: Build Persona"
    [[ -n "$data_path" ]] && print_info "Data path: $data_path"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$data_path" ]]; then
        check_file_exists "$PROJECT_ROOT/$data_path/cognitions/cognitions.json"
        python scripts/pipeline/05_build_persona.py --data-path "$data_path"
    else
        check_file_exists "$PROJECT_ROOT/data/cognitions/cognitions.json"
        python scripts/pipeline/05_build_persona.py
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Step 5 complete"
        print_success "Pipeline finished!"
    else
        print_error "Step 5 failed"
        exit 1
    fi
}

################################################################################
# Run all steps
################################################################################

run_all() {
    print_header "Running Full Pipeline (Steps 1-5)"
    
    step1
    step2
    step3
    step4
    step5
    
    print_header "Pipeline Complete!"
    print_success "All steps completed successfully"
}

################################################################################
# Status check
################################################################################

status() {
    print_header "Pipeline Status"
    
    cd "$PROJECT_ROOT"
    
    echo ""
    echo -e "${YELLOW}Input Data:${NC}"
    [[ -f "data/raw/conversations.json" ]] && print_success "data/raw/conversations.json" || print_error "data/raw/conversations.json (missing)"
    
    echo ""
    echo -e "${YELLOW}Step 1 Output:${NC}"
    [[ -f "data/preprocessed/conversations_clean.json" ]] && print_success "data/preprocessed/conversations_clean.json" || print_error "data/preprocessed/conversations_clean.json (not run)"
    
    echo ""
    echo -e "${YELLOW}Step 2 Output:${NC}"
    [[ -f "data/observations/observations.json" ]] && print_success "data/observations/observations.json" || print_error "data/observations/observations.json (not run)"
    
    echo ""
    echo -e "${YELLOW}Step 3 Output:${NC}"
    [[ -f "data/learnings/learnings.json" ]] && print_success "data/learnings/learnings.json" || print_error "data/learnings/learnings.json (not run)"
    
    echo ""
    echo -e "${YELLOW}Step 4 Output:${NC}"
    [[ -f "data/cognitions/cognitions.json" ]] && print_success "data/cognitions/cognitions.json" || print_error "data/cognitions/cognitions.json (not run)"
    
    echo ""
    echo -e "${YELLOW}Step 5 Output:${NC}"
    [[ -f "data/persona/persona.json" ]] && print_success "data/persona/persona.json" || print_error "data/persona/persona.json (not run)"
    [[ -f "data/persona/persona.md" ]] && print_success "data/persona/persona.md" || print_error "data/persona/persona.md (not run)"
    
    echo ""
}

################################################################################
# Clean outputs
################################################################################

clean() {
    local target="${1:-}"
    
    print_header "Clean Pipeline Outputs"
    
    cd "$PROJECT_ROOT"
    
    case "$target" in
        --all)
            print_info "Removing all generated data..."
            rm -rf data/preprocessed/conversations_clean.json
            rm -rf data/observations/
            rm -rf data/learnings/
            rm -rf data/cognitions/
            rm -rf data/persona/
            print_success "All outputs removed"
            ;;
        --observations)
            print_info "Removing observations..."
            rm -rf data/observations/
            print_success "Observations removed"
            ;;
        --learnings)
            print_info "Removing learnings..."
            rm -rf data/learnings/
            print_success "Learnings removed"
            ;;
        *)
            print_error "Specify what to clean: --all, --observations, --learnings"
            exit 1
            ;;
    esac
}

################################################################################
# Main entry point
################################################################################

main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 0
    fi
    
    local command="$1"
    shift
    
    # Parse arguments for each command
    case "$command" in
        step1)
            local data_path=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --data-path)
                        data_path="$2"
                        shift 2
                        ;;
                    *)
                        print_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            step1 "$data_path"
            ;;
        
        step2)
            local data_path=""
            local mode="full"
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --data-path)
                        data_path="$2"
                        shift 2
                        ;;
                    --cluster-only)
                        mode="cluster-only"
                        shift
                        ;;
                    --skip-cluster)
                        mode="skip-cluster"
                        shift
                        ;;
                    *)
                        print_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            step2 "$data_path" "$mode"
            ;;
        
        step3)
            local data_path=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --data-path)
                        data_path="$2"
                        shift 2
                        ;;
                    *)
                        print_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            step3 "$data_path"
            ;;
        
        step4)
            local data_path=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --data-path)
                        data_path="$2"
                        shift 2
                        ;;
                    *)
                        print_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            step4 "$data_path"
            ;;
        
        step5)
            local data_path=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --data-path)
                        data_path="$2"
                        shift 2
                        ;;
                    *)
                        print_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            step5 "$data_path"
            ;;
        
        all)
            run_all
            ;;
        
        status)
            status
            ;;
        
        clean)
            clean "$@"
            ;;
        
        help|--help|-h)
            usage
            ;;
        
        *)
            print_error "Unknown command: $command"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"

