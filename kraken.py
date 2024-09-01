import os
import sys
import time
import random
import subprocess


if sys.version_info < (3, 0):
    print("This script requires Python 3.")
    sys.exit(1)


try:
    from rich.console import Console
    from rich.table import Table
    from rich.box import SIMPLE_HEAVY
    from colorama import Fore
except ImportError as e:
    print(f"Error: {e}. Please install the required modules using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

console = Console()

def clearScr():
    if os.name == 'nt':  
        os.system('cls')
    else:  
        os.system('clear')

def logo():
    clear = "\x1b[0m"
    colors = [36, 32, 34, 35, 31, 37]

    x = r""" 

        ▄█   ▄█▄    ▄████████    ▄████████    ▄█   ▄█▄    ▄████████ ███▄▄▄▄   
        ███ ▄███▀   ███    ███   ███    ███   ███ ▄███▀   ███    ███ ███▀▀▀██▄ 
        ███▐██▀     ███    ███   ███    ███   ███▐██▀     ███    █▀  ███   ███ 
        ▄█████▀     ▄███▄▄▄▄██▀   ███    ███  ▄█████▀     ▄███▄▄▄     ███   ███ 
        ▀▀█████▄    ▀▀███▀▀▀▀▀   ▀███████████ ▀▀█████▄    ▀▀███▀▀▀     ███   ███ 
        ███▐██▄   ▀███████████   ███    ███   ███▐██▄     ███    █▄  ███   ███ 
        ███ ▀███▄   ███    ███   ███    ███   ███ ▀███▄   ███    ███ ███   ███ 
        ███   ▀█▀   ███    ███   ███    █▀    ███   ▀█▀   ██████████  ▀█   █▀  
        ▀           ███    ███                ▀                                
                                                                                                    
                    NOTE! : I'M NOT RESPONSIBLE FOR ANY ILLEGAL USAGE.
                    CODED BY : JASON13
                    VERSION : 1.0
    """

    for N, line in enumerate(x.split("\n")):
        sys.stdout.write("\x1b[1;%dm%s%s\n" % (random.choice(colors), line, clear))
        time.sleep(0.05)

def display_table():
    table = Table(box=SIMPLE_HEAVY)

    
    table.add_column("Network Tools", justify="left", style="cyan", no_wrap=True)
    table.add_column("Webapps Tools", justify="left", style="magenta", no_wrap=True)
    table.add_column("Finder Tools", justify="left", style="green", no_wrap=True)

    
    table.add_row("1. FTP Brute Force", "11. Cpanel Brute Force", "30. Admin Panel Finder")
    table.add_row("2. Kubernetes Brute Force", "12. Drupal Brute Force", "31. Directory Finder")
    table.add_row("3. LDAP Brute Force", "13. Joomla Brute Force", "32. Subdomain Finder")
    table.add_row("4. VOIP Brute Force", "15. Office365 Brute Force", "")
    table.add_row("5. SSH Brute Force", "16. Prestashop Brute Force", "")
    table.add_row("6. Telnet Brute Force", "17. OpenCart Brute Force", "")
    table.add_row("7. WiFi Brute Force", "18. WooCommerce Brute Force", "")
    table.add_row("8. RDP Brute Force", "19. WordPress Brute Force", "")

    
    table.add_row("", "", "")
    table.add_row("", "[bold red]-" * 15 + " 00. EXIT " + "-" * 15 + "[/bold red]", "", end_section=True)
    console.print(table)

def execute_script(script_name):
    """Executes the script based on the user's choice."""
    script_path = os.path.join("files", script_name)
    
    if os.path.isfile(script_path):
        if os.name == 'nt':  
            subprocess.call(['python', script_path])
        else:  
            subprocess.call(['python3', script_path])
    else:
        print(Fore.RED + f"Script {script_name} not found in 'files' directory.")

def main():
    clearScr()
    logo()
    display_table()

    tools_mapping = {
        '1': 'ftp_bruteforce.py',
        '2': 'kubernetes_bruteforce.py',
        '3': 'ldap_bruteforce.py',
        '4': 'voip_bruteforce.py',
        '5': 'ssh_bruteforce.py',
        '6': 'telnet_bruteforce.py',
        '7': 'wifi_bruteforce.py',
        '8': 'rdp_bruteforce.py',
        '11': 'cpanel_bruteforce.py',
        '12': 'drupal_bruteforce.py',
        '13': 'joomla_bruteforce.py',
        '14': 'magento_bruteforce.py',
        '15': 'office365_bruteforce.py',
        '16': 'prestashop_bruteforce.py',
        '17': 'opencart_bruteforce.py',
        '18': 'woocommerce_bruteforce.py',
        '19': 'wordpress_bruteforce.py',
        '30': 'admin_panel_finder.py',
        '31': 'directory_finder.py',
        '32': 'subdomain_finder.py',
        '33': 'webshell_finder.py',
        '00': 'exitkraken',
    }

    try:
        kraken = input("root@kraken:~# ")
        clearScr()

        if kraken in tools_mapping:
            if kraken == '00':
                print('\033[97m\nClosing Kraken\nPlease Wait...\033[1;m')
                time.sleep(2)
                sys.exit()
            else:
                execute_script(tools_mapping[kraken])
        else:
            print("Invalid Input!")
    except KeyboardInterrupt:
        print('\033[97m\nScript interrupted by user.\033[1;m')
        sys.exit()

if __name__ == "__main__":
    main()
