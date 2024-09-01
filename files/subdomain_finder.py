import os
import sys
import requests
from colorama import Fore, Style, init
from random import choice
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import pyfiglet
import time


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
wordlists_dir = os.path.join(script_dir, '..', 'wordlists')


os.makedirs(results_dir, exist_ok=True)


output_lock = Lock()


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
]


custom_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
}

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Subdomain Finder", font="doom")
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

def summary(msg):
    """Prints summary messages."""
    with output_lock:
        print(Fore.YELLOW + "[!] " + msg)

class SubdomainFinder:
    def __init__(self):
        clear_console()
        display_banner()

        self.base_domain, self.subdomains, self.num_threads = self.get_user_input()
        self.total_attempts = len(self.subdomains)
        self.attempt_number = 0
        self.failed_attempts = []

        self.found_subdomains = []
        self.queue = Queue()
        for subdomain in self.subdomains:
            self.queue.put(subdomain)

        self.run()

    def clean_domain(self, domain):
        """Cleans the base domain to ensure it is in the correct format."""
        domain = domain.lower().strip()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://")[1]
        return domain.rstrip('/')

    def get_user_input(self):
        """Gathers user input for the Subdomain Finder."""
        base_domain = input(Fore.WHITE + "[+] Enter target base domain (e.g., example.com): ").strip()
        base_domain = self.clean_domain(base_domain)
        status(f"Target base domain set to: {base_domain}")

        wordlist_file = input(Fore.WHITE + "[+] Enter subdomains wordlist file (default: subdomains_wordlist.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "subdomains_wordlist.txt")
        status(f"Loading subdomains from {wordlist_file}...")
        if not os.path.isfile(wordlist_file):
            sys.exit(f"Wordlist file not found: {wordlist_file}")
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            subdomains = [line.strip() for line in f if line.strip()]
        if not subdomains:
            sys.exit("No subdomains found in the wordlist.")
        success(f"{len(subdomains)} subdomains loaded from the wordlist.")

        num_threads = int(input(Fore.WHITE + "[+] Enter number of threads to use (default: 10, press Enter for default): ") or 10)

        status("All inputs received successfully.")
        print(Fore.YELLOW + "-"*60)
        print(Fore.YELLOW + Style.BRIGHT + "Starting subdomain search...")
        return base_domain, subdomains, num_threads

    def run(self):
        """Runs the subdomain finder with a thread pool."""
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {executor.submit(self.check_subdomain, self.queue.get()): self.queue.get() for _ in range(self.queue.qsize())}
            for future in as_completed(futures):
                subdomain = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.failed_attempts.append(subdomain)

        if self.found_subdomains:
            success("Subdomains found:")
            for subdomain in self.found_subdomains:
                print(Fore.CYAN + subdomain)
        else:
            status("No subdomains found.")

        if self.failed_attempts:
            summary(f"{len(self.failed_attempts)} subdomains failed to connect:")
            for subdomain in self.failed_attempts:
                print(Fore.RED + f"[-] {subdomain}")

    def check_subdomain(self, subdomain, retries=3, delay=1):
        """Attempts to find subdomains using the provided subdomain."""
        full_url = f"http://{subdomain}.{self.base_domain}"
        for attempt in range(retries):
            try:
                headers = custom_headers.copy()
                headers['User-Agent'] = choice(user_agents)
                response = requests.get(full_url, headers=headers, timeout=5)

                self.attempt_number += 1
                progress = f"{(self.attempt_number/self.total_attempts) * 100:.2f}%"
                
                if response.status_code in [200, 301, 302, 403, 401]:
                    self.found_subdomains.append(full_url)
                    success_msg = (
                        f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {full_url} [{progress}]\n"
                        f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Subdomain found!\n"
                        f"{Fore.YELLOW}{'-'*40}\n"
                        f"URL: {Fore.CYAN}{full_url}{Style.RESET_ALL}\n"
                        f"{Fore.YELLOW}{'-'*40}\n"
                    )
                    sys.stdout.write('\033[K')  
                    print(success_msg)
                    with open(os.path.join(results_dir, 'Subdomains_Found.txt'), 'a') as writer:
                        writer.write(success_msg)
                    break
                else:
                    with output_lock:
                        sys.stdout.write(f'\r\033[K')  
                        sys.stdout.write(f'[{self.attempt_number}/{self.total_attempts}] Tested - Current: {full_url} [{progress}]')
                        sys.stdout.flush()
            except requests.exceptions.RequestException:
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                self.failed_attempts.append(full_url)
                break

def main():
    try:
        SubdomainFinder()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "Script interrupted by user.")

if __name__ == '__main__':
    main()
