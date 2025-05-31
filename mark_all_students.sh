#!/bin/bash

# Batch processing script for marking multiple student assignments
# 
# Usage: ./mark_all_students.sh [OPTIONS]
# 
# This script processes all notebook files in a directory and generates
# individual marking sheets for each student.

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Default configuration
NOTEBOOKS_DIR=""
RUBRIC_FILE=""
OUTPUT_DIR="batch_marking_output"
MODEL="gpt-4o-mini"
VERBOSE=""
DEBUG=""
DRY_RUN=""
CONTINUE_FROM=""
MAX_PARALLEL=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_error() { echo -e "${RED}✗ $1${NC}" >&2; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Print usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Batch process multiple student notebooks for marking.

OPTIONS:
    -n, --notebooks-dir DIR     Directory containing student notebooks (required)
    -r, --rubric FILE          Path to rubric CSV file (required)  
    -o, --output-dir DIR       Output directory (default: batch_marking_output)
    -m, --model MODEL          OpenAI model to use (default: gpt-4o-mini)
    -v, --verbose              Enable verbose output
    -d, --debug                Enable debug output
    --dry-run                  Preview operations without marking
    --continue-from STUDENT    Resume from specific student ID
    --max-parallel N           Max parallel processes (default: 1)
    -h, --help                 Show this help message

EXAMPLES:
    # Basic batch processing
    $0 -n ./student_notebooks -r ./rubric.csv
    
    # With custom output directory and verbose mode
    $0 -n ./notebooks -r ./rubric.csv -o ./results -v
    
    # Dry run to check setup
    $0 -n ./notebooks -r ./rubric.csv --dry-run
    
    # Resume from specific student
    $0 -n ./notebooks -r ./rubric.csv --continue-from student_042

REQUIREMENTS:
    - Python 3.8+ with required packages installed
    - OPENAI_API_KEY environment variable set
    - Student notebooks in .ipynb format
    - Rubric file in CSV format

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--notebooks-dir)
                NOTEBOOKS_DIR="$2"
                shift 2
                ;;
            -r|--rubric)
                RUBRIC_FILE="$2"
                shift 2
                ;;
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -m|--model)
                MODEL="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE="--verbose"
                shift
                ;;
            -d|--debug)
                DEBUG="--debug"
                shift
                ;;
            --dry-run)
                DRY_RUN="--dry-run"
                shift
                ;;
            --continue-from)
                CONTINUE_FROM="$2"
                shift 2
                ;;
            --max-parallel)
                MAX_PARALLEL="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate required arguments and environment
validate_setup() {
    local errors=0
    
    if [[ -z "$NOTEBOOKS_DIR" ]]; then
        print_error "Notebooks directory is required (-n/--notebooks-dir)"
        errors=1
    elif [[ ! -d "$NOTEBOOKS_DIR" ]]; then
        print_error "Notebooks directory does not exist: $NOTEBOOKS_DIR"
        errors=1
    fi
    
    if [[ -z "$RUBRIC_FILE" ]]; then
        print_error "Rubric file is required (-r/--rubric)"
        errors=1
    elif [[ ! -f "$RUBRIC_FILE" ]]; then
        print_error "Rubric file does not exist: $RUBRIC_FILE"
        errors=1
    fi
    
    if [[ -z "$DRY_RUN" ]] && [[ -z "$OPENAI_API_KEY" ]]; then
        print_error "OPENAI_API_KEY environment variable is not set"
        errors=1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "python3 command not found"
        errors=1
    fi
    
    if [[ ! -f "./mark_student.py" ]]; then
        print_error "mark_student.py not found in current directory"
        errors=1
    fi
    
    if [[ $errors -gt 0 ]]; then
        print_error "Setup validation failed"
        exit 1
    fi
}

# Find all notebook files
find_notebooks() {
    local notebooks=()
    while IFS= read -r -d '' file; do
        notebooks+=("$file")
    done < <(find "$NOTEBOOKS_DIR" -name "*.ipynb" -type f -print0 | sort -z)
    
    printf '%s\n' "${notebooks[@]}"
}

# Extract student ID from notebook filename
get_student_id() {
    local notebook_path="$1"
    basename "$notebook_path" .ipynb
}

# Process a single student notebook
process_student() {
    local notebook_path="$1"
    local student_id
    student_id=$(get_student_id "$notebook_path")
    
    local cmd_args=()
    cmd_args+=("--notebook" "$notebook_path")
    cmd_args+=("--rubric" "$RUBRIC_FILE")
    cmd_args+=("--output-dir" "$OUTPUT_DIR")
    cmd_args+=("--model" "$MODEL")
    cmd_args+=("--student-id" "$student_id")
    
    [[ -n "$VERBOSE" ]] && cmd_args+=("$VERBOSE")
    [[ -n "$DEBUG" ]] && cmd_args+=("$DEBUG")
    [[ -n "$DRY_RUN" ]] && cmd_args+=("$DRY_RUN")
    
    print_info "Processing: $student_id"
    
    if python3 mark_student.py "${cmd_args[@]}"; then
        print_success "Completed: $student_id"
        return 0
    else
        print_error "Failed: $student_id"
        return 1
    fi
}

