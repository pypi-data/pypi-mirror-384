#!/bin/bash
# Test script for Nexus CLI commands
# This script tests all CLI functionality end-to-end

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test workspace
TEST_WORKSPACE="/tmp/nexus-cli-test-$$"
DATA_DIR="$TEST_WORKSPACE/nexus-data"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Nexus CLI Test Suite${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up test workspace...${NC}"
    rm -rf "$TEST_WORKSPACE"
}

# Register cleanup
trap cleanup EXIT

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper function
test_command() {
    local description="$1"
    shift
    TESTS_RUN=$((TESTS_RUN + 1))

    echo -e "${BLUE}Test $TESTS_RUN:${NC} $description"

    if "$@"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo ""
        return 1
    fi
}

# Install nexus if not already installed
if ! command -v nexus &> /dev/null; then
    echo -e "${YELLOW}Installing Nexus CLI...${NC}"
    pip install -e . > /dev/null 2>&1
fi

echo -e "${GREEN}Starting CLI tests...${NC}\n"

# Test 1: Initialize workspace
test_command "Initialize workspace" \
    nexus init "$TEST_WORKSPACE"

# Test 2: List empty workspace
test_command "List empty workspace" \
    nexus ls /workspace --data-dir "$DATA_DIR"

# Test 3: Create directory
test_command "Create directory" \
    nexus mkdir /workspace/data --data-dir "$DATA_DIR"

# Test 4: Create nested directory with --parents
test_command "Create nested directory" \
    nexus mkdir /workspace/deep/nested/dir --parents --data-dir "$DATA_DIR"

# Test 5: Write file with string content
test_command "Write file with string content" \
    nexus write /workspace/hello.txt "Hello, Nexus!" --data-dir "$DATA_DIR"

# Test 6: Write Python file
test_command "Write Python file" \
    bash -c "echo 'def hello():\n    print(\"Hello World\")' | nexus write /workspace/code.py --input - --data-dir $DATA_DIR"

# Test 7: Write JSON file
test_command "Write JSON file" \
    bash -c "echo '{\"name\": \"test\", \"value\": 42}' | nexus write /workspace/data.json --input - --data-dir $DATA_DIR"

# Test 8: Write Markdown file
test_command "Write Markdown file" \
    bash -c "echo '# Test Document\n\n## Section 1\n\nSome content here.' | nexus write /workspace/README.md --input - --data-dir $DATA_DIR"

# Test 9: List files
test_command "List files in /workspace" \
    nexus ls /workspace --data-dir "$DATA_DIR"

# Test 10: List files recursively
test_command "List files recursively" \
    nexus ls /workspace --recursive --data-dir "$DATA_DIR"

# Test 11: List files with details
test_command "List files with details" \
    nexus ls /workspace --long --data-dir "$DATA_DIR"

# Test 12: Cat text file
test_command "Display text file" \
    nexus cat /workspace/hello.txt --data-dir "$DATA_DIR"

# Test 13: Cat Python file (with syntax highlighting)
test_command "Display Python file with syntax highlighting" \
    nexus cat /workspace/code.py --data-dir "$DATA_DIR"

# Test 14: Copy file
test_command "Copy file" \
    nexus cp /workspace/hello.txt /workspace/hello_copy.txt --data-dir "$DATA_DIR"

# Test 15: Glob - find all .txt files
test_command "Find all .txt files" \
    nexus glob "*.txt" --path /workspace --data-dir "$DATA_DIR"

# Test 16: Glob - find all files recursively
test_command "Find all files with ** pattern" \
    nexus glob "**/*" --data-dir "$DATA_DIR"

# Test 17: Glob - find Python files
test_command "Find Python files" \
    nexus glob "**/*.py" --data-dir "$DATA_DIR"

# Test 18: Grep - search for "Hello"
test_command "Grep search for 'Hello'" \
    nexus grep "Hello" --data-dir "$DATA_DIR"

