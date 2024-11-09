import socket
import threading
import logging
from collections import defaultdict
from typing import Dict, Any

class UDPHandler:
    def __init__(self, proxy_host: str, proxy_port: int, 
                 target_host: str, target_port: int):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port + 1  # UDP uses next port
        self.target_host = target_host
        self.target_port = target_port
        self.clients: Dict[Any, dict] = defaultdict(dict)

    def handle_response(self, client_addr: tuple, target_socket: socket.socket, 
                       udp_socket: socket.socket, log_data: bool) -> None:
        try:
            response, _ = target_socket.recvfrom(4096)
            udp_socket.sendto(response, client_addr)
            if log_data:
                logging.debug(f"UDP Response: {self.target_host}:{self.target_port} -> {client_addr}")
        except Exception as e:
            logging.error(f"UDP Response Error: {str(e)}")
        finally:
            target_socket.close()

    def start(self, log_data: bool) -> None:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((self.proxy_host, self.proxy_port))
        
        logging.info(f"UDP proxy listening on {self.proxy_host}:{self.proxy_port}")
        
        while True:
            try:
                data, client_addr = udp_socket.recvfrom(4096)
                if log_data:
                    logging.debug(f"UDP: {client_addr} -> {self.target_host}:{self.target_port}")
                    logging.debug(f"Data: {data[:1024]!r}...")

                target_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                target_socket.sendto(data, (self.target_host, self.target_port))
                
                threading.Thread(
                    target=self.handle_response,
                    args=(client_addr, target_socket, udp_socket, log_data)
                ).start()
                
            except Exception as e:
                logging.error(f"UDP Error: {str(e)}")