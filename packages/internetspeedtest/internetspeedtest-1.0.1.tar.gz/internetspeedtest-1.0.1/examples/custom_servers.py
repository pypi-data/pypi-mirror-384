#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example: Using custom server list (e.g., internetspeedtest.net)
"""

from internetspeedtest import SpeedTest, Server

def main():
    print("InternetSpeedTest with Custom Server Example")
    print("=" * 50)
    print()
    
    # Option 1: Use a custom server list URL
    st = SpeedTest(secure=True)
    
    # For internetspeedtest.net or other custom server lists
    custom_server_url = "https://internetspeedtest.net/servers.json"
    
    try:
        servers = st.get_servers(server_list_url=custom_server_url)
        print(f"Loaded {len(servers)} servers from custom list")
    except Exception as e:
        print(f"Error loading custom server list: {e}")
        print("Using default server list instead...")
        servers = st.get_servers()
    
    # Option 2: Define custom servers manually
    custom_servers = [
        {
            "id": 1,
            "name": "Custom Server 1",
            "server": "https://speedtest.example.com/",
            "dlURL": "garbage.php",
            "ulURL": "empty.php",
            "pingURL": "empty.php",
            "getIpURL": "getIP.php"
        }
    ]
    
    # Convert to Server objects
    manual_servers = [Server(s) for s in custom_servers]
    
    # Use whichever server list you prefer
    test_servers = servers if servers else manual_servers
    
    if not test_servers:
        print("No servers available")
        return
    
    # Find best server
    print("Finding best server...")
    best_server = st.find_best_server(test_servers)
    
    if not best_server:
        print("Unable to find suitable server")
        return
    
    print(f"Using server: {best_server.name}")
    print(f"URL: {best_server.server}")
    print()
    
    # Run speed test
    print("Running speed test...")
    ping, jitter = st.ping(best_server)
    print(f"Ping: {ping:.2f} ms, Jitter: {jitter:.2f} ms")
    
    download_speed, _ = st.download(best_server, duration=10)
    print(f"Download: {download_speed:.2f} Mbps")
    
    upload_speed, _ = st.upload(best_server, duration=10)
    print(f"Upload: {upload_speed:.2f} Mbps")

if __name__ == '__main__':
    main()
