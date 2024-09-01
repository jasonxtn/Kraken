import os
import sys
import re
import hashlib
import logging
import requests
import concurrent.futures
from colorama import Fore, Style, init
from queue import Queue
import pyfiglet


init(autoreset=True)


logging.basicConfig(filename=os.path.join('Logs', 'webshell_finder.log'),
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')
wordlists_dir = os.path.join(script_dir, '..', 'wordlists')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


def load_wordlist(wordlist_file):
    try:
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        error(f"Wordlist file not found: {wordlist_file}")
        logging.error(f"Wordlist file not found: {wordlist_file}")
        sys.exit(1)


webshell_keywords = [
    'eval(',
    'base64_decode(',
    'system(',
    'exec(',
    'passthru(',
    'shell_exec(',
    'assert(',
    'preg_replace(',
    'create_function(',
    'include(',
    'require(',
    'fopen(',
    'fwrite(',
    'curl_exec(',
]

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner."""
    banner = pyfiglet.figlet_format("Advanced Webshell Finder", font="doom")
    print(Style.BRIGHT + Fore.RED + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def status(msg):
    """Prints status messages."""
    print(Fore.CYAN + "[*] " + msg)

def success(msg):
    """Prints success messages."""
    print(Fore.GREEN + "[+] " + msg)

def error(msg):
    """Prints error messages."""
    print(Fore.RED + "[-] " + msg)

class WebshellFinder:
    def __init__(self):
        clear_console()
        display_banner()
        self.target_url, self.num_threads, self.webshell_patterns = self.get_user_input()
        self.found_shells = []
        self.url_queue = Queue()
        self.collect_urls()

    def get_user_input(self):
        """Gathers user input for the Webshell Finder."""
        target_url = input(Fore.WHITE + "[+] Enter the target URL (e.g., https://example.com): ").strip()
        if not target_url.startswith(('http://', 'https://')):
            error("Invalid URL format.")
            sys.exit(1)
        status(f"Target URL set to: {target_url}")

        wordlist_file = input(Fore.WHITE + "[+] Enter the webshell wordlist file (default: webshell_wordlists.txt, press Enter for default): ").strip() or os.path.join(wordlists_dir, "webshell_wordlists.txt")
        status(f"Loading webshell patterns from {wordlist_file}...")
        webshell_patterns = load_wordlist(wordlist_file)
        success(f"Loaded {len(webshell_patterns)} webshell patterns.")

        num_threads = int(input(Fore.WHITE + "[+] Enter number of threads to use (default: 10, press Enter for default): ") or 10)
        status(f"Using {num_threads} threads.")

        return target_url, num_threads, webshell_patterns

    def collect_urls(self):
        """Generates URLs to check by appending webshell patterns to the base URL."""
        status("Generating URLs to scan...")
        for pattern in self.webshell_patterns:
            full_url = f"{self.target_url}/{pattern}"
            self.url_queue.put(full_url)
        status(f"Generated {self.url_queue.qsize()} URLs to scan.")

    def run(self):
        """Runs the webshell finder using multithreading."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.check_url, self.url_queue.get()) for _ in range(self.url_queue.qsize())]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    self.found_shells.append(result)

        if self.found_shells:
            success("Webshells found:")
            for shell in self.found_shells:
                print(Fore.CYAN + shell)
            with open(os.path.join(results_dir, 'Webshells_Found.txt'), 'w') as writer:
                writer.write("\n".join(self.found_shells))
        else:
            status("No webshells found.")

    def check_url(self, url):
        """Checks a URL for webshell patterns and signatures."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content_hash = hashlib.md5(response.content).hexdigest()
                for signature in webshell_keywords:
                    if signature in response.text:
                        return self.report_shell(url, f"Content contains suspicious keyword: {signature}")
                return self.report_shell(url, "URL is accessible and returns a valid response.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error accessing URL {url}: {str(e)}")
            error(f"Error accessing URL {url}: {str(e)}")
        return None

    def report_shell(self, url, reason):
        """Reports a URL as a potential webshell."""
        success(f"Potential webshell found: {url}")
        status(f"Reason: {reason}")
        report = f"{url} - {reason}"
        logging.info(report)
        return report

def main():
    try:
        finder = WebshellFinder()
        finder.run()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")

if __name__ == '__main__':
    main()
