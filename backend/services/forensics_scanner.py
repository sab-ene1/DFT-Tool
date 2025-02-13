"""Forensics scanner service for collecting file metadata and hashes."""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from functools import partial
import re

from utils.logging_config import get_logger
from config.config_manager import ConfigManager, ScanningConfig
from utils.exceptions import DFTError, FileSystemError, ValidationError, ProcessingError

logger = get_logger(__name__)

class PathValidator:
    """Validates and sanitizes file paths."""
    
    def __init__(self, base_dir: Path, config: ScanningConfig):
        """
        Initialize path validator.
        
        Args:
            base_dir: Base directory for scanning
            config: Scanning configuration
        """
        self.base_dir = base_dir.resolve()
        self.config = config
        self.symlink_cache: Set[Path] = set()
        
    def is_valid_path(self, path: Path) -> bool:
        """
        Check if a path is valid and safe to process.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is valid and safe
        """
        try:
            # Resolve path (follow symlinks)
            resolved_path = path.resolve()
            
            # Check if path is within base directory
            if not str(resolved_path).startswith(str(self.base_dir)):
                logger.warning(f"Path {path} is outside base directory")
                return False
                
            # Check for symlink loops
            if resolved_path in self.symlink_cache:
                logger.warning(f"Symlink loop detected at {path}")
                return False
                
            if path.is_symlink():
                self.symlink_cache.add(resolved_path)
                
            # Check excluded directories
            if any(excluded in path.parts for excluded in self.config.excluded_dirs):
                return False
                
            # Check excluded extensions
            if path.suffix.lower() in self.config.excluded_extensions:
                return False
                
            # Check hidden files
            if self.config.skip_hidden_files and path.name.startswith('.'):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating path {path}: {e}")
            raise ValidationError(f"Invalid path: {path}")

class FileMetadata:
    """Represents metadata for a single file."""
    
    def __init__(self, path: Path, config: ScanningConfig):
        """
        Initialize file metadata collector.
        
        Args:
            path: Path to file
            config: Scanning configuration
        """
        self.path = path
        self.config = config
        self.stats = None
        self.error = None
        self._collect_metadata()
        
    def _collect_metadata(self) -> None:
        """Collect file metadata safely."""
        try:
            self.stats = self.path.stat()
        except Exception as e:
            self.error = str(e)
            logger.error(f"Error collecting metadata for {self.path}: {e}")
            raise FileSystemError(f"Could not collect metadata for {self.path}")
            
    def _calculate_hash(self) -> Optional[str]:
        """Calculate file hash using configured algorithm."""
        if self.stats is None:
            return None
            
        # Skip if file is too small
        if self.stats.st_size < self.config.min_file_size:
            return None
            
        # Skip if file is too large
        if self.stats.st_size > self.config.max_file_size:
            logger.info(f"Skipping hash for large file: {self.path}")
            return None
            
        try:
            hasher = getattr(hashlib, self.config.hash_algorithm)()
            with open(self.path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    hasher.update(byte_block)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {self.path}: {e}")
            raise ProcessingError(f"Could not calculate hash for {self.path}")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        if self.error:
            return {
                'path': str(self.path),
                'error': self.error,
                'timestamp': datetime.now().isoformat()
            }
            
        return {
            'path': str(self.path),
            'size': self.stats.st_size,
            'created': datetime.fromtimestamp(self.stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(self.stats.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(self.stats.st_atime).isoformat(),
            'file_hash': self._calculate_hash(),
            'timestamp': datetime.now().isoformat()
        }

def process_file(path: Path, config: ScanningConfig) -> Dict[str, Any]:
    """
    Process a single file (used for parallel processing).
    
    Args:
        path: Path to file
        config: Scanning configuration
        
    Returns:
        Dict containing file metadata
    """
    return FileMetadata(path, config).to_dict()

class ForensicsScanner:
    """Scanner for collecting forensic metadata from files."""
    
    def __init__(self, directory: str):
        """
        Initialize scanner.
        
        Args:
            directory: Directory to scan
        """
        self.directory = Path(directory)
        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
            
        self.config = ConfigManager().scanning
        self.path_validator = PathValidator(self.directory, self.config)
        logger.info(f"Initialized ForensicsScanner for directory: {directory}")
        
    def _get_file_list(self) -> List[Path]:
        """Get list of files to process."""
        files = []
        for root, _, filenames in os.walk(self.directory):
            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename
                if self.path_validator.is_valid_path(file_path):
                    files.append(file_path)
        return files
        
    def scan(self) -> List[Dict[str, Any]]:
        """
        Scan directory for files and collect metadata.
        
        Returns:
            List of dictionaries containing file metadata
        """
        logger.info(f"Starting scan of {self.directory}")
        
        try:
            files = self._get_file_list()
            logger.info(f"Found {len(files)} files to process")
            
            # Process files in parallel
            with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
                future_to_file = {
                    executor.submit(process_file, f, self.config): f 
                    for f in files
                }
                
                results = []
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        results.append({
                            'path': str(file_path),
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                        
            logger.info(f"Scan complete. Processed {len(results)} files")
            return results
            
        except Exception as e:
            logger.error(f"Error during directory scan: {e}", exc_info=True)
            raise DFTError(f"Error scanning directory: {e}")
            
    def save_results(self, results: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save scan results to file.
        
        Args:
            results: List of metadata dictionaries
            output_file: Path to output file
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'scan_timestamp': datetime.now().isoformat(),
                'scanned_directory': str(self.directory),
                'file_count': len(results),
                'configuration': {
                    'max_file_size': self.config.max_file_size,
                    'min_file_size': self.config.min_file_size,
                    'hash_algorithm': self.config.hash_algorithm,
                    'parallel_workers': self.config.parallel_workers
                },
                'files': results
            }
            
            with output_path.open('w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {e}")
            raise DFTError(f"Error saving results: {e}")