# Process all students
process_all_students() {
    local notebooks=()
    local notebook
    local student_id
    local continue_processing=true
    local processed_count=0
    local success_count=0
    local error_count=0
    local start_time
    local end_time
    
    # Find all notebooks
    readarray -t notebooks < <(find_notebooks)
    
    if [[ ${#notebooks[@]} -eq 0 ]]; then
        print_warning "No notebook files found in $NOTEBOOKS_DIR"
        return 0
    fi
    
    print_info "Found ${#notebooks[@]} notebook files"
    
    # Handle --continue-from option
    if [[ -n "$CONTINUE_FROM" ]]; then
        continue_processing=false
        print_info "Looking for resume point: $CONTINUE_FROM"
    fi
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Process each notebook
    start_time=$(date +%s)
    
    for notebook in "${notebooks[@]}"; do
        student_id=$(get_student_id "$notebook")
        
        # Handle continue-from logic
        if [[ "$continue_processing" == false ]]; then
            if [[ "$student_id" == "$CONTINUE_FROM" ]]; then
                continue_processing=true
                print_info "Resuming from: $student_id"
            else
                print_info "Skipping: $student_id (before resume point)"
                continue
            fi
        fi
        
        # Check if already processed (skip if output exists)
        local output_file="$OUTPUT_DIR/${student_id}_marks.xlsx"
        if [[ -f "$output_file" ]] && [[ -z "$DRY_RUN" ]]; then
            print_warning "Skipping: $student_id (output already exists)"
            ((processed_count++))
            continue
        fi
        
        # Process the student
        if process_student "$notebook"; then
            ((success_count++))
        else
            ((error_count++))
        fi
        
        ((processed_count++))
        
        # Progress update
        local remaining=$((${#notebooks[@]} - processed_count))
        print_info "Progress: $processed_count/${#notebooks[@]} processed, $remaining remaining"
        
        # Add small delay to avoid overwhelming the API
        if [[ -z "$DRY_RUN" ]] && [[ $processed_count -lt ${#notebooks[@]} ]]; then
            sleep 1
        fi
    done
    
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Print summary
    echo
    echo "======================================"
    echo "BATCH PROCESSING SUMMARY"
    echo "======================================"
    echo "Total notebooks: ${#notebooks[@]}"
    echo "Processed: $processed_count"
    echo "Successful: $success_count"
    echo "Errors: $error_count"
    echo "Duration: ${duration}s"
    echo "Output directory: $OUTPUT_DIR"
    
    if [[ $error_count -gt 0 ]]; then
        print_warning "$error_count assignments had errors"
        echo "Check the logs above for details"
    else
        print_success "All assignments processed successfully!"
    fi
    
    return $error_count
}

# Generate batch summary report
generate_summary() {
    local summary_file="$OUTPUT_DIR/batch_summary.txt"
    local csv_file="$OUTPUT_DIR/batch_results.csv"
    
    print_info "Generating batch summary..."
    
    # Create summary report
    {
        echo "BATCH MARKING SUMMARY"
        echo "Generated: $(date)"
        echo "Notebooks directory: $NOTEBOOKS_DIR"
        echo "Rubric file: $RUBRIC_FILE"
        echo "Model: $MODEL"
        echo "Output directory: $OUTPUT_DIR"
        echo ""
        echo "FILES PROCESSED:"
        
        # List all Excel files created
        if ls "$OUTPUT_DIR"/*.xlsx &>/dev/null; then
            for excel_file in "$OUTPUT_DIR"/*.xlsx; do
                local basename_file
                basename_file=$(basename "$excel_file")
                echo "  - $basename_file"
            done
        else
            echo "  (No Excel files generated)"
        fi
        
        echo ""
        echo "NEXT STEPS:"
        echo "1. Review individual Excel files for detailed marking"
        echo "2. Check any error logs for failed assignments"
        echo "3. Consider manual review for flagged issues"
        
    } > "$summary_file"
    
    # Create CSV summary if Excel files exist
    if ls "$OUTPUT_DIR"/*.xlsx &>/dev/null; then
        {
            echo "student_id,excel_file,status"
            for excel_file in "$OUTPUT_DIR"/*.xlsx; do
                local basename_file student_id
                basename_file=$(basename "$excel_file")
                student_id=$(basename "$excel_file" _marks.xlsx)
                echo "$student_id,$basename_file,completed"
            done
        } > "$csv_file"
        
        print_success "Summary report: $summary_file"
        print_success "CSV results: $csv_file"
    else
        print_success "Summary report: $summary_file"
    fi
}

# Main execution
main() {
    local script_dir
    script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    cd "$script_dir"
    
    # Parse arguments
    parse_args "$@"
    
    # Validate setup
    validate_setup
    
    # Print configuration
    echo "======================================"
    echo "BATCH MARKING CONFIGURATION"
    echo "======================================"
    echo "Notebooks directory: $NOTEBOOKS_DIR"
    echo "Rubric file: $RUBRIC_FILE"
    echo "Output directory: $OUTPUT_DIR"
    echo "Model: $MODEL"
    echo "Max parallel: $MAX_PARALLEL"
    [[ -n "$VERBOSE" ]] && echo "Verbose mode: enabled"
    [[ -n "$DEBUG" ]] && echo "Debug mode: enabled"
    [[ -n "$DRY_RUN" ]] && echo "Dry run: enabled"
    [[ -n "$CONTINUE_FROM" ]] && echo "Continue from: $CONTINUE_FROM"
    echo "======================================"
    echo
    
    # Process all students
    if process_all_students; then
        # Generate summary report
        if [[ -z "$DRY_RUN" ]]; then
            generate_summary
        fi
        
        print_success "Batch processing completed successfully!"
        exit 0
    else
        print_error "Batch processing completed with errors"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
