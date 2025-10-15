#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example: Testing with internetspeedtest.net
This example shows how to use internetspeedtest-cli with internetspeedtest.net servers
"""

from internetspeedtest import SpeedTest

def main():
    print("Testing with internetspeedtest.net")
    print("=" * 50)
    print()
    
    # Initialize SpeedTest with secure connection
    st = SpeedTest(secure=True, timeout=20)
    
    # Option 1: If internetspeedtest.net provides a server list API
    # Replace with actual URL if available
    try:
        print("Attempting to fetch internetspeedtest.net server list...")
        # Example: servers = st.get_servers(server_list_url="https://internetspeedtest.net/api/servers.json")
        # For now, using default LibreSpeed servers
        servers = st.get_servers()
        print(f"Found {len(servers)} servers")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Option 2: Define internetspeedtest.net server manually
    # Replace with actual internetspeedtest.net server details
    from internetspeedtest import Server
    
    # Example server configuration (replace with actual values)
    internetspeedtest_server = Server({
        "id": 1,
        "name": "InternetSpeedTest.net Server",
        "server": "https://internetspeedtest.net/",  # Replace with actual URL
        "dlURL": "garbage.php",
        "ulURL": "empty.php",
        "pingURL": "empty.php",
        "getIpURL": "getIP.php"
    })
    
    # Use the manual server or find best from list
    test_server = internetspeedtest_server
    
    print(f"Using server: {test_server.name}")
    print(f"URL: {test_server.server}")
    print()
    
    # Get IP information
    print("Getting your IP information...")
    ip_info = st.get_ip_info(test_server)
    if 'ip' in ip_info:
        print(f"Your IP: {ip_info['ip']}")
    print()
    
    # Run speed test
    print("Testing ping...")
    ping, jitter = st.ping(test_server, count=10)
    print(f"Ping: {ping:.2f} ms")
    print(f"Jitter: {jitter:.2f} ms")
    print()
    
    print("Testing download speed (15 seconds)...")
    download_speed, download_bytes = st.download(
        test_server,
        duration=15,
        concurrent=3
    )
    print(f"Download: {download_speed:.2f} Mbps ({download_bytes / (1024*1024):.2f} MB)")
    print()
    
    print("Testing upload speed (15 seconds)...")
    upload_speed, upload_bytes = st.upload(
        test_server,
        duration=15,
        concurrent=3
    )
    print(f"Upload: {upload_speed:.2f} Mbps ({upload_bytes / (1024*1024):.2f} MB)")
    print()
    
    # Display summary
    print("=" * 50)
    print("InternetSpeedTest.net Results:")
    print(f"  Ping: {ping:.2f} ms")
    print(f"  Jitter: {jitter:.2f} ms")
    print(f"  Download: {download_speed:.2f} Mbps")
    print(f"  Upload: {upload_speed:.2f} Mbps")
    print()
    print("Note: Update the server URL in this example with")
    print("      the actual internetspeedtest.net server endpoint.")

if __name__ == '__main__':
    main()
