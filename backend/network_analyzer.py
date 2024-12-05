import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from decorators import log_exception
from scapy.all import ARP, Ether, srp, conf
from typing import List, Dict, Optional
from config import ForensicsConfig
import psutil
import datetime
import ctypes

class NetworkAnalyzer:
    @retry(stop=stop_after_attempt(ForensicsConfig.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
    @log_exception
    def perform_arp_scan(self, target: Optional[str] = None, timeout: float = 2.0) -> List[Dict[str, str]]:
        if not target:
            logging.error("No target specified for ARP scan.")
            return []
        
        try:
            #checks if we have admin permission or not
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                logging.warning("ARP scanning requires administrator privileges. Running in limited mode.")
                # gets basic network info
                interfaces = psutil.net_if_addrs()
                results = []
                for interface, addrs in interfaces.items():
                    for addr in addrs:
                        if addr.family == psutil.AF_INET:  # IPv4
                            results.append({
                                'ip': addr.address,
                                'mac': 'Unknown (limited access)',
                                'timestamp': datetime.datetime.now().isoformat(),
                                'interface': interface
                            })
                if results:
                    logging.info(f"Found {len(results)} network interfaces in limited mode")
                    return results
            
            # If we have admin rights, proceed with ARP scan
            arp = ARP(pdst=target)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp
            
            answered, _ = srp(packet, timeout=timeout, verbose=False)
            
            results = [
                {
                    'ip': received.psrc, 
                    'mac': received.hwsrc,
                    'timestamp': datetime.datetime.now().isoformat()
                } 
                for sent, received in answered
            ]
            
            logging.info(f"ARP scan discovered {len(results)} devices")
            return results
        
        except PermissionError:
            logging.error("ARP scan failed due to insufficient permissions. Try running the tool with elevated privileges.")
            return []
        except Exception as e:
            logging.error(f"Comprehensive ARP scan error: {e}")
            return []

    @log_exception
    def get_network_info(self) -> Dict[str, str]:
        try:
            net_io = psutil.net_io_counters()
            network_interfaces = psutil.net_if_addrs()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'scan_time': datetime.datetime.now().isoformat(),
                'active_interfaces': list(network_interfaces.keys())
            }
        except Exception as e:
            logging.error(f"Error retrieving network information: {e}")
            return {}

