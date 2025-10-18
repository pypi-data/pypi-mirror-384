#!/bin/bash
# Script to run compatibility tests in isolated environments

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Polyspark Compatibility Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to create and run tests in a venv
run_compatibility_test() {
    local test_name=$1
    local venv_name=$2
    local test_file=$3
    local extra_package=$4
    
    echo -e "${YELLOW}Testing: ${test_name}${NC}"
    echo "----------------------------------------"
    
    # Create venv if it doesn't exist
    if [ ! -d "$venv_name" ]; then
        echo "Creating virtual environment: $venv_name"
        python3.8 -m venv "$venv_name"
    fi
    
    # Activate venv
    source "$venv_name/bin/activate"
    
    # Install polyspark and dependencies
    echo "Installing polyspark and dependencies..."
    pip install -q -e . > /dev/null 2>&1
    pip install -q pytest pytest-cov > /dev/null 2>&1
    
    # Install the extra package
    if [ -n "$extra_package" ]; then
        echo "Installing $extra_package..."
        pip install -q "$extra_package" > /dev/null 2>&1
    fi
    
    # Run the specific test
    echo "Running tests..."
    if python -m pytest "$test_file" -v --tb=short 2>&1 | tee /tmp/polyspark_test_output.txt; then
        echo -e "${GREEN}✓ $test_name tests PASSED${NC}"
    else
        echo -e "${RED}✗ $test_name tests FAILED${NC}"
        cat /tmp/polyspark_test_output.txt
        deactivate
        return 1
    fi
    
    echo ""
    deactivate
}

# Track if any tests failed
FAILED=0

# Test 1: Mock-Spark compatibility (NO PySpark)
echo -e "${BLUE}Test 1: Mock-Spark Compatibility (No PySpark)${NC}"
echo "Environment: Python 3.8 + mock-spark>=2.2.0 (NO PySpark)"
if ! run_compatibility_test \
    "Mock-Spark Compatibility" \
    ".venv38-mockspark" \
    "tests/compatibility/test_mockspark_compat.py" \
    "mock-spark>=2.2.0"; then
    FAILED=1
fi

# Test 2: PySpark compatibility
echo -e "${BLUE}Test 2: PySpark Compatibility${NC}"
echo "Environment: Python 3.11 + pyspark"
if ! run_compatibility_test \
    "PySpark Compatibility" \
    ".venv311-pyspark" \
    "tests/compatibility/test_pyspark_compat.py" \
    "pyspark>=3.0.0"; then
    FAILED=1
fi

# Test 3: Pydantic compatibility
echo -e "${BLUE}Test 3: Pydantic Compatibility${NC}"
echo "Environment: Python 3.11 + pydantic"
if ! run_compatibility_test \
    "Pydantic Compatibility" \
    ".venv311-pydantic" \
    "tests/compatibility/test_pydantic_compat.py" \
    "pydantic>=2.0.0"; then
    FAILED=1
fi

echo ""
echo -e "${BLUE}================================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All compatibility tests PASSED${NC}"
    echo -e "${GREEN}Polyspark is compatible with all tested packages!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some compatibility tests FAILED${NC}"
    echo -e "${RED}Please check the output above for details${NC}"
    exit 1
fi

