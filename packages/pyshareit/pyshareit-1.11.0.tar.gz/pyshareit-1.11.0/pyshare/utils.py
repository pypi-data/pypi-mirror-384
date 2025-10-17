# pyshare/utils.py

from colorama import Fore, Style, init

# Initialize Colorama for cross-platform colored text
init(autoreset=True)

def print_info(message):
    print(f"{Fore.CYAN}{Style.BRIGHT}INFO: {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}{Style.BRIGHT}SUCCESS: {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}{Style.BRIGHT}ERROR: {message}{Style.RESET_ALL}")