# pyshare/receiver.py

import os
import socket
import threading
import zipfile
from datetime import datetime
import pyperclip
from tqdm import tqdm

from . import config
from .network_utils import send_json, recv_json
from .utils import print_info, print_error, print_success

class Receiver:
    # --- THIS IS THE MISSING CONSTRUCTOR ---
    def __init__(self):
        self.stop_event = threading.Event()
        self.threads = []
        self.transfer_history = []
    # -----------------------------------------

    def _discovery_responder(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', config.DISCOVERY_PORT))
            sock.settimeout(1)
            while not self.stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == config.DISCOVERY_MAGIC:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as response_sock:
                            response_sock.sendto(config.RESPONSE_MAGIC, (addr[0], config.DISCOVERY_PORT + 1))
                except socket.timeout:
                    continue

    def _handle_client(self, conn, addr):
        try:
            initial_request = recv_json(conn)
            if not initial_request or initial_request.get('action') != 'request_transfer':
                return

            metadata = initial_request['metadata']
            sender_hostname = metadata.get('sender_hostname', addr[0])

            print_info(f"Connection request from {sender_hostname}.")
            accept_conn = input("Accept connection? (y/n): ").lower()
            if accept_conn != 'y':
                send_json(conn, {'status': 'rejected'})
                conn.close()
                return
            
            send_json(conn, {'status': 'ok_to_send'})

            if metadata['filename'] == '__pyshare_text_snippet__':
                print_success(f"Text snippet from {sender_hostname}:")
                print(metadata['content'])
                pyperclip.copy(metadata['content'])
                print_info("Copied to clipboard!")
                return

            fname, fsize = os.path.basename(metadata['filename']), metadata['filesize']
            print_info(f"Incoming file from {sender_hostname}: {fname} ({fsize / (1024*1024):.2f} MB)")
            
            output_path = fname
            
            with open(output_path, 'wb') as f, tqdm(
                total=fsize,
                desc="Receiving",
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as pbar:
                received_bytes = 0
                while received_bytes < fsize:
                    chunk = conn.recv(config.BUFFER_SIZE)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    received_bytes += len(chunk)
                    pbar.update(len(chunk))

            if os.path.getsize(output_path) == fsize:
                print_success(f"'{fname}' received successfully!")
                self.transfer_history.append(f"{fname} from {sender_hostname}")
                if fname.lower().endswith('.zip'):
                    with zipfile.ZipFile(output_path, 'r') as zip_ref:
                        zip_ref.extractall()
                    os.remove(output_path)
                    print_info(f"Extracted and removed {fname}")
            else:
                print_error(f"File transfer for '{fname}' was incomplete.")
        
        except Exception as e:
            print_error(f"An error occurred: {e}")
        finally:
            conn.close()

    def _file_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('', config.TCP_PORT))
            except OSError:
                print_error(f"Port {config.TCP_PORT} is already in use.")
                self.stop_event.set()
                return
            s.listen()
            s.settimeout(1)
            while not self.stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue

    def start(self):
        self.stop_event.clear()
        self.threads = [
            threading.Thread(target=self._discovery_responder, daemon=True),
            threading.Thread(target=self._file_listener, daemon=True)
        ]
        for t in self.threads:
            t.start()
        print_success("Receiver is active.")

    def stop(self):
        self.stop_event.set()
        print_info("Receiver stopped.")