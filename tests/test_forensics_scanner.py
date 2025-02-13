"""Test suite for the forensics scanner module."""

import os
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

from backend.services.forensics_scanner import ForensicsScanner, FileMetadata, PathValidator
from backend.config.config_manager import ConfigManager

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_files(temp_test_dir):
    """Create sample files for testing."""
    # Create normal files
    (temp_test_dir / "file1.txt").write_text("Hello World")
    (temp_test_dir / "file2.txt").write_text("Test content")
    
    # Create nested directory
    nested_dir = temp_test_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "file3.txt").write_text("Nested content")
    
    # Create large file
    large_file = temp_test_dir / "large.bin"
    large_file.write_bytes(os.urandom(1024 * 1024))  # 1MB file
    
    # Create symlink (on non-Windows systems)
    if os.name != 'nt':
        (temp_test_dir / "link.txt").symlink_to(temp_test_dir / "file1.txt")
    
    return temp_test_dir

def test_scanner_initialization(temp_test_dir):
    """Test scanner initialization."""
    scanner = ForensicsScanner(str(temp_test_dir))
    assert scanner.directory == temp_test_dir
    assert scanner.config is not None

def test_scanner_invalid_directory():
    """Test scanner initialization with invalid directory."""
    with pytest.raises(ValueError):
        ForensicsScanner("/nonexistent/directory")

def test_file_metadata(sample_files):
    """Test file metadata collection."""
    config = ConfigManager().scanning
    file_path = sample_files / "file1.txt"
    metadata = FileMetadata(file_path, config)
    data = metadata.to_dict()
    
    assert "path" in data
    assert "size" in data
    assert "created" in data
    assert "modified" in data
    assert "accessed" in data
    assert "file_hash" in data
    assert "timestamp" in data
    
    # Verify hash is calculated for small files
    assert data["file_hash"] is not None

def test_large_file_handling(sample_files):
    """Test handling of large files."""
    config = ConfigManager().scanning
    file_path = sample_files / "large.bin"
    metadata = FileMetadata(file_path, config)
    data = metadata.to_dict()
    
    # Verify hash is skipped for large files
    if metadata.stats.st_size > config.max_file_size:
        assert data["file_hash"] is None

def test_path_validator(sample_files):
    """Test path validation."""
    config = ConfigManager().scanning
    validator = PathValidator(sample_files, config)
    
    # Test valid path
    assert validator.is_valid_path(sample_files / "file1.txt")
    
    # Test path outside base directory
    outside_path = Path("/tmp/outside.txt")
    assert not validator.is_valid_path(outside_path)
    
    # Test excluded extensions
    excluded_file = sample_files / "test.pyc"
    excluded_file.touch()
    assert not validator.is_valid_path(excluded_file)

def test_full_scan(sample_files):
    """Test complete directory scan."""
    scanner = ForensicsScanner(str(sample_files))
    results = scanner.scan()
    
    # Verify all files are found
    paths = {result["path"] for result in results}
    assert str(sample_files / "file1.txt") in paths
    assert str(sample_files / "file2.txt") in paths
    assert str(sample_files / "nested/file3.txt") in paths
    
    # Test saving results
    output_file = sample_files / "results.json"
    scanner.save_results(results, str(output_file))
    assert output_file.exists()
    
    # Verify saved data
    with output_file.open() as f:
        saved_data = json.load(f)
        assert "scan_timestamp" in saved_data
        assert "files" in saved_data
        assert "configuration" in saved_data
        assert len(saved_data["files"]) == len(results)

def test_error_handling(temp_test_dir):
    """Test error handling for inaccessible files."""
    # Create a file with no read permissions
    no_access_file = temp_test_dir / "no_access.txt"
    no_access_file.write_text("Secret")
    if os.name != 'nt':  # Skip on Windows
        no_access_file.chmod(0o000)
    
    scanner = ForensicsScanner(str(temp_test_dir))
    results = scanner.scan()
    
    # Find result for no_access file
    no_access_result = next(
        (r for r in results if r["path"] == str(no_access_file)), None
    )
    
    if os.name != 'nt':  # Skip on Windows
        assert no_access_result is not None
        assert "error" in no_access_result

def test_parallel_processing(sample_files):
    """Test parallel processing of files."""
    # Create many small files
    for i in range(100):
        (sample_files / f"test_{i}.txt").write_text(f"Content {i}")
    
    scanner = ForensicsScanner(str(sample_files))
    start_time = datetime.now()
    results = scanner.scan()
    end_time = datetime.now()
    
    # Verify all files were processed
    assert len(results) > 100
    
    # Verify parallel processing was faster than sequential would be
    # (this is a rough estimate, might need adjustment)
    processing_time = end_time - start_time
    assert processing_time < timedelta(seconds=30)
