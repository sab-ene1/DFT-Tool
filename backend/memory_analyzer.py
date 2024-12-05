import logging
import psutil
from typing import List, Dict, Any
import datetime
from decorators import log_exception

class MemoryAnalyzer:
    @log_exception
    def analyze_running_processes(self) -> List[Dict[str, Any]]:
        processes = []
        basic_info = ['pid', 'name', 'username', 'memory_percent', 'cpu_percent', 'status']
        
        try:
            
            for proc in psutil.process_iter(basic_info):
                try:
                    process_info = proc.info.copy()
                    
                    
                    process_info['name'] = process_info.get('name', 'Unknown')
                    process_info['cpu_percent'] = process_info.get('cpu_percent', 0.0)
                    process_info['memory_percent'] = process_info.get('memory_percent', 0.0)
                    
                 
                    try:
                        process_info['cmdline'] = proc.cmdline()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info['cmdline'] = []
                        
                    try:
                        process_info['cwd'] = proc.cwd()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info['cwd'] = 'Unknown'
                        
                    try:
                        open_files = proc.open_files()
                        process_info['open_files'] = [f.path for f in open_files] if open_files else []
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info['open_files'] = []
                    
                    try:
                        connections = proc.connections(kind='all')
                        process_info['connections'] = [
                            {
                                'fd': conn.fd, 
                                'family': str(conn.family),
                                'type': str(conn.type),
                                'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                                'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                                'status': conn.status
                            } 
                            for conn in connections if conn.laddr
                        ]
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info['connections'] = []
                    
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    logging.warning(f"Error getting process info for PID {process_info.get('pid', 'Unknown')}: {e}")
                    continue
            
            if processes:
                logging.info(f"Analyzed {len(processes)} running processes")
            else:
                logging.warning("No process information could be collected. Try running with elevated privileges.")
            return processes
        
        except Exception as e:
            logging.error(f"Comprehensive process analysis error: {e}")
            return []

    @log_exception
    def analyze_loaded_modules(self) -> List[Dict[str, Any]]:
        modules = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    memory_maps = proc.memory_maps()
                    for mmap in memory_maps:
                        module_info = {
                            'pid': proc.pid,
                            'process_name': proc.name(),
                            'path': mmap.path,
                            'rss': mmap.rss,
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                        # Handles potential missing size attribute
                        try:
                            module_info['size'] = mmap.size
                        except AttributeError:
                            
                            module_info['size'] = getattr(mmap, 'private_clean', 0) + getattr(mmap, 'private_dirty', 0) + getattr(mmap, 'shared_clean', 0) + getattr(mmap, 'shared_dirty', 0)
                        modules.append(module_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logging.info(f"Analyzed {len(modules)} loaded modules")
            return modules
        
        except Exception as e:
            logging.error(f"Comprehensive module analysis error: {e}")
            return []
