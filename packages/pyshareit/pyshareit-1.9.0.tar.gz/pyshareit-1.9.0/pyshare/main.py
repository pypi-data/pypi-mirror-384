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
from datetime import datetime

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
DISCOVERY_INTERVAL = 2  # Send discovery packets every 2 seconds
BROADCAST_ADDRESS = '<broadcast>'
DISCOVERY_MAGIC = b"PYSHARE_DISCOVERY_V2"
RESPONSE_MAGIC = b"PYSHARE_RESPONSE_V2"
BUFFER_SIZE = 4096

# --- UI Helpers ---
def print_info(message): print(f"{Fore.CYAN}{Style.BRIGHT}INFO: {message}{Style.RESET_ALL}")
def print_success(message): print(f"{Fore.GREEN}{Style.BRIGHT}SUCCESS: {message}{Style.RESET_ALL}")
def print_error(message): print(f"{Fore.RED}{Style.BRIGHT}ERROR: {message}{Style.RESET_ALL}")
def print_warn(message): print(f"{Fore.YELLOW}{Style.BRIGHT}WARN: {message}{Style.RESET_ALL}")

# --- Network Protocol Helpers ---
def send_json(sock, data):
    json_data = json.dumps(data).encode('utf-8')
    sock.sendall(len(json_data).to_bytes(4, 'big'))
    sock.sendall(json_data)

def recv_json(sock):
    try:
        data_len = int.from_bytes(sock.recv(4), 'big')
        if not data_len: return None
        return json.loads(sock.recv(data_len))
    except (ConnectionResetError, OSError):
        return None

