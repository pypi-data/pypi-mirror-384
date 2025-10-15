import socket
import os
import threading
import json
import time
import shutil
import tempfile
import zipfile
import random
import platform
import sys
import shlex

# --- Import Core Libraries ---
from tqdm import tqdm
from colorama import Fore, Style, init

# --- Import Feature Libraries ---
import pyperclip
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

# --- Initialize Colorama for cross-platform colored text ---
init(autoreset=True)

# --- Configuration ---
DISCOVERY_PORT = 50001
TCP_PORT = 50002
BROADCAST_ADDRESS = '<broadcast>'
DISCOVERY_MAGIC = b"PYSHARE_DISCOVERY_V2" # Version bump for new protocol
RESPONSE_MAGIC = b"PYSHARE_RESPONSE_V2"
BUFFER_SIZE = 4096

# --- UI Helpers ---
def print_info(message): print(f"{Fore.CYAN}{Style.BRIGHT}INFO: {message}{Style.RESET_ALL}")
def print_success(message): print(f"{Fore.GREEN}{Style.BRIGHT}SUCCESS: {message}{Style.RESET_ALL}")
def print_error(message): print(f"{Fore.RED}{Style.BRIGHT}ERROR: {message}{Style.RESET_ALL}")
def print_warn(message): print(f"{Fore.YELLOW}{Style.BRIGHT}WARN: {message}{Style.RESET_ALL}")

# --- Network Protocol Helpers ---
def send_json(sock, data):
    """Sends a JSON object with a 4-byte length prefix."""
    json_data = json.dumps(data).encode('utf-8')
    sock.sendall(len(json_data).to_bytes(4, 'big'))
    sock.sendall(json_data)

def recv_json(sock):
    """Receives a JSON object with a 4-byte length prefix."""
    try:
        data_len = int.from_bytes(sock.recv(4), 'big')
        if not data_len: return None
        return json.loads(sock.recv(data_len))
    except (ConnectionResetError, OSError):
        return None

# --- Sender Logic ---
class Sender:
    def _discover_receivers(self, stop_event):
        # Discovery logic (remains the same)
        pass # Placeholder for brevity, code is unchanged from previous version

    def start_transfer(self, user_input):
        # ... Main transfer logic will be here ...
        pass

# --- Receiver Logic ---
class Receiver:
    # ... Receiver logic will be here ...
    pass

# --- Main Application REPL ---
def show_help():
    print(f"""
{Fore.YELLOW}{Style.BRIGHT}pyshare v3.0 Commands:{Style.RESET_ALL}
  {Style.BRIGHT}send <file_or_folder_path>{Style.RESET_ALL} - Send a file or entire folder.
  {Style.BRIGHT}send --text "your message"{Style.RESET_ALL} - Send a text snippet.
  {Style.BRIGHT}paste{Style.RESET_ALL}                       - Send the contents of your clipboard.
  {Style.BRIGHT}receive{Style.RESET_ALL}                     - Start listening for incoming files (runs in background).
  {Style.BRIGHT}stop{Style.RESET_ALL}                        - Stop the background receiver.
  {Style.BRIGHT}help{Style.RESET_ALL}                        - Show this help message.
  {Style.BRIGHT}exit | quit{Style.RESET_ALL}                 - Exit the pyshare session.
    """)

