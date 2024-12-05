import datetime
import os
import glob
import logging
import hashlib
from functools import lru_cache
from decorators import log_exception
import yara
from typing import Optional, List, Dict, Any
from config import ForensicsConfig

def is_safe_to_scan(file_path: str) -> bool:
    """
    Determine if a file is safe to scan based on path and permissions
    """
    # List of system files and directories to avoid
    PROTECTED_PATHS = [
        'hiberfil.sys', 
        'pagefile.sys', 
        'swapfile.sys', 
        'DumpStack.log.tmp',
        ':\\Windows\\',
        ':\\Program Files\\',
        ':\\Program Files (x86)\\',
        ':\\ProgramData\\',
        ':\\Users\\Default\\',
        ':\\Users\\Public\\'
    ]

    # Check if file path contains any protected path
    file_path = file_path.lower()
    if any(protected in file_path for protected in PROTECTED_PATHS):
        return False

    try:
        # Check file permissions
        return os.access(file_path, os.R_OK)
    except Exception:
        return False

def load_yara_rules(yara_rules_path: Optional[str] = None) -> Optional[Dict[str, yara.Rules]]:
    """
    Load YARA rules from a directory, handling multiple .yar files
    """
    if not yara_rules_path or not os.path.exists(yara_rules_path):
        logging.warning(f"YARA rules path does not exist: {yara_rules_path}")
        return None

    try:
        # Ensure path is a directory
        if not os.path.isdir(yara_rules_path):
            logging.warning(f"YARA rules path is not a directory: {yara_rules_path}")
            return None

        # Find all .yar files in the directory
        yar_files = [
            f for f in os.listdir(yara_rules_path) 
            if f.lower().endswith('.yar') or f.lower().endswith('.yara')
        ]

        if not yar_files:
            logging.warning(f"No YARA rule files found in {yara_rules_path}")
            return None

        # Compile rules from each file
        compiled_rules = {}
        for yar_file in yar_files:
            full_path = os.path.join(yara_rules_path, yar_file)
            try:
                rule_name = os.path.splitext(yar_file)[0]
                compiled_rules[rule_name] = yara.compile(full_path)
                logging.info(f"Loaded YARA rule: {rule_name}")
            except Exception as e:
                logging.warning(f"Could not compile YARA rule {yar_file}: {e}")

        return compiled_rules if compiled_rules else None

    except Exception as e:
        logging.error(f"Error loading YARA rules from {yara_rules_path}: {e}")
        return None

def process_single_file_wrapper(file_path: str, yara_rules_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Process a single file with optional YARA scanning
    """
    # Skip system files or files we can't read
    if not is_safe_to_scan(file_path):
        logging.debug(f"Skipping file due to safety checks: {file_path}")
        return None

    try:
        # Hash the file
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                hash_obj.update(byte_block)
        sha256_hash = hash_obj.hexdigest()

        # Get file stats
        file_stat = os.stat(file_path)
        file_info = {
            'file_path': file_path,
            'sha256_hash': sha256_hash,
            'size_bytes': file_stat.st_size,
            'created_at': datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            'modified_at': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'accessed_at': datetime.datetime.fromtimestamp(file_stat.st_atime).isoformat(),
            'is_executable': os.access(file_path, os.X_OK)
        }

        # Perform YARA scanning if rules are available
        if yara_rules_path:
            try:
                yara_rules = load_yara_rules(yara_rules_path)
                if yara_rules:
                    all_matches = []
                    for rule_name, rule_set in yara_rules.items():
                        try:
                            matches = rule_set.match(file_path)
                            if matches:
                                all_matches.extend([f"{rule_name}:{match.rule}" for match in matches])
                        except Exception as e:
                            logging.warning(f"YARA scanning error for {file_path} with rule {rule_name}: {e}")
                    
                    file_info['yara_matches'] = all_matches
            except Exception as e:
                logging.warning(f"YARA scanning error for {file_path}: {e}")
                file_info['yara_matches'] = []

        return file_info

    except PermissionError:
        logging.debug(f"Permission denied scanning file: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return None

class FileAnalyzer:
    def __init__(self, yara_rules_path: Optional[str] = None):
        self.yara_rules_path = yara_rules_path
    
    @log_exception
    @lru_cache(maxsize=10000)
    def hash_file(self, file_path: str, hash_algorithm: str = 'sha256') -> Optional[str]:
        if not is_safe_to_scan(file_path):
            logging.info(f"Skipping protected system file: {file_path}")
            return "PROTECTED_SYSTEM_FILE"

        try:
            hash_obj = hashlib.new(hash_algorithm)
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    hash_obj.update(byte_block)
            return hash_obj.hexdigest()
        except PermissionError:
            logging.warning(f"Permission denied for file: {file_path}")
            return "ACCESS_DENIED"
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return "FILE_NOT_FOUND"
        except Exception as e:
            logging.error(f"Unexpected error hashing file {file_path}: {e}")
            return None
    
    @log_exception
    def process_file_batch(self, files: List[str], max_workers: Optional[int] = None) -> List[Dict[str, Any]]:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        results = []
        max_workers = max_workers or os.cpu_count()
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Pass yara_rules_path instead of compiled rules
            future_to_file = {
                executor.submit(process_single_file_wrapper, file, self.yara_rules_path): file 
                for file in files
            }
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logging.error(f"Error processing file {future_to_file[future]}: {e}")
        return results
