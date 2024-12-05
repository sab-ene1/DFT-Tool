import os
import logging
import datetime
import socket
import string
import sys
import psutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from file_analyzer import FileAnalyzer
from network_analyzer import NetworkAnalyzer
from memory_analyzer import MemoryAnalyzer
from config import ForensicsConfig
from decorators import log_exception

class ForensicsTriageTool:
    def __init__(self, config_path: Optional[str] = None, custom_config: Optional[Dict[str, Any]] = None):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = {}
        if config_path:
            self.config.update(self.load_config(config_path))
        if custom_config:
            self.config.update(custom_config)
        
        self.results_dir = self.setup_results_directory()
        self.setup_logging()

        self.yara_rules_path = self.config.get('yara_rules_dir', ForensicsConfig.YARA_RULES_DIR)
        self.yara_rules_path = os.path.abspath(self.yara_rules_path)
        
        self.file_analyzer = FileAnalyzer(yara_rules_path=self.yara_rules_path)
        self.network_analyzer = NetworkAnalyzer()
        self.memory_analyzer = MemoryAnalyzer()

    @log_exception
    def setup_results_directory(self) -> str:
        base_dir = self.config.get('output_dir', ForensicsConfig.RESULTS_BASE_DIR)
        results_dir = os.path.join(base_dir, self.timestamp)
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        return results_dir

    @log_exception
    def setup_logging(self) -> None:
        log_file = os.path.join(self.results_dir, 'triage_tool.log')
        log_level_str = self.config.get('log_level', ForensicsConfig.LOG_LEVEL).upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        try:
            os.chmod(log_file, 0o600)
        except Exception as e:
            logging.warning(f"Could not set restrictive permissions on log file: {e}")
        logging.info(f"Starting forensics triage session at {self.timestamp}")

    @log_exception
    def load_config(self, config_path: str) -> Dict[str, Any]:
        import configparser

        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            config_dict = {section: dict(config[section]) for section in config.sections()}
            logging.info(f"Configuration loaded from {config_path}")
            return config_dict
        except Exception as e:
            logging.error(f"Error loading config file {config_path}: {e}")
            return {}

    @log_exception
    def get_system_info(self) -> Dict[str, Any]:
        system_info = {
            'disk': []
        }
        try:
            import ctypes
            from ctypes import windll, c_ulonglong, byref

            # Function to safely get disk space
            def get_disk_space(drive):
                free_bytes = c_ulonglong(0)
                total_bytes = c_ulonglong(0)
                used_bytes = c_ulonglong(0)

                try:
                    # Ensure drive path ends with backslash for Windows API
                    if not drive.endswith('\\'):
                        drive += '\\'
                        
                    if windll.kernel32.GetDiskFreeSpaceExW(drive, byref(free_bytes), byref(total_bytes), None):
                        total = total_bytes.value
                        free = free_bytes.value
                        used = total - free
                        percent_used = (used / total) * 100 if total > 0 else 0

                        return {
                            'mountpoint': drive,
                            'total': total,
                            'used': used,
                            'free': free,
                            'percent': percent_used
                        }
                except Exception as e:
                    logging.error(f"Error getting disk usage for {drive}: {e}")
                    return None

            # Get all logical drives
            drives_bitmask = windll.kernel32.GetLogicalDrives()
            for i in range(26):  # A-Z
                if drives_bitmask & (1 << i):
                    drive = f"{chr(65 + i)}:\\"
                    disk_info = get_disk_space(drive)
                    if disk_info:
                        system_info['disk'].append(disk_info)

            if system_info['disk']:
                logging.info(f"Retrieved disk usage for {len(system_info['disk'])} drives")
            else:
                logging.warning("No disk drives found or accessible")

        except Exception as e:
            logging.error(f"Comprehensive disk space retrieval error: {e}")

        return system_info

    @log_exception
    def system_scan(self, paths: Optional[List[str]] = None, max_depth: int = 3) -> List[Dict[str, Any]]:
        if not paths:
            if os.name == 'nt':
                paths = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            else:
                paths = [os.path.expanduser('~'), '/']
        
        scan_results = []
        for base_path in paths:
            try:
                for root, dirs, files in os.walk(base_path, topdown=True, followlinks=False):
                    current_depth = root[len(base_path):].count(os.sep)
                    if current_depth > max_depth:
                        del dirs[:]
                        continue
                    
                    dirs[:] = [d for d in dirs if not any(os.path.join(root, d).startswith(p) for p in ForensicsConfig.PROTECTED_PATHS)]
                    
                    file_paths = [os.path.join(root, f) for f in files]
                    if not file_paths:
                        continue

                    batch_size = ForensicsConfig.BATCH_SIZE
                    for i in range(0, len(file_paths), batch_size):
                        batch = file_paths[i:i + batch_size]
                        batch_results = self.file_analyzer.process_file_batch(batch)
                        scan_results.extend(batch_results)
            except Exception as e:
                logging.error(f"Error scanning path {base_path}: {e}")
        
        logging.info(f"System scan completed with {len(scan_results)} files processed.")
        return scan_results

    @log_exception
    def network_scan(self, target: str = "192.168.1.0/24", timeout: float = 2.0) -> Dict[str, Any]:
        try:
            arp_results = self.network_analyzer.perform_arp_scan(target, timeout)
            network_info = self.network_analyzer.get_network_info()
            
            logging.info("Network scan completed.")
            return {
                'arp_scan': arp_results,
                'network_info': network_info,
                'scan_timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Comprehensive network scan error: {e}")
            return {}

    @log_exception
    def memory_analysis(self) -> Dict[str, Any]:
        try:
            processes = self.memory_analyzer.analyze_running_processes()
            modules = self.memory_analyzer.analyze_loaded_modules()
            
            logging.info("Memory analysis completed.")
            return {
                'processes': processes,
                'modules': modules,
                'analysis_timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Comprehensive memory analysis error: {e}")
            return {}

    @log_exception
    def save_results(self, system_results: List[Dict[str, Any]], network_results: Dict[str, Any], memory_results: Optional[Dict[str, Any]] = None) -> None:
        try:
            import orjson

            results = {
                'system_scan': system_results,
                'network_scan': network_results,
                'memory_analysis': memory_results or {}
            }

            results_file = os.path.join(self.results_dir, 'forensics_results.json')
            with open(results_file, 'wb') as f:
                f.write(orjson.dumps(results, option=orjson.OPT_INDENT_2))
            
            logging.info(f"Results saved to {results_file}")

            self.create_visualizations(results)
            
        except Exception as e:
            logging.error(f"Error saving forensics results: {e}")

    def create_visualizations(self, results: Dict[str, Any]) -> None:
        try:
            self.create_system_visualizations(results.get('system_scan', []))
            self.create_network_visualizations(results.get('network_scan', {}))
            self.create_memory_visualizations(results.get('memory_analysis', {}))
        except Exception as e:
            logging.error(f"Error creating visualizations: {e}")

    def create_system_visualizations(self, results: List[Dict[str, Any]]) -> None:
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            
            # File Size Visualization
            file_sizes = [file.get('size_bytes', 0) for file in results if isinstance(file.get('size_bytes'), (int, float))]
            if file_sizes and len(file_sizes) > 0:
                fig = px.histogram(x=file_sizes, nbins=50, title='File Size Distribution')
                fig.update_layout(xaxis_title='File Size (Bytes)', yaxis_title='Number of Files')
                fig.write_html(os.path.join(self.results_dir, 'file_size_distribution.html'))
                logging.info("System visualization: File Size Distribution created.")
            else:
                logging.warning("No file size data available for visualization.")

            # Disk Usage Visualization
            system_info = self.get_system_info()
            disk_info = system_info.get('disk', [])
            
            if disk_info and len(disk_info) > 0:
                df_disk = pd.DataFrame(disk_info)
                
                # Pie Chart for Disk Usage
                fig_pie = px.pie(
                    values=df_disk['used'], 
                    names=df_disk['mountpoint'], 
                    title='Disk Usage by Partition'
                )
                fig_pie.write_html(os.path.join(self.results_dir, 'disk_usage_pie_chart.html'))
                
                # Bar Chart for Disk Usage
                fig_bar = px.bar(
                    df_disk, 
                    x='mountpoint', 
                    y=['used', 'free'], 
                    title='Disk Space Breakdown',
                    labels={'value': 'Bytes', 'variable': 'Space Type'}
                )
                fig_bar.write_html(os.path.join(self.results_dir, 'disk_usage_bar_chart.html'))
                
                logging.info("System visualization: Disk Usage charts created.")
            else:
                logging.warning("No disk usage data available for visualization.")
        
        except ImportError:
            logging.error("Plotly library not installed. Please install plotly to generate visualizations.")
        except Exception as e:
            logging.error(f"Error creating system visualizations: {e}")

    def create_network_visualizations(self, results: Dict[str, Any]) -> None:
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            
            arp_scan = results.get('arp_scan', [])
            if arp_scan:
                df = pd.DataFrame(arp_scan)
                if not df.empty:
                    fig = go.Figure(data=[go.Table(
                        header=dict(values=['IP Address', 'MAC Address', 'Timestamp'],
                                    fill_color='paleturquoise',
                                    align='left'),
                        cells=dict(values=[df.ip, df.mac, df.timestamp],
                                    fill_color='lavender',
                                    align='left'))
                    ])
                    fig.update_layout(title='Discovered Network Devices')
                    fig.write_html(os.path.join(self.results_dir, 'network_devices.html'))
                    
                    fig2 = px.scatter(df, x='timestamp', y='ip', 
                                     hover_data=['mac'],
                                     title='Network Device Discovery Timeline')
                    fig2.update_layout(xaxis_title='Timestamp', yaxis_title='IP Address')
                    fig2.write_html(os.path.join(self.results_dir, 'network_timeline.html'))
                    
                    logging.info("Network visualizations created successfully")
            else:
                logging.warning("No ARP scan data available for visualization.")
        except Exception as e:
            logging.error(f"Error creating network visualizations: {str(e)}")

    def create_memory_visualizations(self, results: Dict[str, Any]) -> None:
        try:
            import plotly.express as px
            import pandas as pd
            
            processes = results.get('processes', [])
            if processes:
                df_cpu = pd.DataFrame(processes)
                df_cpu = df_cpu.dropna(subset=['cpu_percent', 'name'])
                top_cpu = df_cpu.sort_values(by='cpu_percent', ascending=False).head(10)

                if not top_cpu.empty:
                    fig_cpu = px.bar(top_cpu, x='name', y='cpu_percent', title='Top 10 Processes by CPU Usage')
                    fig_cpu.update_layout(xaxis_title='Process Name', yaxis_title='CPU Usage (%)')
                    fig_cpu.write_html(os.path.join(self.results_dir, 'top_cpu_processes.html'))
                    logging.info("Memory visualization: Top CPU Processes created.")
                else:
                    logging.warning("No CPU usage data available for visualization.")

                df_mem = df_cpu.dropna(subset=['memory_percent'])
                top_mem = df_mem.sort_values(by='memory_percent', ascending=False).head(10)
                if not top_mem.empty:
                    fig_mem = px.bar(top_mem, x='name', y='memory_percent', title='Top 10 Processes by Memory Usage')
                    fig_mem.update_layout(xaxis_title='Process Name', yaxis_title='Memory Usage (%)')
                    fig_mem.write_html(os.path.join(self.results_dir, 'top_memory_processes.html'))
                    logging.info("Memory visualization: Top Memory Processes created.")
                else:
                    logging.warning("No memory usage data available for visualization.")
            else:
                logging.warning("No process data available for visualization.")
        except Exception as e:
            logging.error(f"Error creating memory visualizations: {e}")