# Test 19: Grep - search in Python files only
test_command "Grep in Python files only" \
    nexus grep "def" --file-pattern "**/*.py" --data-dir "$DATA_DIR"

# Test 20: Grep - case-insensitive search
test_command "Grep case-insensitive search" \
    nexus grep "HELLO" --ignore-case --data-dir "$DATA_DIR"

# Test 21: Info - show file details
test_command "Show file information" \
    nexus info /workspace/hello.txt --data-dir "$DATA_DIR"

# Test 22: Delete file
test_command "Delete file" \
    nexus rm /workspace/hello_copy.txt --force --data-dir "$DATA_DIR"

# Test 23: Verify deletion
test_command "Verify file was deleted" \
    bash -c "! nexus cat /workspace/hello_copy.txt --data-dir $DATA_DIR 2>/dev/null"

# Populate /workspace/data for rmdir test
echo -e "${BLUE}Populating /workspace/data for rmdir test...${NC}"
nexus write /workspace/data/testfile.txt "test content" --data-dir "$DATA_DIR"

# Test 24: Remove directory (should fail - not empty)
test_command "Try to remove non-empty directory" \
    bash -c "! nexus rmdir /workspace/data --force --data-dir $DATA_DIR 2>/dev/null"

# Test 25: Remove directory recursively
test_command "Remove directory recursively" \
    nexus rmdir /workspace/data --recursive --force --data-dir "$DATA_DIR"

# Test 26: Version command
test_command "Show version information" \
    nexus version --data-dir "$DATA_DIR"

# Test 27: Help command
test_command "Show help" \
    nexus --help

# Test 28: Command-specific help
test_command "Show ls command help" \
    nexus ls --help

# Test 29: Write multiple test files for advanced grep
echo -e "${BLUE}Creating test files for advanced operations...${NC}"
nexus write /workspace/test1.py "# TODO: implement feature\ndef test():\n    pass" --data-dir "$DATA_DIR"
nexus write /workspace/test2.py "def another_test():\n    # TODO: add tests\n    return 42" --data-dir "$DATA_DIR"
nexus write /workspace/test3.txt "This file has TODO items\nAnd ERROR messages" --data-dir "$DATA_DIR"

test_command "Grep with multiple matches" \
    nexus grep "TODO" --data-dir "$DATA_DIR"

# Test 30: Complex glob pattern
test_command "Complex glob with test_*.py pattern" \
    nexus glob "test*.py" --path /workspace --data-dir "$DATA_DIR"

# Test 31: Export metadata to JSONL
test_command "Export all metadata to JSONL" \
    nexus export "$TEST_WORKSPACE/metadata-export.jsonl" --data-dir "$DATA_DIR"

# Test 32: Verify export file exists
test_command "Verify export file was created" \
    test -f "$TEST_WORKSPACE/metadata-export.jsonl"

# Test 33: Export with prefix filter
test_command "Export only /workspace metadata" \
    nexus export "$TEST_WORKSPACE/workspace-export.jsonl" --prefix /workspace --data-dir "$DATA_DIR"

# Test 34: Create a new test workspace for import testing
IMPORT_DATA_DIR="$TEST_WORKSPACE/import-test-data"
test_command "Create import test workspace" \
    mkdir -p "$IMPORT_DATA_DIR"

# Test 35: Import metadata to new workspace
test_command "Import metadata from export file" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --data-dir "$IMPORT_DATA_DIR"

# Test 36: Verify imported files exist in metadata
test_command "List imported files" \
    nexus ls / --data-dir "$IMPORT_DATA_DIR"

# Test 37: Re-import with skip existing (should skip all)
test_command "Re-import should skip existing files" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --data-dir "$IMPORT_DATA_DIR"

# Test 38: Import with overwrite
test_command "Import with overwrite flag" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --overwrite --data-dir "$IMPORT_DATA_DIR"

