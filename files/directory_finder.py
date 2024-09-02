import os
import sys
import requests
from colorama import Fore, Style, init
from random import choice
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import pyfiglet

init(autoreset=True)

# Removed logging setup
# logging.basicConfig(filename=os.path.join('Logs', 'directory_finder.log'),
#                     level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')
wordlists_dir = os.path.join(script_dir, '..', 'wordlists')

os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

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
    banner = pyfiglet.figlet_format("Directory Finder", font="doom")
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

class DirectoryFinder:
    def __init__(self):
        clear_console()
        display_banner()

        self.base_url, self.paths, self.num_threads = self.get_user_input()
        self.total_attempts = len(self.paths)
        self.attempt_number = 0

        self.found_directories = []
        self.queue = Queue()
        for path in self.paths:
            self.queue.put(self.clean_path(path))

        self.run()

    def clean_url(self, url):
        """Cleans the base URL to ensure it is in the correct format."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        return url.rstrip('/')

    def clean_path(self, path):
        """Cleans the path to ensure it doesn't start with a slash."""
        return path.lstrip('/')

    def get_user_input(self):
        """Gathers user input for the Directory Finder."""
        base_url = input(Fore.WHITE + "[+] Enter target base URL (e.g., https://example.com): ").strip()
        base_url = self.clean_url(base_url)
        status(f"Target base URL set to: {base_url}")

        wordlist_file = input(Fore.WHITE + "[+] Enter paths wordlist file (default: directory_wordlists.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "directory_wordlists.txt")
        status(f"Loading paths from {wordlist_file}...")
        if not os.path.isfile(wordlist_file):
            error(f"Wordlist file not found: {wordlist_file}")
            sys.exit(1)
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            paths = [line.strip() for line in f if line.strip()]
        if not paths:
            error("No paths found in the wordlist.")
            sys.exit(1)
        success(f"{len(paths)} paths loaded from the wordlist.")

        num_threads = int(input(Fore.WHITE + "[+] Enter number of threads to use (default: 10, press Enter for default): ") or 10)

        status("All inputs received successfully.")
        print(Fore.YELLOW + "-"*60)
        print(Fore.YELLOW + Style.BRIGHT + "Starting directory search...")
        return base_url, paths, num_threads

    def run(self):
        """Runs the directory finder with a thread pool."""
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {executor.submit(self.check_path, self.queue.get()): self.queue.get() for _ in range(self.queue.qsize())}
            for future in as_completed(futures):
                path = futures[future]
                try:
                    future.result()
                except Exception as e:
                    error(f"Error processing path {path}: {e}")

        if self.found_directories:
            success("Directories found:")
            for directory in self.found_directories:
                print(Fore.CYAN + directory)
        else:
            status("No directories found.")

    def check_path(self, path):
        """Attempts to find directories using the provided path."""
        full_url = f"{self.base_url}/{path}"
        try:
            headers = custom_headers.copy()
            headers['User-Agent'] = choice(user_agents)
            response = requests.get(full_url, headers=headers, timeout=5)

            self.attempt_number += 1
            progress = f"{(self.attempt_number/self.total_attempts) * 100:.2f}%"
            
            if response.status_code in [200, 301, 302, 403, 401]:
                self.found_directories.append(full_url)
                success_msg = (
                    f"\n[{self.attempt_number}/{self.total_attempts}] Tested - {full_url} [{progress}]\n"
                    f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Directory found!\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                    f"URL: {Fore.CYAN}{full_url}{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}{'-'*40}\n"
                )
                sys.stdout.write('\033[K')  
                print(success_msg)
                with open(os.path.join(results_dir, 'Directories_Found.txt'), 'a') as writer:
                    writer.write(success_msg)
            else:
                with output_lock:
                    sys.stdout.write(f'\r\033[K')  
                    sys.stdout.write(f'[{self.attempt_number}/{self.total_attempts}] Tested - Current: {full_url} [{progress}]')
                    sys.stdout.flush()

        except requests.exceptions.RequestException as e:
            error(f"Failed to connect to {full_url}: {str(e)}")

def main():
    try:
        DirectoryFinder()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "Script interrupted by user.")

if __name__ == '__main__':
    main()