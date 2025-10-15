#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LibreSpeed SpeedTest implementation
"""

import time
import json
import math
import threading
import concurrent.futures
from typing import List, Dict, Optional, Tuple, Callable
from urllib.parse import urljoin, urlparse
import requests
from .progress import show_spinner, show_progress_bar, create_multi_stage, create_speed_progress


class Server:
    """Represents a LibreSpeed server"""
    
    def __init__(self, server_dict: Dict):
        self.id = server_dict.get('id', 0)
        self.name = server_dict.get('name', '')
        self.server = server_dict.get('server', '')
        self.dl_url = server_dict.get('dlURL', 'garbage.php')
        self.ul_url = server_dict.get('ulURL', 'empty.php')
        self.ping_url = server_dict.get('pingURL', 'empty.php')
        self.get_ip_url = server_dict.get('getIpURL', 'getIP.php')
        self.sponsor_name = server_dict.get('sponsorName', '')
        self.sponsor_url = server_dict.get('sponsorURL', '')
        
    def __repr__(self):
        return f"Server(id={self.id}, name={self.name}, server={self.server})"


class SpeedTest:
    """LibreSpeed SpeedTest implementation"""
    
    DEFAULT_SERVER_LIST = "https://internetspeedtest.net/api/servers"
    USER_AGENT = "internetspeedtest-cli-python/1.0.0"
    
    def __init__(self, source: Optional[str] = None, timeout: int = 15, secure: bool = False):
        """
        Initialize SpeedTest
        
        Args:
            source: Source IP address to bind to
            timeout: HTTP timeout in seconds
            secure: Use HTTPS for server communication
        """
        self.source = source
        self.timeout = timeout
        self.secure = secure
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        
    def get_servers(self, server_list_url: Optional[str] = None, 
                    exclude: Optional[List[int]] = None,
                    specific: Optional[List[int]] = None) -> List[Server]:
        """
        Fetch and parse server list
        
        Args:
            server_list_url: Custom server list URL
            exclude: List of server IDs to exclude
            specific: List of specific server IDs to use
            
        Returns:
            List of Server objects
        """
        url = server_list_url or self.DEFAULT_SERVER_LIST
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            servers_data = response.json()
        except Exception as e:
            raise Exception(f"Failed to fetch server list: {e}")
        
        servers = [Server(s) for s in servers_data]
        
        # Filter servers
        if specific:
            servers = [s for s in servers if s.id in specific]
        elif exclude:
            servers = [s for s in servers if s.id not in exclude]
            
        # Force HTTPS if secure option is set
        if self.secure:
            for server in servers:
                if server.server.startswith('http://'):
                    server.server = server.server.replace('http://', 'https://')
                elif not server.server.startswith('http'):
                    server.server = 'https://' + server.server.lstrip('/')
                    
        return servers
    
    def ping(self, server: Server, count: int = 10) -> Tuple[float, float]:
        """
        Measure ping and jitter to a server
        
        Args:
            server: Server to ping
            count: Number of ping requests
            
        Returns:
            Tuple of (average_ping, jitter) in milliseconds
        """
        url = urljoin(server.server, server.ping_url)
        pings = []
        
        for _ in range(count):
            start = time.time()
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    ping_ms = (time.time() - start) * 1000
                    pings.append(ping_ms)
            except Exception:
                pass
                
        if not pings:
            return 0.0, 0.0
            
        avg_ping = sum(pings) / len(pings)
        
        # Calculate jitter
        jitter = 0.0
        if len(pings) > 1:
            last_ping = pings[0]
            for i in range(1, len(pings)):
                inst_jitter = abs(last_ping - pings[i])
                if i > 1:
                    if jitter > inst_jitter:
                        jitter = jitter * 0.7 + inst_jitter * 0.3
                    else:
                        jitter = inst_jitter * 0.2 + jitter * 0.8
                last_ping = pings[i]
                
        return round(avg_ping, 2), round(jitter, 2)
    
    def download(self, server: Server, duration: int = 15, 
                 concurrent: int = 3, chunks: int = 100) -> Tuple[float, int]:
        """
        Measure download speed
        
        Args:
            server: Server to test with
            duration: Test duration in seconds
            concurrent: Number of concurrent connections
            chunks: Number of chunks to request
            
        Returns:
            Tuple of (speed_mbps, bytes_downloaded)
        """
        url = urljoin(server.server, server.dl_url)
        
        # Add query parameters for chunks
        if '?' in url:
            url = f"{url}&ckSize={chunks}"
        else:
            url = f"{url}?ckSize={chunks}"
            
        total_bytes = 0
        lock = threading.Lock()
        stop_event = threading.Event()
        
        # Create speed test progress indicator
        speed_progress = create_speed_progress()
        speed_progress.start_test("Download")
        
        def download_worker():
            nonlocal total_bytes
            while not stop_event.is_set():
                try:
                    response = self.session.get(url, timeout=self.timeout, stream=True)
                    for chunk in response.iter_content(chunk_size=8192):
                        if stop_event.is_set():
                            break
                        if chunk:
                            with lock:
                                total_bytes += len(chunk)
                except Exception:
                    pass
                    
        # Start worker threads
        threads = []
        start_time = time.time()
        
        for _ in range(concurrent):
            t = threading.Thread(target=download_worker)
            t.daemon = True
            t.start()
            threads.append(t)
            
        # Monitor progress during test
        progress_start = time.time()
        while time.time() - progress_start < duration:
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_speed = ((total_bytes * 8) / elapsed) / 1_000_000  # Mbps
                speed_progress.update_speed(current_speed, total_bytes)
            time.sleep(0.1)  # Update every 100ms
            
        stop_event.set()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=1)
            
        elapsed = time.time() - start_time
        
        # Calculate speed in Mbps
        if elapsed > 0:
            speed_bps = (total_bytes * 8) / elapsed
            speed_mbps = speed_bps / 1_000_000
        else:
            speed_mbps = 0.0
            
        # Clean up progress indicator
        speed_progress.finish_test(speed_mbps, "Download")
            
        return round(speed_mbps, 2), total_bytes
    
    def upload(self, server: Server, duration: int = 15,
               concurrent: int = 3, upload_size: int = 1024) -> Tuple[float, int]:
        """
        Measure upload speed
        
        Args:
            server: Server to test with
            duration: Test duration in seconds
            concurrent: Number of concurrent connections
            upload_size: Size of upload payload in KiB
            
        Returns:
            Tuple of (speed_mbps, bytes_uploaded)
        """
        url = urljoin(server.server, server.ul_url)
        
        # Create upload data
        upload_data = b'0' * (upload_size * 1024)
        
        total_bytes = 0
        lock = threading.Lock()
        stop_event = threading.Event()
        
        # Create speed test progress indicator
        speed_progress = create_speed_progress()
        speed_progress.start_test("Upload")
        
        def upload_worker():
            nonlocal total_bytes
            while not stop_event.is_set():
                try:
                    response = self.session.post(
                        url, 
                        data=upload_data,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        with lock:
                            total_bytes += len(upload_data)
                except Exception:
                    pass
                    
        # Start worker threads
        threads = []
        start_time = time.time()
        
        for _ in range(concurrent):
            t = threading.Thread(target=upload_worker)
            t.daemon = True
            t.start()
            threads.append(t)
            
        # Monitor progress during test
        progress_start = time.time()
        while time.time() - progress_start < duration:
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_speed = ((total_bytes * 8) / elapsed) / 1_000_000  # Mbps
                speed_progress.update_speed(current_speed, total_bytes)
            time.sleep(0.1)  # Update every 100ms
            
        stop_event.set()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=1)
            
        elapsed = time.time() - start_time
        
        # Calculate speed in Mbps
        if elapsed > 0:
            speed_bps = (total_bytes * 8) / elapsed
            speed_mbps = speed_bps / 1_000_000
        else:
            speed_mbps = 0.0
            
        # Clean up progress indicator
        speed_progress.finish_test(speed_mbps, "Upload")
            
        return round(speed_mbps, 2), total_bytes
    
    def get_ip_info(self, server: Server) -> Dict:
        """
        Get IP information from server
        
        Args:
            server: Server to query
            
        Returns:
            Dictionary with IP information
        """
        url = urljoin(server.server, server.get_ip_url)
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                return response.json()
            except:
                # If not JSON, return text as IP
                return {'ip': response.text.strip()}
        except Exception as e:
            return {'error': str(e)}
    
    def find_best_server(self, servers: List[Server], max_workers: int = 10, 
                         timeout_per_server: int = 5) -> Optional[Server]:
        """
        Find the best server based on ping using concurrent threading
        
        Args:
            servers: List of servers to test
            max_workers: Maximum number of concurrent threads
            timeout_per_server: Timeout for each server ping test
            
        Returns:
            Server with lowest ping, or None
        """
        if not servers:
            return None
            
        import concurrent.futures
        import threading
        
        # Results storage
        results = {}
        results_lock = threading.Lock()
        
        def ping_server(server: Server) -> None:
            """Ping a single server and store result"""
            try:
                ping, jitter = self.ping(server, count=3)
                if ping > 0:
                    with results_lock:
                        results[server] = {'ping': ping, 'jitter': jitter}
            except Exception as e:
                # Server failed, skip it
                pass
        
        # Use ThreadPoolExecutor for concurrent pinging
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ping tasks
            futures = [
                executor.submit(ping_server, server) 
                for server in servers
            ]
            
            # Wait for all tasks to complete with proper timeout handling
            try:
                # Use wait() instead of as_completed() to avoid timeout issues
                done, not_done = concurrent.futures.wait(
                    futures, 
                    timeout=timeout_per_server * 2,
                    return_when=concurrent.futures.ALL_COMPLETED
                )
                
                # Process completed futures
                for future in done:
                    try:
                        future.result(timeout=0.1)
                    except Exception:
                        pass  # Server failed, already handled in ping_server
                
                # Cancel any remaining futures
                for future in not_done:
                    future.cancel()
                    
            except Exception as e:
                # If something goes wrong, cancel all futures
                for future in futures:
                    future.cancel()
        
        # Find the best server from results
        if not results:
            return None
            
        best_server = min(results.keys(), key=lambda s: results[s]['ping'])
        return best_server
    
    def find_best_server_fast(self, servers: List[Server], max_workers: int = 15,
                             early_exit_threshold: float = 10.0,
                             progress_callback: Optional[Callable] = None) -> Optional[Server]:
        """
        Advanced version with early exit and progress reporting
        
        Args:
            servers: List of servers to test
            max_workers: Maximum number of concurrent threads
            early_exit_threshold: Exit early if ping < this value (ms)
            progress_callback: Function called with (completed, total, best_so_far)
            
        Returns:
            Server with lowest ping, or None
        """
        if not servers:
            return None
            
        import concurrent.futures
        import threading
        
        # Results storage
        results = {}
        results_lock = threading.Lock()
        completed_count = 0
        should_exit = threading.Event()
        
        def ping_server_with_early_exit(server: Server) -> Optional[Server]:
            """Ping server with early exit capability"""
            nonlocal completed_count
            
            if should_exit.is_set():
                return None
                
            try:
                ping, jitter = self.ping(server, count=2)  # Reduced count for speed
                
                with results_lock:
                    if ping > 0:
                        results[server] = {'ping': ping, 'jitter': jitter}
                        
                        # Check for early exit
                        if ping < early_exit_threshold:
                            should_exit.set()
                            
                    completed_count += 1
                    
                    # Progress callback
                    if progress_callback:
                        best_so_far = None
                        if results:
                            best_so_far = min(results.keys(), key=lambda s: results[s]['ping'])
                        progress_callback(completed_count, len(servers), best_so_far)
                        
                return server if ping > 0 else None
                
            except Exception:
                with results_lock:
                    completed_count += 1
                    if progress_callback:
                        best_so_far = None
                        if results:
                            best_so_far = min(results.keys(), key=lambda s: results[s]['ping'])
                        progress_callback(completed_count, len(servers), best_so_far)
                return None
        
        # Use ThreadPoolExecutor with smaller timeout for faster results
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ping tasks
            futures = [
                executor.submit(ping_server_with_early_exit, server)
                for server in servers
            ]
            
            # Process results with better timeout handling
            try:
                # Check for completion or early exit periodically
                start_time = time.time()
                max_wait_time = 30
                
                while time.time() - start_time < max_wait_time:
                    if should_exit.is_set():
                        # Early exit triggered, cancel all remaining futures
                        for f in futures:
                            f.cancel()
                        break
                    
                    # Wait for some futures to complete
                    done, not_done = concurrent.futures.wait(
                        futures, 
                        timeout=1.0,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    
                    # Process completed futures
                    for future in done:
                        try:
                            future.result(timeout=0.1)
                        except Exception:
                            pass
                    
                    # Remove completed futures from list
                    futures = list(not_done)
                    
                    # If all done, break
                    if not futures:
                        break
                
                # Cancel any remaining futures after timeout
                for future in futures:
                    future.cancel()
                    
            except Exception as e:
                # Clean up on error
                for future in futures:
                    future.cancel()
        
        # Return best server found
        if not results:
            return None
            
        return min(results.keys(), key=lambda s: results[s]['ping'])
    
    def find_best_server_simple(self, servers: List[Server], max_workers: int = 8) -> Optional[Server]:
        """
        Simple and reliable version for CLI usage
        
        Args:
            servers: List of servers to test
            max_workers: Maximum number of concurrent threads
            
        Returns:
            Server with lowest ping, or None
        """
        if not servers:
            return None
            
        results = {}
        completed_count = 0
        
        # Create progress bar for server testing
        progress_bar = show_progress_bar(width=30)
        progress_bar.update(0, f"Testing {len(servers)} servers...")
        
        def ping_single_server(server: Server) -> Tuple[Server, float]:
            """Ping a single server and return result"""
            nonlocal completed_count
            try:
                ping, _ = self.ping(server, count=1)
                completed_count += 1
                progress = completed_count / len(servers)
                progress_bar.update(progress, f"Tested {completed_count}/{len(servers)} servers")
                return server, ping if ping > 0 else float('inf')
            except Exception:
                completed_count += 1
                progress = completed_count / len(servers)
                progress_bar.update(progress, f"Tested {completed_count}/{len(servers)} servers")
                return server, float('inf')
        
        # Use ThreadPoolExecutor with simple approach
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_server = {
                executor.submit(ping_single_server, server): server 
                for server in servers
            }
            
            # Collect results with timeout
            for future in future_to_server:
                try:
                    server, ping = future.result(timeout=10)  # 10 second timeout per server
                    if ping < float('inf'):
                        results[server] = ping
                except Exception:
                    pass  # Skip failed servers
        
        # Clear progress bar completely
        progress_bar.finish()
        
        # Return best server
        if not results:
            print("❌ No servers responded")
            return None
            
        best_server = min(results.keys(), key=lambda s: results[s])
        best_ping = results[best_server]
        print(f"✅ Best server: {best_server.name} - {best_ping:.0f}ms")
        return best_server