def main():
    # --- Enable Command History ---
    try:
        if platform.system() != "Windows":
            import readline
        else:
            import pyreadline3 # Should be installed via pyproject.toml
    except ImportError:
        print_warn("Install 'pyreadline3' on Windows for command history.")

    print(f"{Fore.YELLOW}{Style.BRIGHT}{'='*60}\n{'pyshare v3.0 - Secure Interactive File Transfer':^60}\n{'='*60}{Style.RESET_ALL}")
    show_help()
    
    receiver_instance = None
    
    while True:
        try:
            line = input(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}").strip()
            if not line: continue
            
            try:
                parts = shlex.split(line)
            except ValueError:
                print_error("Mismatched quotes in command.")
                continue
            
            command = parts[0].lower()
            args = parts[1:]

            if command == "send":
                if not args:
                    print_error("Usage: send <file_path> OR send --text <message>")
                    continue
                
                # --- Text/Clipboard Sending Logic ---
                if args[0] == '--text':
                    text_to_send = " ".join(args[1:])
                    if not text_to_send:
                        print_error("No text provided after --text flag.")
                        continue
                    Sender().start_transfer({'type': 'text', 'content': text_to_send})
                else:
                    path_to_send = " ".join(args)
                    Sender().start_transfer({'type': 'path', 'content': path_to_send})

            elif command == "paste":
                clipboard_content = pyperclip.paste()
                if not clipboard_content:
                    print_error("Clipboard is empty.")
                    continue
                print_info("Sending clipboard content...")
                Sender().start_transfer({'type': 'text', 'content': clipboard_content})

            elif command == "receive":
                if receiver_instance:
                    print_info("Receiver is already running.")
                else:
                    receiver_instance = Receiver()
                    receiver_instance.start()

            elif command == "stop":
                if receiver_instance:
                    receiver_instance.stop()
                    receiver_instance = None
                else:
                    print_info("Receiver is not currently running.")
            
            elif command == "help":
                show_help()

            elif command in ["exit", "quit"]:
                if receiver_instance: receiver_instance.stop()
                print_info("Exiting pyshare. Goodbye!")
                break
            
            else:
                print_error(f"Unknown command: '{command}'. Type 'help' for commands.")

        except KeyboardInterrupt:
            if receiver_instance: receiver_instance.stop()
            print_info("\nExiting pyshare. Goodbye!")
            break

# --- Replacing Placeholder Classes with Full Implementation ---