# Test 39: Test export/import workflow end-to-end
test_command "End-to-end export/import workflow" \
    bash -c "nexus export $TEST_WORKSPACE/full-backup.jsonl --data-dir $DATA_DIR && \
             nexus import $TEST_WORKSPACE/full-backup.jsonl --data-dir $IMPORT_DATA_DIR"

# ============================================================
# Advanced Export/Import Tests (Issue #35)
# ============================================================
echo -e "\n${BLUE}Testing advanced export/import features...${NC}"

# Test 39a: Import with conflict-mode=overwrite
test_command "Import with conflict-mode=overwrite" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --conflict-mode overwrite --data-dir "$IMPORT_DATA_DIR"

# Test 39b: Import with conflict-mode=skip (default)
test_command "Import with conflict-mode=skip" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --conflict-mode skip --data-dir "$IMPORT_DATA_DIR"

# Test 39c: Import with dry-run mode
test_command "Import with dry-run mode (no changes)" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --dry-run --data-dir "$IMPORT_DATA_DIR"

# ============================================================
# Work Detection CLI Tests (Issue #69)
# ============================================================
echo -e "\n${BLUE}Testing work detection CLI...${NC}"

# Create a separate workspace for work tests
WORK_DATA_DIR="$TEST_WORKSPACE/work-test-data"
test_command "Create work test workspace" \
    mkdir -p "$WORK_DATA_DIR"

# Test 40: Initialize work workspace
test_command "Initialize work test workspace" \
    nexus init "$WORK_DATA_DIR"

# Create work items using Python for setup
cat > "$TEST_WORKSPACE/setup_work.py" << 'EOF'
import sys
import nexus
from datetime import datetime, UTC

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir + "/nexus-data"})

# Create work item files
work_items = [
    ("/jobs/task1.json", b'{"task": "process_data"}'),
    ("/jobs/task2.json", b'{"task": "train_model"}'),
    ("/jobs/task3.json", b'{"task": "analyze"}'),
    ("/jobs/task4.json", b'{"task": "report"}'),
    ("/jobs/task5.json", b'{"task": "cleanup"}'),
]

for path, content in work_items:
    nx.write(path, content)

# Set work metadata
nx.metadata.set_file_metadata("/jobs/task1.json", "status", "ready")
nx.metadata.set_file_metadata("/jobs/task1.json", "priority", 1)

nx.metadata.set_file_metadata("/jobs/task2.json", "status", "in_progress")
nx.metadata.set_file_metadata("/jobs/task2.json", "priority", 2)
nx.metadata.set_file_metadata("/jobs/task2.json", "worker_id", "worker-001")
nx.metadata.set_file_metadata("/jobs/task2.json", "started_at", datetime.now(UTC).isoformat())

nx.metadata.set_file_metadata("/jobs/task3.json", "status", "pending")
nx.metadata.set_file_metadata("/jobs/task3.json", "priority", 3)

# Task 4 is blocked by task 2
task2_path_id = nx.metadata.get_path_id("/jobs/task2.json")
nx.metadata.set_file_metadata("/jobs/task4.json", "status", "blocked")
nx.metadata.set_file_metadata("/jobs/task4.json", "priority", 2)
nx.metadata.set_file_metadata("/jobs/task4.json", "depends_on", task2_path_id)

nx.metadata.set_file_metadata("/jobs/task5.json", "status", "ready")
nx.metadata.set_file_metadata("/jobs/task5.json", "priority", 5)

nx.close()
print("Work items created successfully")
EOF

# Test 41: Setup work items
test_command "Setup work items with metadata" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/setup_work.py\" \"$WORK_DATA_DIR\""

# Test 42: Query ready work items
test_command "Query ready work items" \
    nexus work ready --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 43: Query ready work with limit
test_command "Query ready work with limit" \
    nexus work ready --limit 1 --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 44: Query pending work items
test_command "Query pending work items" \
    nexus work pending --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 45: Query blocked work items
