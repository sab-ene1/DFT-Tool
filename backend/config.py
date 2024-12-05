# config.py
import os

class ForensicsConfig:
    MAX_RETRIES = 3
    BATCH_SIZE = 1000
    SCAN_TIMEOUT = 300
    LOG_LEVEL = 'INFO'
    RESULTS_BASE_DIR = 'results'
    YARA_RULES_DIR = 'yara_rules'

    PROTECTED_PATHS = {
        "/etc/", "/root/", "/var/log/"
    } if os.name != 'nt' else {
        "\\Windows\\System32\\config\\", "\\Windows\\System32\\catroot2\\"
    }