# Full Sender class
class Sender:
    def __init__(self):
        self.receivers = {}
        self.stop_discovery = threading.Event()

    def _discover_receivers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1)
            while not self.stop_discovery.is_set():
                sock.sendto(DISCOVERY_MAGIC, (BROADCAST_ADDRESS, DISCOVERY_PORT))
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == RESPONSE_MAGIC and addr[0] not in [r['ip'] for r in self.receivers.values()]:
                        try: hostname = socket.gethostbyaddr(addr[0])[0]
                        except socket.herror: hostname = "Unknown"
                        receiver_id = len(self.receivers) + 1
                        self.receivers[receiver_id] = {'ip': addr[0], 'hostname': hostname}
                        print(f"\r{Fore.MAGENTA}Found Receiver {receiver_id}: {hostname} ({addr[0]})", end="")
                except socket.timeout: pass

    def _prepare_path(self, path):
        """Checks if path is a file or folder. Zips folder and returns path to artifact."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if os.path.isdir(path):
            print_info(f"Archiving folder: {os.path.basename(path)}...")
            temp_dir = tempfile.mkdtemp()
            zip_path_base = os.path.join(temp_dir, os.path.basename(path))
            zip_path = shutil.make_archive(zip_path_base, 'zip', path)
            return zip_path, f"{os.path.basename(path)}.zip", True
        return path, os.path.basename(path), False

    def start_transfer(self, transfer_request):
        # Discovery Phase
        print_info("Searching for receivers... (Press Ctrl+C to stop and select)")
        discover_thread = threading.Thread(target=self._discover_receivers, daemon=True)
        discover_thread.start()
        try:
            while not self.receivers: time.sleep(0.2)
            discover_thread.join()
        except KeyboardInterrupt: print_info("\nStopping discovery.")
        finally: self.stop_discovery.set()
        
        if not self.receivers:
            print_error("No receivers found.")
            return

        print_success("\nAvailable receivers:")
        for r_id, info in self.receivers.items(): print(f"  [{r_id}] {info['hostname']} ({info['ip']})")
        
        choice = input(f"{Fore.YELLOW}PROMPT: Enter receiver ID to send to: {Style.RESET_ALL}")
        try:
            target_info = self.receivers[int(choice)]
        except (ValueError, KeyError):
            print_error("Invalid selection.")
            return

        threading.Thread(target=self._transfer_to_target, args=(target_info, transfer_request), daemon=True).start()
        time.sleep(0.5) # Allow thread to start and print messages

    def _transfer_to_target(self, target, request):
        ip, hostname = target['ip'], target['hostname']
        print_info(f"Initiating transfer to {hostname}...")
        
        temp_zip_path = None
        try:
            # Prepare metadata based on request type
            metadata = {'type': request['type']}
            if request['type'] == 'path':
                temp_zip_path, filename, is_temp = self._prepare_path(request['content'])
                metadata.update({'filename': filename, 'filesize': os.path.getsize(temp_zip_path)})
            else: # text
                metadata.update({'filename': '__pyshare_text_snippet__', 'content': request['content']})

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, TCP_PORT))
                send_json(s, {'action': 'request_transfer', 'metadata': metadata})

                # --- Secure Handshake ---
                handshake_data = recv_json(s)
                if not handshake_data or handshake_data.get('status') != 'ready':
                    print_error(f"Receiver {hostname} rejected transfer or handshake failed.")
                    return

                print_success(f"Receiver is ready. Confirmation PIN: {Fore.RED}{Style.BRIGHT}{handshake_data['pin']}{Style.RESET_ALL}")
                
                fernet_key = Fernet.generate_key()
                pub_key = serialization.load_pem_public_key(handshake_data['public_key'].encode('utf-8'))
                encrypted_fernet_key = pub_key.encrypt(
                    fernet_key,
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
                )
                send_json(s, {'fernet_key': encrypted_fernet_key.hex()})
                
                final_ack = recv_json(s)
                if not final_ack or final_ack.get('status') != 'go':
                    print_error("Failed to complete secure handshake.")
                    return
                
                print_success("Secure connection established. Starting transfer...")
                fernet = Fernet(fernet_key)

                # --- Data Transfer ---
                if metadata['type'] == 'path':
                    filesize = metadata['filesize']
                    resume_from = handshake_data.get('resume_from', 0)
                    if resume_from > 0:
                        print_info(f"Resuming transfer from {resume_from / (1024*1024):.2f} MB...")
                    
                    with open(temp_zip_path, 'rb') as f, tqdm(total=filesize, initial=resume_from, desc=f"Sending to {hostname}", unit='B', unit_scale=True, colour='green') as pbar:
                        f.seek(resume_from)
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk: break
                            encrypted_chunk = fernet.encrypt(chunk)
                            s.sendall(len(encrypted_chunk).to_bytes(4, 'big'))
                            s.sendall(encrypted_chunk)
                            pbar.update(len(chunk))
                    print_success(f"File '{metadata['filename']}' sent to {hostname}.")
        
        except FileNotFoundError as e: print_error(str(e))
        except Exception as e: print_error(f"Transfer failed: {e}")
        finally:
            if temp_zip_path and is_temp: shutil.rmtree(os.path.dirname(temp_zip_path))

# Full Receiver class
class Receiver:
    def __init__(self):
        self.stop_event = threading.Event()
        self.threads = []

    def _discovery_responder(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', DISCOVERY_PORT)); sock.settimeout(1)
            while not self.stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == DISCOVERY_MAGIC: sock.sendto(RESPONSE_MAGIC, addr)
                except socket.timeout: continue

    def _unzip_and_cleanup(self, zip_path):
        """Extracts a zip file and then deletes it."""
        try:
            target_dir = os.path.splitext(zip_path)[0]
            print_info(f"Extracting folder '{os.path.basename(target_dir)}'...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(zip_path))
            os.remove(zip_path)
            print_success(f"Folder extracted to '{target_dir}'.")
        except Exception as e:
            print_error(f"Failed to auto-extract zip file: {e}")

    def _handle_client(self, conn, addr):
        private_key = None
        try:
            try: host = socket.gethostbyaddr(addr[0])[0]
            except: host = addr[0]
            
            initial_request = recv_json(conn)
            if not initial_request or initial_request.get('action') != 'request_transfer': return
            
            metadata = initial_request['metadata']
            
            # --- Text Snippet Handling ---
            if metadata['filename'] == '__pyshare_text_snippet__':
                print_success(f"\n--- Text Snippet from {host} ---")
                print(f"{Fore.WHITE}{metadata['content']}")
                print(f"{Fore.GREEN}-------------------------------------")
                pyperclip.copy(metadata['content'])
                print_info("Snippet copied to clipboard.")
                return

            # --- File/Folder Transfer Confirmation ---
            fname, fsize = os.path.basename(metadata['filename']), metadata['filesize']
            partial_path = fname + ".part"
            resume_from = os.path.getsize(partial_path) if os.path.exists(partial_path) else 0

            print_info(f"\nIncoming transfer request from {host} for '{fname}' ({fsize/(1024*1024):.2f} MB).")
            if resume_from > 0: print_info(f"Partial file found. Can resume from {resume_from/(1024*1024):.2f} MB.")
            
            if input(f"{Fore.YELLOW}PROMPT: Accept? [y/n]: {Style.RESET_ALL}").lower() != 'y':
                send_json(conn, {'status': 'rejected'})
                print_info("Transfer rejected.")
                return

            # --- Secure Handshake ---
            pin = str(random.randint(1000, 9999))
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            send_json(conn, {'status': 'ready', 'pin': pin, 'public_key': public_key_pem, 'resume_from': resume_from})

            encrypted_key_data = recv_json(conn)
            if not encrypted_key_data: return
            
            encrypted_fernet_key = bytes.fromhex(encrypted_key_data['fernet_key'])
            fernet_key = private_key.decrypt(
                encrypted_fernet_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
            )
            fernet = Fernet(fernet_key)
            send_json(conn, {'status': 'go'})

            # --- Data Transfer ---
            with open(partial_path, 'ab') as f, tqdm(total=fsize, initial=resume_from, desc=f"Receiving from {host}", unit='B', unit_scale=True, colour='green') as pbar:
                received = resume_from
                while received < fsize:
                    chunk_len_bytes = conn.recv(4)
                    if not chunk_len_bytes: break
                    chunk_len = int.from_bytes(chunk_len_bytes, 'big')
                    encrypted_chunk = conn.recv(chunk_len)
                    if not encrypted_chunk: break
                    chunk = fernet.decrypt(encrypted_chunk)
                    f.write(chunk)
                    received += len(chunk)
                    pbar.update(len(chunk))

            os.rename(partial_path, fname)
            print_success(f"File '{fname}' received successfully.")
            
            if fname.lower().endswith('.zip'):
                self._unzip_and_cleanup(fname)
            
        except Exception as e:
            print_error(f"Transfer failed: {e}")
        finally:
            conn.close()

    def _file_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: s.bind(('', TCP_PORT))
            except OSError:
                print_error(f"Could not start receiver: Port {TCP_PORT} is in use.")
                self.stop_event.set()
                return
            s.listen(); s.settimeout(1)
            while not self.stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
                except socket.timeout: continue

    def start(self):
        self.stop_event.clear()
        self.threads = [
            threading.Thread(target=self._discovery_responder, daemon=True),
            threading.Thread(target=self._file_listener, daemon=True)
        ]
        for t in self.threads: t.start()
        print_success("Receiver is now active in the background.")

    def stop(self):
        self.stop_event.set()
        print_success("Receiver has been stopped.")

if __name__ == '__main__':
    main()