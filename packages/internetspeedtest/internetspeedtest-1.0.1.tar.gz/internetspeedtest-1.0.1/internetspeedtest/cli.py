#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
InternetSpeedTest CLI - Command line interface
"""

import sys
import json
import argparse
from typing import Optional
from .speedtest import SpeedTest, Server
from .progress import create_multi_stage, show_spinner


def format_speed(speed_mbps: float, use_bytes: bool = False) -> str:
    """Format speed for display"""
    if use_bytes:
        speed_MBps = speed_mbps / 8
        return f"{speed_MBps:.2f} MB/s"
    return f"{speed_mbps:.2f} Mbps"


def format_data_size(bytes_count: int) -> str:
    """Format data size for display"""
    if bytes_count >= 1024**3:  # GB
        return f"{bytes_count/(1024**3):.2f} GB"
    elif bytes_count >= 1024**2:  # MB
        return f"{bytes_count/(1024**2):.1f} MB"
    elif bytes_count >= 1024:  # KB
        return f"{bytes_count/1024:.1f} KB"
    else:
        return f"{bytes_count} B"


def clear_progress_line():
    """Clear any remaining progress line"""
    sys.stdout.write('\r' + ' ' * 100 + '\r')
    sys.stdout.flush()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Test your Internet speed with InternetSpeedTest',
        prog='internetspeedtest-py'
    )
    
    # Basic options
    parser.add_argument('--version', action='store_true',
                        help='Show version and exit')
    parser.add_argument('--list', action='store_true',
                        help='Display a list of LibreSpeed servers')
    parser.add_argument('--server', type=int, action='append',
                        help='Specify server ID to test against (can be used multiple times)')
    parser.add_argument('--exclude', type=int, action='append',
                        help='Exclude server from selection (can be used multiple times)')
    parser.add_argument('--server-json', type=str,
                        help='Use alternative server list from remote JSON URL')
    parser.add_argument('--local-json', type=str,
                        help='Use alternative server list from local JSON file')
    
    # Test options
    parser.add_argument('--no-download', action='store_true',
                        help='Do not perform download test')
    parser.add_argument('--no-upload', action='store_true',
                        help='Do not perform upload test')
    parser.add_argument('--concurrent', type=int, default=3,
                        help='Number of concurrent HTTP connections (default: 3)')
    parser.add_argument('--chunks', type=int, default=100,
                        help='Number of chunks for download test (default: 100)')
    parser.add_argument('--upload-size', type=int, default=1024,
                        help='Size of upload payload in KiB (default: 1024)')
    parser.add_argument('--duration', type=int, default=15,
                        help='Test duration in seconds (default: 15)')
    
    # Network options
    parser.add_argument('--source', type=str,
                        help='Source IP address to bind to')
    parser.add_argument('--timeout', type=int, default=15,
                        help='HTTP timeout in seconds (default: 15)')
    parser.add_argument('--secure', action='store_true',
                        help='Use HTTPS instead of HTTP')
    
    # Output options
    parser.add_argument('--simple', action='store_true',
                        help='Suppress verbose output, show basic information only')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='Output results in JSON format')
    parser.add_argument('--csv', action='store_true',
                        help='Output results in CSV format')
    parser.add_argument('--bytes', action='store_true',
                        help='Display values in bytes instead of bits')
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        from . import __version__
        print(f"internetspeedtest-py {__version__}")
        return 0
    
    # Initialize SpeedTest
    try:
        speedtest = SpeedTest(
            source=args.source,
            timeout=args.timeout,
            secure=args.secure
        )
    except Exception as e:
        print(f"Error initializing SpeedTest: {e}", file=sys.stderr)
        return 1
    
    # Get servers
    try:
        if args.local_json:
            with open(args.local_json, 'r') as f:
                servers_data = json.load(f)
            servers = [Server(s) for s in servers_data]
        else:
            server_list_url = args.server_json
            servers = speedtest.get_servers(
                server_list_url=server_list_url,
                exclude=args.exclude,
                specific=args.server
            )
    except Exception as e:
        print(f"Error fetching servers: {e}", file=sys.stderr)
        return 1
    
    if not servers:
        print("No servers available", file=sys.stderr)
        return 1
    
    # List servers
    if args.list:
        print("\nAvailable servers:")
        print("-" * 80)
        for server in servers:
            sponsor = f" ({server.sponsor_name})" if server.sponsor_name else ""
            print(f"[{server.id:4d}] {server.name}{sponsor}")
            print(f"       {server.server}")
        return 0
    
    # Determine if we should show progress (only for interactive mode)
    show_progress = not args.simple and not args.json_output and not args.csv
    
    # Find best server
    if show_progress:
        print("🔍 Finding best server...")
        
    if args.server and len(args.server) == 1:
        # Use specified server
        test_server = servers[0]
    else:
        # Find best server using simple method for better reliability
        test_server = speedtest.find_best_server_simple(servers, max_workers=6)
        
    if not test_server:
        print("❌ Unable to find suitable server", file=sys.stderr)
        return 1
    
    # Get IP info
    ip_info = speedtest.get_ip_info(test_server)
    
    # Perform ping test (quick, no separate progress needed)
    ping, jitter = speedtest.ping(test_server, count=10)
    
    if show_progress:
        print(f"📍 Server: {test_server.name}")
        print(f"🏓 Ping: {ping:.2f} ms | Jitter: {jitter:.2f} ms")
    
    # Perform download test
    download_speed = 0.0
    download_bytes = 0
    
    if not args.no_download:
        if show_progress:
            print("\n⬇️ Starting download test...")
        
        download_speed, download_bytes = speedtest.download(
            test_server,
            duration=args.duration,
            concurrent=args.concurrent,
            chunks=args.chunks
        )
        
        if show_progress:
            # Clear current progress line before showing completion message
            clear_progress_line()
            print(f"✅ Download completed: {format_speed(download_speed, args.bytes)}")
    
    # Perform upload test
    upload_speed = 0.0
    upload_bytes = 0
    
    if not args.no_upload:
        if show_progress:
            print("\n⬆️ Starting upload test...")
        
        upload_speed, upload_bytes = speedtest.upload(
            test_server,
            duration=args.duration,
            concurrent=args.concurrent,
            upload_size=args.upload_size
        )
        
        if show_progress:
            # Clear current progress line before showing completion message
            clear_progress_line()
            print(f"✅ Upload completed: {format_speed(upload_speed, args.bytes)}")
    
    # Show results summary
    if show_progress:
        clear_progress_line()  # Clear any remaining progress
        print("\n🎉 Speed test completed!")
        
        # Display final results summary
        print("\n" + "="*50)
        print("📊 SPEED TEST RESULTS")
        print("="*50)
        
        # Server info
        sponsor = f" ({test_server.sponsor_name})" if test_server.sponsor_name else ""
        print(f"🌐 Server: {test_server.name}{sponsor}")
        print(f"🔗 URL: {test_server.server}")
        
        # Network info
        if ip_info.get('ip'):
            print(f"🏠 Your IP: {ip_info['ip']}")
        
        print(f"🏓 Ping: {ping:.2f} ms")
        print(f"📊 Jitter: {jitter:.2f} ms")
        
        # Speed results
        if not args.no_download:
            download_formatted = format_speed(download_speed, args.bytes)
            data_downloaded = format_data_size(download_bytes) if download_bytes > 0 else "N/A"
            print(f"⬇️  Download: {download_formatted} (Data: {data_downloaded})")
        
        if not args.no_upload:
            upload_formatted = format_speed(upload_speed, args.bytes)
            data_uploaded = format_data_size(upload_bytes) if upload_bytes > 0 else "N/A"
            print(f"⬆️  Upload: {upload_formatted} (Data: {data_uploaded})")
        
        print("="*50)
    
    # Output results
    if args.json_output:
        result = {
            'server': {
                'id': test_server.id,
                'name': test_server.name,
                'url': test_server.server,
                'sponsor': test_server.sponsor_name
            },
            'ping': ping,
            'jitter': jitter,
            'download': download_speed * 1_000_000,  # Convert to bps
            'upload': upload_speed * 1_000_000,  # Convert to bps
            'bytes_received': download_bytes,
            'bytes_sent': upload_bytes,
            'ip': ip_info.get('ip', '')
        }
        print(json.dumps(result, indent=2))
    elif args.csv:
        # CSV header
        print("Server,Sponsor,Ping (ms),Jitter (ms),Download (bps),Upload (bps),IP")
        # CSV data
        print(f'"{test_server.name}","{test_server.sponsor_name}",{ping},{jitter},'
              f'{download_speed * 1_000_000},{upload_speed * 1_000_000},'
              f'"{ip_info.get("ip", "")}"')
    elif args.simple:
        print(f"Ping: {ping:.2f} ms\tJitter: {jitter:.2f} ms")
        print(f"Download: {format_speed(download_speed, args.bytes)}")
        print(f"Upload: {format_speed(upload_speed, args.bytes)}")
    else:
        # Full output already printed above
        print("Test completed!")
        print("Powered by https://internetspeedtest.net")
    return 0


if __name__ == '__main__':
    sys.exit(main())