test_command "Query blocked work items" \
    nexus work blocked --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 46: Query in-progress work items
test_command "Query in-progress work items" \
    nexus work in-progress --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 47: Query work status (aggregate statistics)
test_command "Query work queue status" \
    nexus work status --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 48: Query ready work as JSON
test_command "Query ready work as JSON output" \
    nexus work ready --json --data-dir "$WORK_DATA_DIR/nexus-data"

# Test 49: Query status as JSON
test_command "Query status as JSON output" \
    nexus work status --json --data-dir "$WORK_DATA_DIR/nexus-data"

# ============================================================
# Validation Tests (Issue #37)
# ============================================================
echo -e "\n${BLUE}Testing type-level validation...${NC}"

# Create a separate test script for validation
cat > "$TEST_WORKSPACE/test_validation.py" << 'EOF'
import sys
import nexus
from nexus.core.metadata import FileMetadata
from nexus.core.exceptions import ValidationError

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir})

# Test 1: Invalid path (doesn't start with /)
print("Testing invalid path validation...")
try:
    invalid_meta = FileMetadata(
        path="invalid-path",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected invalid path: {e}")

# Test 2: Negative size
print("\nTesting negative size validation...")
try:
    invalid_meta = FileMetadata(
        path="/test/file.txt",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=-100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected negative size: {e}")

# Test 3: Path with null bytes
print("\nTesting path with null bytes validation...")
try:
    invalid_meta = FileMetadata(
        path="/test/file\x00.txt",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected path with null bytes: {e}")

# Test 4: Valid metadata should work
print("\nTesting valid metadata...")
try:
    valid_meta = FileMetadata(
        path="/test/valid.txt",
        backend_name="local",
        physical_path="/storage/valid.txt",
        size=1024,
    )
    nx.metadata.put(valid_meta)
    print("PASSED: Valid metadata accepted")
except ValidationError as e:
    print(f"FAILED: Valid metadata was rejected: {e}")
    sys.exit(1)

nx.close()
print("\nAll validation tests passed!")
EOF

# Test 50: Run validation tests
test_command "Run validation tests" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_validation.py\" \"$DATA_DIR\""

# Test 51: Test SQLAlchemy model validation
cat > "$TEST_WORKSPACE/test_model_validation.py" << 'EOF'
import sys
from nexus.storage.models import FilePathModel, FileMetadataModel, ContentChunkModel
from nexus.core.exceptions import ValidationError
from datetime import datetime, UTC

print("Testing SQLAlchemy model validation...")

# Test FilePathModel validation
print("\n1. Testing FilePathModel validation...")
try:
    invalid_model = FilePathModel(
        virtual_path="no-leading-slash",
        backend_id="local",
        physical_path="/storage/file.txt",
        size_bytes=100,
        tenant_id="test",
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test FileMetadataModel validation
print("\n2. Testing FileMetadataModel validation...")
try:
    invalid_model = FileMetadataModel(
        path_id="test-id",
        key="a" * 300,  # Too long
        value="test",
        created_at=datetime.now(UTC),
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test ContentChunkModel validation
print("\n3. Testing ContentChunkModel validation...")
try:
    invalid_model = ContentChunkModel(
        content_hash="tooshort",
        size_bytes=1024,
        storage_path="/storage/chunk",
        ref_count=1,
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test negative ref_count
print("\n4. Testing negative ref_count validation...")
try:
    invalid_model = ContentChunkModel(
        content_hash="a" * 64,
        size_bytes=1024,
        storage_path="/storage/chunk",
        ref_count=-1,  # Negative
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

print("\nAll SQLAlchemy model validation tests passed!")
EOF

test_command "Test SQLAlchemy model validation" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_model_validation.py\""

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Total tests run: ${TESTS_RUN}"
echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    TESTS_FAILED=$((TESTS_RUN - TESTS_PASSED))
    echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi
