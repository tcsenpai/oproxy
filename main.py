import socket
import threading
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import argparse
from collections import defaultdict

# Load environment variables
load_dotenv()

# Configuration
PROXY_HOST = '0.0.0.0'  # Listen on all interfaces
PROXY_PORT = int(os.getenv('PROXY_PORT', 8080))
TARGET_HOST = os.getenv('TARGET_HOST', 'localhost')
TARGET_PORT = int(os.getenv('TARGET_PORT', 80))

def setup_logging(log_file=None, log_level=logging.INFO):
    # Configure logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Setup basic configuration
    if log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # This will also print to stdout
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )

def parse_args():
    parser = argparse.ArgumentParser(description='Transparent TCP/UDP Proxy with logging capabilities')
    parser.add_argument('--log-file', type=str, help='Path to the log file')
    parser.add_argument('--log-data', action='store_true', help='Enable logging of data content')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       default='INFO',
                       help='Set the logging level')
    parser.add_argument('--enable-udp', action='store_true', help='Enable UDP proxy alongside TCP')
    return parser.parse_args()

def handle_tcp_client(client_socket, log_data=False):
    client_address = client_socket.getpeername()
    logging.info(f"New connection from {client_address[0]}:{client_address[1]}")
    
    # Connect to target server
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((TARGET_HOST, TARGET_PORT))
    logging.info(f"Connected to target {TARGET_HOST}:{TARGET_PORT}")

    def forward(source, destination, direction):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                if log_data:
                    print("[INFO] Logging data is enabled")
                    src = source.getpeername()
                    dst = destination.getpeername()
                    timestamp = datetime.now().isoformat()
                    logging.debug(f"[{direction}] {src[0]}:{src[1]} -> {dst[0]}:{dst[1]}")
                    logging.debug(f"Data: {data[:1024]!r}...")  # Log first 1KB of data
                destination.send(data)
        except Exception as e:
            logging.error(f"Error in {direction}: {str(e)}")
        finally:
            source.close()
            destination.close()
            logging.info(f"Connection closed ({direction})")

    # Create two threads for bidirectional communication
    client_to_target = threading.Thread(
        target=forward, 
        args=(client_socket, target_socket, "CLIENT->TARGET")
    )
    target_to_client = threading.Thread(
        target=forward, 
        args=(target_socket, client_socket, "TARGET->CLIENT")
    )

    client_to_target.start()
    target_to_client.start()

def handle_udp_proxy(log_data=False):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((PROXY_HOST, PROXY_PORT + 1))  # Use next port for UDP
    
    clients = defaultdict(dict)
    
    logging.info(f"UDP proxy listening on {PROXY_HOST}:{PROXY_PORT + 1}")
    
    while True:
        try:
            data, client_addr = udp_socket.recvfrom(4096)
            if log_data:
                logging.debug(f"UDP: {client_addr} -> {TARGET_HOST}:{TARGET_PORT}")
                logging.debug(f"Data: {data[:1024]!r}...")

            # Forward to target
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            target_socket.sendto(data, (TARGET_HOST, TARGET_PORT))
            
            # Store socket for this client
            clients[client_addr]['socket'] = target_socket
            clients[client_addr]['target'] = (TARGET_HOST, TARGET_PORT)
            
            # Handle response in a separate thread to not block
            def handle_response(client_addr, target_socket):
                try:
                    response, _ = target_socket.recvfrom(4096)
                    udp_socket.sendto(response, client_addr)
                    if log_data:
                        logging.debug(f"UDP Response: {TARGET_HOST}:{TARGET_PORT} -> {client_addr}")
                except Exception as e:
                    logging.error(f"UDP Response Error: {str(e)}")
                finally:
                    target_socket.close()
                    
            threading.Thread(target=handle_response, 
                           args=(client_addr, target_socket)).start()
            
        except Exception as e:
            logging.error(f"UDP Error: {str(e)}")

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(args.log_file, log_level)
    
    # Start TCP proxy (main functionality)
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((PROXY_HOST, PROXY_PORT))
    tcp_server.listen(100)

    logging.info(f"TCP proxy listening on {PROXY_HOST}:{PROXY_PORT}")
    logging.info(f"Forwarding to {TARGET_HOST}:{TARGET_PORT}")
    logging.info(f"Logging level: {args.log_level}")
    if args.log_file:
        logging.info(f"Logging to file: {args.log_file}")
    if args.log_data:
        logging.info("Data logging is enabled")

    # Start UDP proxy if enabled
    if args.enable_udp:
        udp_thread = threading.Thread(target=handle_udp_proxy, 
                                    args=(args.log_data,),
                                    daemon=True)
        udp_thread.start()
        logging.info("UDP proxy enabled")

    # Main TCP loop
    while True:
        client_socket, addr = tcp_server.accept()
        proxy_thread = threading.Thread(
            target=handle_tcp_client,
            args=(client_socket, args.log_data)
        )
        proxy_thread.start()

if __name__ == "__main__":
    main()