# --- Sender Logic (COMPLETELY REDESIGNED) ---
class Sender:
    def __init__(self):
        self.receivers = {}
        self.stop_discovery = threading.Event()
        self.receivers_lock = threading.Lock()

    def _discover_receivers(self):
        """Continuous discovery in background - doesn't block"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)
            
            while not self.stop_discovery.is_set():
                try:
                    sock.sendto(DISCOVERY_MAGIC, (BROADCAST_ADDRESS, DISCOVERY_PORT))
                    time.sleep(DISCOVERY_INTERVAL)
                except Exception:
                    pass

    def _listen_for_responses(self):
        """Separate thread to listen for responses"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', DISCOVERY_PORT + 1))
            sock.settimeout(0.5)
            
            # Send initial broadcast
            broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            while not self.stop_discovery.is_set():
                try:
                    broadcast_sock.sendto(DISCOVERY_MAGIC, (BROADCAST_ADDRESS, DISCOVERY_PORT))
                except:
                    pass
                
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == RESPONSE_MAGIC:
                        with self.receivers_lock:
                            if addr[0] not in [r['ip'] for r in self.receivers.values()]:
                                try: 
                                    hostname = socket.gethostbyaddr(addr[0])[0]
                                except socket.herror: 
                                    hostname = "Unknown"
                                receiver_id = len(self.receivers) + 1
                                self.receivers[receiver_id] = {'ip': addr[0], 'hostname': hostname}
                                print(f"\n{Fore.MAGENTA}[+] Found Receiver #{receiver_id}: {hostname} ({addr[0]}){Style.RESET_ALL}")
                                print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
                except socket.timeout:
                    continue
            
            broadcast_sock.close()

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

    def start_transfer(self, transfer_request):
        """NON-BLOCKING discovery with immediate user control"""
        print_info("Searching for receivers... (Press Enter when ready to select)")
        
        # Start discovery threads
        discover_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        discover_thread.start()
        
        # Wait for user input instead of timeout
        input(f"{Fore.YELLOW}Press Enter to see available receivers and select one...{Style.RESET_ALL}")
        
        self.stop_discovery.set()  # Stop discovery
        time.sleep(0.5)  # Give threads time to finish
        
        with self.receivers_lock:
            if not self.receivers:
                print_error("No receivers found. Make sure receiver is running on target device.")
                return

            print_success("\nAvailable receivers:")
            for r_id, info in self.receivers.items():
                print(f"  {Fore.CYAN}[{r_id}]{Style.RESET_ALL} {info['hostname']} ({info['ip']})")
        
        try:
            choice = input(f"{Fore.YELLOW}Enter receiver ID (or 'c' to cancel): {Style.RESET_ALL}").strip()
            if choice.lower() == 'c':
                print_info("Transfer cancelled.")
                return
            
            with self.receivers_lock:
                target_info = self.receivers[int(choice)]
        except (ValueError, KeyError):
            print_error("Invalid selection.")
            return

        # Start transfer in new thread so REPL remains responsive
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

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(30)
                s.connect((ip, TCP_PORT))
                
                send_json(s, {'action': 'request_transfer', 'metadata': metadata})
                handshake_data = recv_json(s)
                
                if not handshake_data or handshake_data.get('status') != 'ready':
                    print_error(f"Receiver {hostname} rejected transfer.")
                    return
                
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*60}")
                print(f"⏳ Waiting for receiver to accept...")
                print(f"{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}The receiver will see PIN: {Fore.RED}{Style.BRIGHT}{handshake_data['pin']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}No action needed on sender side - just wait for receiver to accept.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
                
                # Generate encryption key
                fernet_key = Fernet.generate_key()
                pub_key = serialization.load_pem_public_key(handshake_data['public_key'].encode('utf-8'))
                encrypted_fernet_key = pub_key.encrypt(
                    fernet_key, 
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                        algorithm=hashes.SHA256(), 
                        label=None
                    )
                )
                
                send_json(s, {
                    'fernet_key': encrypted_fernet_key.hex(), 
                    'pin': handshake_data['pin']
                })
                
                final_ack = recv_json(s)
                if not final_ack or final_ack.get('status') != 'go':
                    print_error("❌ Transfer rejected - PIN not confirmed by receiver.")
                    print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
                    return
                
                print_success("✅ PIN confirmed by receiver! Starting transfer...")
                fernet = Fernet(fernet_key)
                
                if metadata['type'] == 'path':
                    filesize = metadata['filesize']
                    resume_from = handshake_data.get('resume_from', 0)
                    
                    if resume_from > 0:
                        print_info(f"Resuming from {resume_from / (1024*1024):.2f} MB")
                    
                    with open(temp_zip_path, 'rb') as f:
                        with tqdm(
                            total=filesize, 
                            initial=resume_from, 
                            desc=f"→ {hostname}", 
                            unit='B', 
                            unit_scale=True, 
                            colour='green'
                        ) as pbar:
                            f.seek(resume_from)
                            while True:
                                chunk = f.read(BUFFER_SIZE)
                                if not chunk: 
                                    break
                                encrypted_chunk = fernet.encrypt(chunk)
                                s.sendall(len(encrypted_chunk).to_bytes(4, 'big'))
                                s.sendall(encrypted_chunk)
                                pbar.update(len(chunk))
                    
                    print_success(f"'{metadata['filename']}' sent to {hostname}!")
                    
        except FileNotFoundError as e: 
            print_error(str(e))
        except socket.timeout:
            print_error(f"Connection to {hostname} timed out.")
        except Exception as e: 
            print_error(f"Transfer failed: {e}")
        finally:
            if temp_zip_path and is_temp: 
                shutil.rmtree(os.path.dirname(temp_zip_path))
            print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)

