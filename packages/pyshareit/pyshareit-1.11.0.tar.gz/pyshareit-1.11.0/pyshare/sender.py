# pyshare/sender.py

import os
import shutil
import socket
import tempfile
import threading
import time
from tqdm import tqdm

from . import config
from .network_utils import send_json, recv_json
from .utils import print_info, print_error, print_success

class Sender:
    def __init__(self):
        self.receivers = {}
        self.stop_discovery = threading.Event()
        self.receivers_lock = threading.Lock()

    def _listen_for_responses(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', config.DISCOVERY_PORT + 1))
            sock.settimeout(0.5)

            broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            while not self.stop_discovery.is_set():
                try:
                    broadcast_sock.sendto(config.DISCOVERY_MAGIC, (config.BROADCAST_ADDRESS, config.DISCOVERY_PORT))
                except Exception:
                    pass

                try:
                    data, addr = sock.recvfrom(1024)
                    if data == config.RESPONSE_MAGIC:
                        with self.receivers_lock:
                            if addr[0] not in [r['ip'] for r in self.receivers.values()]:
                                try:
                                    hostname = socket.gethostbyaddr(addr[0])[0]
                                except socket.herror:
                                    hostname = "Unknown"
                                receiver_id = len(self.receivers) + 1
                                self.receivers[receiver_id] = {'ip': addr[0], 'hostname': hostname}
                                print_success(f"Found Receiver #{receiver_id}: {hostname} ({addr[0]})")
                except socket.timeout:
                    continue

            broadcast_sock.close()

    def discover_devices(self):
        print_info("Searching for receivers... Press Enter when you see your device.")
        discover_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        discover_thread.start()
        input()
        self.stop_discovery.set()
        return self.receivers

    def _prepare_path(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        if os.path.isdir(path):
            print_info(f"Archiving folder: {os.path.basename(path)}...")
            temp_dir = tempfile.mkdtemp()
            zip_path_base = os.path.join(temp_dir, os.path.basename(path))
            zip_path = shutil.make_archive(zip_path_base, 'zip', path)
            return zip_path, f"{os.path.basename(path)}.zip", True
        return path, os.path.basename(path), False

    def start_transfer(self, target_info, transfer_request):
        transfer_thread = threading.Thread(
            target=self._transfer_to_target,
            args=(target_info, transfer_request),
            daemon=True
        )
        transfer_thread.start()

    def _transfer_to_target(self, target, request):
        ip, hostname = target['ip'], target['hostname']
        print_info(f"Initiating transfer to {hostname}...")
        temp_zip_path = None
        is_temp = False

        try:
            metadata = {'type': request['type']}
            if request['type'] == 'path':
                temp_zip_path, filename, is_temp = self._prepare_path(request['content'])
                metadata.update({
                    'filename': filename,
                    'filesize': os.path.getsize(temp_zip_path)
                })
            else:
                metadata.update({
                    'filename': '__pyshare_text_snippet__',
                    'content': request['content']
                })
            
            # Add sender's hostname to metadata for the new handshake
            metadata['sender_hostname'] = socket.gethostname()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(30)
                s.connect((ip, config.TCP_PORT))
                
                # Send initial metadata including sender's name
                send_json(s, {'action': 'request_transfer', 'metadata': metadata})
                
                # Wait for the receiver to accept the connection
                print_info("Waiting for receiver to accept the connection...")
                confirmation = recv_json(s)
                
                if not confirmation or confirmation.get('status') != 'ok_to_send':
                    print_error(f"Receiver {hostname} rejected the connection.")
                    return

                print_success("Connection accepted! Starting transfer...")

                if metadata['type'] == 'path':
                    filesize = metadata['filesize']
                    with open(temp_zip_path, 'rb') as f, tqdm(
                        total=filesize,
                        desc="Sending",
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024
                    ) as pbar:
                        while True:
                            chunk = f.read(config.BUFFER_SIZE)
                            if not chunk:
                                break
                            s.sendall(chunk)
                            pbar.update(len(chunk))
                    print_success(f"'{metadata['filename']}' sent to {hostname}!")

        except FileNotFoundError as e:
            print_error(str(e))
        except (socket.timeout, ConnectionResetError) as e:
            print_error(f"Connection error: {e}")
        except Exception as e:
            print_error(f"An unexpected error occurred: {e}")
        finally:
            if temp_zip_path and is_temp:
                shutil.rmtree(os.path.dirname(temp_zip_path))