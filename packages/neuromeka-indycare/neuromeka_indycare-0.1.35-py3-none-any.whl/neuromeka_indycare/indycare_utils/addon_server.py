"""
TCP/IP server for receiving data from IndyCAREReport addons
"""
import socket
import threading
import json
import time
import logging
from queue import Queue, Empty

class AddonServer:
    """
    A TCP/IP server addon clients for IndyCAREReport
    """
    def __init__(self, addon_data_queue, config):
        """
        Initialize the addon server
        Args:
            addon_data_queue: Queue for sending data to IndyCAREReport
            config: Configuration dictionary for the addon server
        """
        # Setup logger
        self.logger = logging.getLogger("AddonServer_log")
        
        # Server configuration from config file
        self._config = config
        self._host = self._config.get("host", "0.0.0.0")  # Default to all interfaces
        self._port = self._config.get("port", 8765)  # Default port
        self._max_connections = self._config.get("max_connections", 5)
        self._timeout = self._config.get("timeout", 10)
        
        # Data queue for communication with IndyCAREReport
        self._addon_data_queue = addon_data_queue
        
        # Server state
        self._thread = None
        self._stop_requested = False
        self._clients = []
        self._clients_lock = threading.Lock()
        self._server_socket = None

    def _handle_client(self, client_socket, addr):
        """Handle a client connection"""
        self.logger.info(f"Client connected: {addr}")
        client_socket.settimeout(self._timeout)
        
        try:
            while not self._stop_requested:
                try:
                    # Receive data from client
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    # Parse the data
                    try:
                        json_data = json.loads(data.decode('utf-8'))
                        
                        # Put data into the queue
                        self._addon_data_queue.put(json_data)
                        self.logger.debug(f"Received addon data: {json_data}")
                        
                        # Send acknowledgement
                        response = {"status": "ok", "timestamp": time.time()}
                        client_socket.sendall(json.dumps(response).encode('utf-8'))
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON data received: {e}")
                        # Send error response
                        error_response = {"status": "error", "message": "Invalid JSON format"}
                        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
                    except Exception as e:
                        self.logger.error(f"Error processing addon data: {e}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._stop_requested:
                        self.logger.error(f"Error with client connection: {e}")
                    break
        finally:
            with self._clients_lock:
                if client_socket in self._clients:
                    self._clients.remove(client_socket)
            client_socket.close()
            self.logger.info(f"Client disconnected: {addr}")

    def _server_loop(self):
        """Main server loop that accepts client connections"""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self._server_socket.bind((self._host, self._port))
            self._server_socket.listen(self._max_connections)
            self._server_socket.settimeout(1.0)
            self.logger.info(f"Addon server listening on {self._host}:{self._port}")
            
            while not self._stop_requested:
                try:
                    client_sock, client_addr = self._server_socket.accept()
                    with self._clients_lock:
                        self._clients.append(client_sock)
                    
                    # Start thread to handle client connection
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_sock, client_addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._stop_requested:
                        self.logger.error(f"Error accepting client connection: {e}")
                        time.sleep(1)
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            if self._server_socket:
                self._server_socket.close()
                self._server_socket = None
            self.logger.info("Addon server stopped")
    
    def start(self):
        """Start the addon server"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_requested = False
            self._thread = threading.Thread(target=self._server_loop, daemon=True)
            self._thread.start()
            self.logger.info("Addon server started")
    
    def stop(self):
        """Stop the addon server"""
        self._stop_requested = True
        
        # Close all client connections
        with self._clients_lock:
            for client in self._clients:
                try:
                    client.close()
                except Exception:
                    pass
            self._clients.clear()
        
        # Close server socket
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            
        # Wait for the server thread to terminate
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                self.logger.warning("Addon server thread did not terminate gracefully")
            else:
                self.logger.info("Addon server stopped successfully")
    
    def is_running(self):
        """Check if the server is running"""
        return self._thread is not None and self._thread.is_alive()
    