# --- Receiver Logic ---
class Receiver:
    def __init__(self):
        self.stop_event = threading.Event()
        self.threads = []
        self._active_pins = {}
        self.transfer_history = []

    def _discovery_responder(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', DISCOVERY_PORT))
            sock.settimeout(1)
            
            while not self.stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == DISCOVERY_MAGIC:
                        # Respond on different port to avoid conflicts
                        response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        response_sock.sendto(RESPONSE_MAGIC, (addr[0], DISCOVERY_PORT + 1))
                        response_sock.close()
                except socket.timeout: 
                    continue
                except Exception:
                    continue

    def _unzip_and_cleanup(self, zip_path):
        try:
            target_dir = os.path.splitext(zip_path)[0]
            print_info(f"Extracting '{os.path.basename(target_dir)}'...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(zip_path))
            os.remove(zip_path)
            print_success(f"Folder extracted to '{target_dir}'")
        except Exception as e: 
            print_error(f"Failed to extract: {e}")

    def _handle_client(self, conn, addr):
        private_key = None
        try:
            try: 
                host = socket.gethostbyaddr(addr[0])[0]
            except: 
                host = addr[0]
            
            initial_request = recv_json(conn)
            if not initial_request or initial_request.get('action') != 'request_transfer': 
                return
            
            metadata = initial_request['metadata']
            
            # Handle text snippets
            if metadata['filename'] == '__pyshare_text_snippet__':
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*60}")
                print(f"📝 Text from {host} at {timestamp}")
                print(f"{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{metadata['content']}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
                pyperclip.copy(metadata['content'])
                print_info("Copied to clipboard!")
                print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
                return
            
            fname, fsize = os.path.basename(metadata['filename']), metadata['filesize']
            partial_path = fname + ".part"
            resume_from = os.path.getsize(partial_path) if os.path.exists(partial_path) else 0
            
            # Generate PIN
            pin = str(random.randint(1000, 9999))
            self._active_pins[addr[0]] = pin
            
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*60}")
            print(f"📥 Incoming Transfer Request")
            print(f"{'='*60}{Style.RESET_ALL}")
            print(f"From: {Fore.CYAN}{host}{Style.RESET_ALL}")
            print(f"File: {Fore.CYAN}{fname}{Style.RESET_ALL}")
            print(f"Size: {Fore.CYAN}{fsize/(1024*1024):.2f} MB{Style.RESET_ALL}")
            if resume_from > 0:
                print(f"Resume: {Fore.YELLOW}{resume_from/(1024*1024):.2f} MB{Style.RESET_ALL}")
            print(f"\n{Fore.RED}{Style.BRIGHT}⚠️  VERIFY THIS PIN WITH SENDER: {pin}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Make sure the sender sees the same PIN!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
            
            accept = input(f"{Fore.YELLOW}Accept transfer? [y/n]: {Style.RESET_ALL}").lower()
            if accept != 'y':
                send_json(conn, {'status': 'rejected'})
                print_info("Transfer rejected.")
                print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
                return
            
            # Generate keys
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM, 
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            send_json(conn, {
                'status': 'ready', 
                'public_key': public_key_pem, 
                'resume_from': resume_from, 
                'pin': pin
            })
            
            # Verify PIN
            encrypted_key_data = recv_json(conn)
            if not encrypted_key_data or encrypted_key_data.get('pin') != self._active_pins.get(addr[0]):
                send_json(conn, {'status': 'pin_mismatch'})
                print_error("PIN mismatch!")
                print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
                return
            
            del self._active_pins[addr[0]]
            
            # Decrypt Fernet key
            encrypted_fernet_key = bytes.fromhex(encrypted_key_data['fernet_key'])
            fernet_key = private_key.decrypt(
                encrypted_fernet_key, 
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                    algorithm=hashes.SHA256(), 
                    label=None
                )
            )
            fernet = Fernet(fernet_key)
            send_json(conn, {'status': 'go'})
            
            # Receive file
            with open(partial_path, 'ab') as f:
                with tqdm(
                    total=fsize, 
                    initial=resume_from, 
                    desc=f"← {host}", 
                    unit='B', 
                    unit_scale=True, 
                    colour='green'
                ) as pbar:
                    received = resume_from
                    while received < fsize:
                        chunk_len_bytes = conn.recv(4)
                        if not chunk_len_bytes: 
                            break
                        chunk_len = int.from_bytes(chunk_len_bytes, 'big')
                        encrypted_chunk = conn.recv(chunk_len)
                        if not encrypted_chunk: 
                            break
                        chunk = fernet.decrypt(encrypted_chunk)
                        f.write(chunk)
                        received += len(chunk)
                        pbar.update(len(chunk))
            
            os.rename(partial_path, fname)
            print_success(f"'{fname}' received!")
            
            self.transfer_history.append({
                'file': fname,
                'from': host,
                'size': fsize,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            if fname.lower().endswith('.zip'):
                self._unzip_and_cleanup(fname)
            
            print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
            
        except Exception as e: 
            print_error(f"Transfer failed: {e}")
            print(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}", end='', flush=True)
        finally:
            if addr and addr[0] in self._active_pins: 
                del self._active_pins[addr[0]]
            conn.close()

    def _file_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: 
                s.bind(('', TCP_PORT))
            except OSError:
                print_error(f"Port {TCP_PORT} in use!")
                self.stop_event.set()
                return
            
            s.listen()
            s.settimeout(1)
            
            while not self.stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=self._handle_client, 
                        args=(conn, addr), 
                        daemon=True
                    ).start()
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
        print_success("Receiver active and listening!")
    
    def stop(self):
        self.stop_event.set()
        print_success("Receiver stopped.")
    
    def show_history(self):
        if not self.transfer_history:
            print_info("No transfer history.")
            return
        
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Transfer History:{Style.RESET_ALL}")
        for i, transfer in enumerate(self.transfer_history[-10:], 1):
            print(f"  {i}. {transfer['file']} from {transfer['from']} "
                  f"({transfer['size']/(1024*1024):.2f} MB) at {transfer['time']}")

# --- Main Application ---
def show_help():
    print(f"""
{Fore.YELLOW}{Style.BRIGHT}╔════════════════════════════════════════════════════════════╗
║           pyshare v3.1 - Enhanced File Transfer           ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Style.BRIGHT}File Commands:{Style.RESET_ALL}
  send <path>              Send a file or folder
  send --text "message"    Send a text snippet
  paste                    Send clipboard contents
  
{Style.BRIGHT}Receiver Commands:{Style.RESET_ALL}
  receive                  Start receiver (background)
  stop                     Stop receiver
  history                  Show transfer history
  
{Style.BRIGHT}Other:{Style.RESET_ALL}
  help                     Show this message
  clear                    Clear screen
  exit / quit              Exit pyshare

{Fore.CYAN}How PIN Verification Works:{Style.RESET_ALL}
  1. Sender initiates transfer to receiver
  2. Both devices display the SAME 4-digit PIN
  3. Receiver verifies PIN matches, then accepts
  4. Transfer proceeds with end-to-end encryption
  
  ⚠️  Always verify the PIN matches on both devices!
    """)

def main():
    # Setup readline for command history
    try:
        if platform.system() != "Windows": 
            import readline
        else: 
            import pyreadline3
    except ImportError: 
        print_warn("Install 'pyreadline3' for command history on Windows")
    
    # Banner
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*60}")
    print(f"{'pyshare v3.1 - Secure Interactive File Transfer':^60}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    show_help()
    
    receiver_instance = None
    
    while True:
        try:
            line = input(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}").strip()
            if not line: 
                continue
            
            try: 
                parts = shlex.split(line)
            except ValueError: 
                print_error("Mismatched quotes in command.")
                continue
            
            command = parts[0].lower()
            args = parts[1:]
            
            if command == "send":
                if not args: 
                    print_error("Usage: send <path> OR send --text <message>")
                    continue
                
                if args[0] == '--text':
                    text_to_send = " ".join(args[1:])
                    if not text_to_send: 
                        print_error("No text provided.")
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
                print_info("Sending clipboard...")
                Sender().start_transfer({'type': 'text', 'content': clipboard_content})
            
            elif command == "receive":
                if receiver_instance: 
                    print_info("Receiver already running.")
                else: 
                    receiver_instance = Receiver()
                    receiver_instance.start()
            
            elif command == "stop":
                if receiver_instance: 
                    receiver_instance.stop()
                    receiver_instance = None
                else: 
                    print_info("Receiver not running.")
            
            elif command == "history":
                if receiver_instance:
                    receiver_instance.show_history()
                else:
                    print_info("Start receiver first to track history.")
            
            elif command == "clear":
                os.system('cls' if platform.system() == 'Windows' else 'clear')
                show_help()
            
            elif command == "help": 
                show_help()
            
            elif command in ["exit", "quit"]:
                if receiver_instance: 
                    receiver_instance.stop()
                print_info("Goodbye!")
                break
            
            else: 
                print_error(f"Unknown command: '{command}'. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print()  # New line
            continue
        except EOFError:
            if receiver_instance: 
                receiver_instance.stop()
            print_info("\nGoodbye!")
            break

if __name__ == '__main__':
    main()