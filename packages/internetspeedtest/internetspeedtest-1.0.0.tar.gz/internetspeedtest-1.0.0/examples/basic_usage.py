#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example usage of internetspeedtest Python library
"""

from internetspeedtest import SpeedTest

def main():
    # Initialize SpeedTest
    print("InternetSpeedTest Python CLI Example")
    print("=" * 50)
    print()
    
    st = SpeedTest(secure=True)  # Use HTTPS
    
    # Get available servers
    print("Fetching server list...")
    servers = st.get_servers()
    print(f"Found {len(servers)} servers")
    print()
    
    # Find best server
    print("Finding best server based on ping...")
    best_server = st.find_best_server(servers)
    
    if not best_server:
        print("Unable to find suitable server")
        return
    
    print(f"Selected server: {best_server.name}")
    if best_server.sponsor_name:
        print(f"Sponsor: {best_server.sponsor_name}")
    print(f"URL: {best_server.server}")
    print()
    
    # Get IP information
    print("Getting IP information...")
    ip_info = st.get_ip_info(best_server)
    if 'ip' in ip_info:
        print(f"Your IP: {ip_info['ip']}")
    print()
    
    # Test ping and jitter
    print("Testing ping and jitter...")
    ping, jitter = st.ping(best_server, count=10)
    print(f"Ping: {ping:.2f} ms")
    print(f"Jitter: {jitter:.2f} ms")
    print()
    
    # Test download speed
    print("Testing download speed (this may take a while)...")
    download_speed, bytes_downloaded = st.download(
        best_server,
        duration=15,
        concurrent=3,
        chunks=100
    )
    print(f"Download speed: {download_speed:.2f} Mbps")
    print(f"Downloaded: {bytes_downloaded / (1024*1024):.2f} MB")
    print()
    
    # Test upload speed
    print("Testing upload speed (this may take a while)...")
    upload_speed, bytes_uploaded = st.upload(
        best_server,
        duration=15,
        concurrent=3,
        upload_size=1024
    )
    print(f"Upload speed: {upload_speed:.2f} Mbps")
    print(f"Uploaded: {bytes_uploaded / (1024*1024):.2f} MB")
    print()
    
    print("=" * 50)
    print("Speed Test Summary:")
    print(f"  Server: {best_server.name}")
    print(f"  Ping: {ping:.2f} ms")
    print(f"  Jitter: {jitter:.2f} ms")
    print(f"  Download: {download_speed:.2f} Mbps")
    print(f"  Upload: {upload_speed:.2f} Mbps")

if __name__ == '__main__':
    main()
