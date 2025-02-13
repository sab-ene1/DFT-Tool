"""Digital Forensics Triage Tool - A lightweight tool for initial forensic analysis."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from services.forensics_scanner import ForensicsScanner
from utils.logging_config import setup_logging, get_logger
from utils.exceptions import DFTError

logger = get_logger(__name__)

class ForensicsTriageTool:
    """Main class for forensic triage operations."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the forensics triage tool.
        
        Args:
            output_dir: Optional directory for output files. Defaults to './forensics_output'
        """
        self.output_dir = Path(output_dir or './forensics_output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup logging
        log_file = self.output_dir / f"forensics_triage_{self.timestamp}.log"
        setup_logging(log_file)
        logger.info(f"Initialized ForensicsTriageTool. Output directory: {self.output_dir}")

    def scan_directory(self, target_dir: str, max_file_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform forensic scan of a directory.
        
        Args:
            target_dir: Directory to scan
            max_file_size: Optional maximum file size in bytes for hash calculation
            
        Returns:
            Dictionary containing scan results
        """
        try:
            scanner = ForensicsScanner(target_dir)
            results = scanner.scan(max_size=max_file_size)
            
            # Save results
            output_file = self.output_dir / f"scan_results_{self.timestamp}.json"
            scanner.save_results(results, str(output_file))
            
            return {
                'status': 'success',
                'scanned_directory': target_dir,
                'file_count': len(results),
                'output_file': str(output_file)
            }
            
        except DFTError as e:
            logger.error(f"Error during directory scan: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during scan: {e}")
            return {
                'status': 'error',
                'error': 'An unexpected error occurred'
            }

def main():
    """Main entry point for the forensics triage tool."""
    parser = argparse.ArgumentParser(
        description='Digital Forensics Triage Tool - Quick analysis of directories and files'
    )
    parser.add_argument(
        'directory',
        type=str,
        help='Directory to scan for forensic analysis'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./forensics_output',
        help='Directory for output files (default: ./forensics_output)'
    )
    parser.add_argument(
        '--max-file-size',
        type=int,
        help='Maximum file size in bytes for hash calculation'
    )
    
    args = parser.parse_args()
    
    try:
        tool = ForensicsTriageTool(args.output_dir)
        results = tool.scan_directory(args.directory, args.max_file_size)
        
        if results['status'] == 'success':
            print(f"\nScan complete!")
            print(f"- Scanned directory: {results['scanned_directory']}")
            print(f"- Files processed: {results['file_count']}")
            print(f"- Results saved to: {results['output_file']}")
            print(f"- Check the log file in the output directory for detailed information")
            sys.exit(0)
        else:
            print(f"\nError during scan: {results['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
