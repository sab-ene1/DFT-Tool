import argparse
import logging
import sys
from forensics_triage_tool import ForensicsTriageTool
from config import ForensicsConfig

def main():
    parser = argparse.ArgumentParser(description='Advanced Forensics Triage Tool')
    parser.add_argument('--config', type=str, help='Path to custom configuration file')
    parser.add_argument('--scan-type', choices=['system', 'network', 'memory', 'all'], default='all', help='Type of forensic scan to perform')
    parser.add_argument('--target', type=str, default='192.168.1.0/24', help='Network target for scanning (for network scan)')
    parser.add_argument('--output-dir', type=str, help='Custom output directory for results')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set logging verbosity')
    parser.add_argument('--max-depth', type=int, default=3, help='Maximum directory depth for system scan')
    parser.add_argument('--timeout', type=float, default=2.0, help='Network scan timeout in seconds')
    parser.add_argument('--yara-rules-dir', type=str, default=ForensicsConfig.YARA_RULES_DIR, help='Directory containing YARA rule files')
    
    args = parser.parse_args()

    try:
        forensics_tool = ForensicsTriageTool(
            config_path=args.config,
            custom_config={
                'log_level': args.log_level,
                'output_dir': args.output_dir if args.output_dir else ForensicsConfig.RESULTS_BASE_DIR,
                'yara_rules_dir': args.yara_rules_dir
            }
        )
        system_results, network_results, memory_results = [], {}, {}
        
        if args.scan_type in ['system', 'all']:
            system_results = forensics_tool.system_scan(max_depth=args.max_depth)
        
        if args.scan_type in ['network', 'all']:
            network_results = forensics_tool.network_scan(target=args.target, timeout=args.timeout)
        
        if args.scan_type in ['memory', 'all']:
            memory_results = forensics_tool.memory_analysis()

        forensics_tool.save_results(system_results, network_results, memory_results)
        
    except Exception as e:
        logging.error(f"Forensics triage failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
