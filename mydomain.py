#!/usr/bin/env python3
# usage: python3 mydomain.py -d <domaine> où mydomain -d <domaine>
# exemple: python3 mydomain.py -d tesla.com --recursive -i 
#          mydomain -d tesla.com --recurisive -i
# le mieux est de l'ajouter à votre patch root pour pourvoir l'utiliser partout dans votre terminal.

#par Pikachu :)

import requests
from rich.live import Live
import socket
import re
import time
import threading
from rich.console import Console
import httpx
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()
parser = argparse.ArgumentParser(prog='mydomain.py ')
parser.add_argument('-r', '--recursive', action='store_true', help='enumerate subdomains recursively')
parser.add_argument('-a', '--all', action='store_true', help='enumerate all subdomains')
parser.add_argument('-t', '--timeout', type=int, default=2, help='timeout for requests')
parser.add_argument('-rl', '--rate-limit', type=int, default=1, help='rate limit for requests')
parser.add_argument('-d', '--domaine', type=str, required=True, help='enumerate subdomains')
parser.add_argument('-i', '--ip', action='store_true', help='get IP adress of subdomains')

console.print("""
[bold cyan]
                              888                                 d8b          
                            888                                 Y8P          
                            888                                            vesrion 1.0  
88888b.d88b.  888  888  .d88888  .d88b.  88888b.d88b.   8888b.  888 88888b.  
888 "888 "88b 888  888 d88" 888 d88""88b 888 "888 "88b     "88b 888 888 "88b 
888  888  888 888  888 888  888 888  888 888  888  888 .d888888 888 888  888 
888  888  888 Y88b 888 Y88b 888 Y88..88P 888  888  888 888  888 888 888  888 
888  888  888  "Y88888  "Y88888  "Y88P"  888  888  888 "Y888888 888 888  888 
                   888                                                       
              Y8b d88P                                                       
               "Y88P"                                                        
                               
[/bold cyan]
[green]by Pikachu[/green]
[dim]                 FILESS[/dim]
[dim]          [yellow]OUtils d'énumération de subdomaine avancé. [/yellow]  [/dim]
""")

args = parser.parse_args()
console.print(f"[yellow][+] domaine : {args.domaine} | timeout : {args.timeout} | rate-limit : {args.rate_limit} [/yellow]")
time.sleep(1)
console.print("[blue] Analyse en cours...")
time.sleep(2)
console.print(f"[red] ----- enumeration de {args.domaine} en cours... -----")

start_time = time.time()
stop_timer = threading.Event()
live = Live(console=console, refresh_per_second=1)
def timer():
    while not stop_timer.is_set():
        elapsed = int(time.time() - start_time)
        live.update(
            f"[blue]Enumeration en cours... {elapsed}s[/blue]",
            
        )
        time.sleep(1)
timer_thread = threading.Thread(target=timer)
timer_thread.start()

def check_subdomain(subdomain):
    try:
        response = httpx.get(
            f"http://{subdomain}",
            timeout=args.timeout,
            follow_redirects=False
        )

        return subdomain, response.status_code, response.headers.get("Server", "[server non trouvé]")

    except Exception:
        return None

def get_subdomains(domain):
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        response = requests.get(url)
        subdomains = set()
        if response.status_code == 200:
            data = response.json()
            
            for entry in data:
                names = entry.get("name_value", "")
                names = names.replace("\\n", "\n")

                if not entry:
                    continue

                for subdomain in names.splitlines():
                    subdomain = subdomain.strip()
                    if subdomain.startswith("*."):
                        subdomain = subdomain[2:]
                    

                    if subdomain and re.fullmatch(r"^[a-zA-Z0-9.-]+$", subdomain):
                        subdomains.add(subdomain)
            
        return subdomains
    
    except Exception as e:
        console.print(f"Error : {e}")

def get_interesting_subdomains(domain, subdomains):
    interesting_subdomaines = []
    with ThreadPoolExecutor(max_workers=args.rate_limit) as executor:
         futures = {executor.submit(check_subdomain, subdomain): subdomain for subdomain in subdomains}


         for future in as_completed(futures):
             result = future.result()

             if result is None:
                continue

             subdomain, status_code, server = result
             if args.ip:
                 try:
                     ip_address = socket.getaddrinfo(subdomain, None)[0][4][0]
                 except socket.gaierror:
                     ip_address = ""
             else:
                 ip_address = ""

             console.print(f"[yellow] {subdomain} :[/yellow] [purple] {status_code} / {server} [/purple] [blue] {ip_address} [/blue]")

             if status_code == 200:
                interesting_subdomaines.append(subdomain)
            
    return interesting_subdomaines        

subdomains = get_subdomains(args.domaine)
interesting_subdomains = get_interesting_subdomains(args.domaine, subdomains)
stop_timer.set()
timer_thread.join()
