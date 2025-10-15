"""
InternetSpeedTest Python CLI
A Python library and CLI for testing Internet speed using LibreSpeed backend servers.
"""

__version__ = "1.0.1"
__author__ = "LibreSpeed"
__license__ = "LGPL-3.0"

from .speedtest import SpeedTest, Server

__all__ = ["SpeedTest", "Server"]
