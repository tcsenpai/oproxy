import os
import argparse
from dotenv import load_dotenv
import socket
import threading
import logging

from proxy.logger import setup_logging
from proxy.tcp_handler import TCPHandler
from proxy.udp_handler import UDPHandler

def parse_args():
    parser = argparse.ArgumentParser(description='Transparent TCP/UDP Proxy with logging capabilities')
    parser.add_argument('--log-file', type=str, help='Path to the log file')
    parser.add_argument('--log-data', action='store_true', help='Enable logging of data content')
    parser.add_argument('--full-debug', action='store_true', help='Enable full data logging (entire payload)')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       default='INFO',
                       help='Set the logging level')
    parser.add_argument('--enable-udp', action='store_true', help='Enable UDP proxy alongside TCP')
    return parser.parse_args()

def main():
    # Load configuration
    load_dotenv()
    PROXY_HOST = '0.0.0.0'
    PROXY_PORT = int(os.getenv('PROXY_PORT', 8080))
    TARGET_HOST = os.getenv('TARGET_HOST', 'localhost')
    TARGET_PORT = int(os.getenv('TARGET_PORT', 80))

    # Parse arguments and setup logging
    args = parse_args()
    setup_logging(args.log_file, getattr(logging, args.log_level))

    # Initialize TCP handler
    tcp_handler = TCPHandler(TARGET_HOST, TARGET_PORT)
    
    # Setup TCP server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((PROXY_HOST, PROXY_PORT))
    tcp_server.listen(100)

    logging.info(f"TCP proxy listening on {PROXY_HOST}:{PROXY_PORT}")
    logging.info(f"Forwarding to {TARGET_HOST}:{TARGET_PORT}")

    # Start UDP handler if enabled
    if args.enable_udp:
        udp_handler = UDPHandler(PROXY_HOST, PROXY_PORT, TARGET_HOST, TARGET_PORT)
        udp_thread = threading.Thread(
            target=udp_handler.start,
            args=(args.log_data,),
            daemon=True
        )
        udp_thread.start()
        logging.info("UDP proxy enabled")

    # Main TCP loop
    while True:
        client_socket, addr = tcp_server.accept()
        proxy_thread = threading.Thread(
            target=tcp_handler.handle_client,
            args=(client_socket, args.log_data, args.full_debug)
        )
        proxy_thread.start()

if __name__ == "__main__":
    main()