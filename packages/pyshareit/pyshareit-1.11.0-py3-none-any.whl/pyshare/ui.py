# pyshare/ui.py

import platform
import shlex
import time
from colorama import Fore, Style
from .sender import Sender
from .receiver import Receiver
from .utils import print_info, print_success, print_error


def show_help():
    print(f"""
{Fore.YELLOW}{Style.BRIGHT}pyshare - Secure File Transfer{Style.RESET_ALL}

{Style.BRIGHT}MAIN COMMANDS:{Style.RESET_ALL}
  connect                  Search for devices and connect to one to send files.
  receive                  Become discoverable and wait to receive files.
  help                     Show this help message.
  exit / quit              Exit the application.

{Style.BRIGHT}COMMANDS (WHEN CONNECTED):{Style.RESET_ALL}
  send <path>              Send a file or folder to the connected device.
  send -t "message"        Send a text snippet to the connected device.
  back                     Disconnect and return to the main menu.
    """)

def connected_loop(sender, target_info):
    """A dedicated loop for when connected to a specific device."""
    target_name = target_info['hostname']
    print_success(f"Connected to {target_name}. You can now send files or text.")
    
    while True:
        try:
            line = input(f"{Fore.CYAN}pyshare ({target_name})> {Style.RESET_ALL}").strip()
            if not line:
                continue
            
            parts = shlex.split(line)
            command = parts[0].lower()
            args = parts[1:]

            if command == "send":
                if not args:
                    print_error("Usage: send <path> or send -t <message>")
                    continue
                if args[0] == '-t':
                    text_to_send = " ".join(args[1:])
                    sender.start_transfer(target_info, {'type': 'text', 'content': text_to_send})
                else:
                    path_to_send = " ".join(args)
                    sender.start_transfer(target_info, {'type': 'path', 'content': path_to_send})
            
            elif command == "back":
                print_info("Disconnecting and returning to main menu.")
                return

            elif command in ["exit", "quit"]:
                print_info("Exiting.")
                return "exit" # Signal to the main loop to exit

            else:
                print_error(f"Unknown command. Use 'send', 'back', or 'exit'.")

        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            return "exit"


def main_loop():
    try:
        if platform.system() != "Windows":
            import readline
        else:
            import pyreadline3
    except ImportError:
        print("Install 'pyreadline3' for command history on Windows.")
    
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*60}")
    print(f"{'pyshare - Secure Interactive File Transfer':^60}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    show_help()

    while True:
        try:
            choice = input(f"{Fore.CYAN}pyshare> {Style.RESET_ALL}").strip().lower()
            if not choice:
                continue

            if choice == "connect":
                sender = Sender()
                receivers = sender.discover_devices()

                if not receivers:
                    print_error("No devices found. Make sure the other device has selected 'receive'.")
                    continue

                print_success("Available devices to connect to:")
                for r_id, info in receivers.items():
                    print(f"  [{r_id}] {info['hostname']} ({info['ip']})")

                try:
                    device_id_str = input("Enter device ID to connect (or 'c' to cancel): ")
                    if device_id_str.lower() == 'c':
                        continue
                    
                    device_id = int(device_id_str)
                    target_info = receivers[device_id]
                except (ValueError, KeyError):
                    print_error("Invalid selection. Returning to main menu.")
                    continue
                
                # Enter the dedicated loop for sending files
                result = connected_loop(sender, target_info)
                if result == "exit":
                    break

            elif choice == "receive":
                receiver = Receiver()
                receiver.start()
                print_info("This device is now discoverable. Waiting for connections...")
                print_info("Press Ctrl+C to stop and return to the main menu.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping receiver...")
                    receiver.stop()
                    print_success("Returned to main menu.")
            
            elif choice == "help":
                show_help()

            elif choice in ["exit", "quit"]:
                print_info("Goodbye!")
                break
            
            else:
                print_error(f"Unknown command: '{choice}'. Type 'help' for commands.")

        except KeyboardInterrupt:
            print("\nUse 'exit' or 'quit' to leave the application.")
            continue
        except EOFError:
            print("\nGoodbye!")
            break