#!/usr/bin/env python3
"""
NetScan v2 - WLAN & Bluetooth Scanner für Termux
Add-ons: SQLite History, Port Scanner, Netzwerk-Map
"""

import subprocess
import sys
import os
import socket
import time
import sqlite3
import threading
from datetime import datetime

# ─── Farben ───────────────────────────────────────────────
R="\033[91m"; G="\033[92m"; Y="\033[93m"
B="\033[94m"; C="\033[96m"; W="\033[0m"; BOLD="\033[1m"

DB_PATH = os.path.expanduser("~/.netscan.db")

# ─── Datenbank ────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT, mac TEXT, hostname TEXT,
            first_seen TEXT, last_seen TEXT,
            scan_type TEXT
        )
    """)
    con.commit()
    con.close()

def save_device(ip, mac, hostname, scan_type="wifi"):
    con = sqlite3.connect(DB_PATH)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = con.execute("SELECT id FROM devices WHERE ip=? AND mac=?", (ip, mac)).fetchone()
    if row:
        con.execute("UPDATE devices SET last_seen=? WHERE id=?", (now, row[0]))
    else:
        con.execute("INSERT INTO devices (ip,mac,hostname,first_seen,last_seen,scan_type) VALUES (?,?,?,?,?,?)",
                    (ip, mac, hostname, now, now, scan_type))
    con.commit()
    con.close()

def show_history():
    print(f"\n{BOLD}{Y}[*] Geräte-History:{W}\n")
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT ip,mac,hostname,first_seen,last_seen,scan_type FROM devices ORDER BY last_seen DESC").fetchall()
    con.close()
    if not rows:
        print(f"  {Y}Noch keine Geräte gespeichert.{W}")
        return
    print(f"  {'IP':<16} {'MAC':<18} {'Hostname':<20} {'Zuletzt':<20} {'Typ'}")
    print("  " + "─"*80)
    for r in rows:
        print(f"  {G}{r[0]:<16}{W} {C}{r[1]:<18}{W} {Y}{r[2]:<20}{W} {r[4]:<20} {r[5]}")

# ─── Netzwerk Helfer ──────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None

def get_subnet(ip):
    return ".".join(ip.split(".")[:3])

def ping_host(ip):
    try:
        r = subprocess.run(["ping","-c","1","-W","1",ip],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return r.returncode == 0
    except:
        return False

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unbekannt"

def get_mac(ip):
    try:
        r = subprocess.run(["arp","-n",ip], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if ip in line:
                for p in line.split():
                    if ":" in p and len(p)==17:
                        return p
    except:
        pass
    return "??:??:??:??:??:??"

# ─── WLAN Scan ────────────────────────────────────────────
def scan_wifi():
    print(f"\n{BOLD}{Y}[*] WLAN Ping Sweep...{W}")
    local_ip = get_local_ip()
    if not local_ip:
        print(f"{R}[!] Keine IP. Mit WLAN verbunden?{W}")
        return []

    subnet = get_subnet(local_ip)
    print(f"{G}[+] Eigene IP: {local_ip} | Subnetz: {subnet}.0/24{W}\n")

    found = []
    threads = []
    lock = threading.Lock()

    def check(ip):
        if ping_host(ip):
            mac = get_mac(ip)
            host = get_hostname(ip)
            marker = f"{G}← DU{W}" if ip == local_ip else ""
            with lock:
                print(f"  {G}[+]{W} {ip:<16} MAC: {C}{mac}{W}  Host: {Y}{host}{W} {marker}")
                found.append((ip, mac, host))
                save_device(ip, mac, host)

    for i in range(1, 255):
        t = threading.Thread(target=check, args=(f"{subnet}.{i}",))
        threads.append(t)
        t.start()
        if len(threads) % 50 == 0:
            for t in threads: t.join()
            threads = []

    for t in threads: t.join()
    print(f"\n{BOLD}Gefunden: {len(found)} Geräte{W}")
    return found

# ─── Port Scanner ─────────────────────────────────────────
COMMON_PORTS = {
    21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP",
    53:"DNS", 80:"HTTP", 110:"POP3", 143:"IMAP",
    443:"HTTPS", 445:"SMB", 3306:"MySQL",
    3389:"RDP", 5900:"VNC", 8080:"HTTP-Alt",
    8443:"HTTPS-Alt", 1883:"MQTT", 5353:"mDNS"
}

def port_scan(ip):
    print(f"\n{BOLD}{Y}[*] Port Scan: {ip}{W}\n")
    open_ports = []
    for port, name in COMMON_PORTS.items():
        try:
            s = socket.socket()
            s.settimeout(0.5)
            if s.connect_ex((ip, port)) == 0:
                print(f"  {G}[OPEN]{W} {port:<6} {C}{name}{W}")
                open_ports.append((port, name))
            s.close()
        except:
            pass
    if not open_ports:
        print(f"  {Y}Keine bekannten Ports offen.{W}")

def scan_with_ports():
    devices = scan_wifi()
    if not devices:
        return
    print(f"\n{BOLD}Port Scan für alle Geräte:{W}")
    for ip, mac, host in devices:
        port_scan(ip)

# ─── Netzwerk ASCII Map ───────────────────────────────────
def network_map():
    print(f"\n{BOLD}{C}[*] Netzwerk-Map wird erstellt...{W}\n")
    local_ip = get_local_ip()
    if not local_ip:
        print(f"{R}Keine IP.{W}")
        return

    subnet = get_subnet(local_ip)
    found = []
    threads = []
    lock = threading.Lock()

    def check(ip):
        if ping_host(ip):
            host = get_hostname(ip)
            mac = get_mac(ip)
            with lock:
                found.append((ip, host, mac))

    for i in range(1, 255):
        t = threading.Thread(target=check, args=(f"{subnet}.{i}",))
        threads.append(t)
        t.start()
        if len(threads) % 50 == 0:
            for t in threads: t.join()
            threads = []
    for t in threads: t.join()

    found.sort(key=lambda x: int(x[0].split(".")[-1]))

    print(f"{BOLD}{C}╔══════════════════════════════════════╗{W}")
    print(f"{BOLD}{C}║      NETZWERK MAP  {subnet}.x          ║{W}")
    print(f"{BOLD}{C}╚══════════════════════════════════════╝{W}")
    print(f"\n         {BOLD}[Router/Gateway]{W}")
    print(f"         {Y}{subnet}.1{W}")
    print(f"              │")

    for i, (ip, host, mac) in enumerate(found):
        is_last = i == len(found) - 1
        is_me = ip == local_ip
        branch = "└──" if is_last else "├──"
        tag = f"{G}[ICH]{W}  " if is_me else f"{B}[Gerät]{W}"
        name = f"{Y}{host[:18]}{W}" if host != "unbekannt" else f"{R}unbekannt{W}"
        print(f"         {branch} {tag} {ip:<16} {name}")
        print(f"         {'   ' if is_last else '│'}    MAC: {C}{mac}{W}")

    print(f"\n{BOLD}Gesamt: {len(found)} Geräte online{W}")

# ─── Bluetooth ────────────────────────────────────────────
def scan_bluetooth():
    print(f"\n{BOLD}{B}[*] Bluetooth Scan (10s)...{W}")
    try:
        proc = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc.stdin.write("scan on\n"); proc.stdin.flush()
        time.sleep(10)
        proc.stdin.write("devices\n"); proc.stdin.flush()
        time.sleep(1)
        proc.stdin.write("scan off\nexit\n"); proc.stdin.flush()
        out, _ = proc.communicate(timeout=5)
        seen = set()
        for line in out.split("\n"):
            if "Device" in line and ":" in line:
                parts = line.strip().split(" ", 2)
                if len(parts) >= 2:
                    mac = parts[1]
                    name = parts[2] if len(parts) > 2 else "Unbekannt"
                    if mac not in seen:
                        seen.add(mac)
                        print(f"  {B}[BT]{W} {C}{mac}{W}  {Y}{name}{W}")
                        save_device(mac, mac, name, "bluetooth")
        if not seen:
            print(f"  {Y}Keine Geräte gefunden.{W}")
    except FileNotFoundError:
        print(f"  {R}bluetoothctl fehlt: pkg install bluez{W}")
    except Exception as e:
        print(f"  {R}Fehler: {e}{W}")

# ─── Menü ─────────────────────────────────────────────────
def banner():
    print(f"""
{C}{BOLD}╔══════════════════════════════════╗
║      NetScan v2 für Termux       ║
║  WLAN · BT · Ports · Map · Log   ║
╚══════════════════════════════════╝{W}""")

def menu():
    banner()
    print(f"""
  {BOLD}1{W} - WLAN Geräte scannen
  {BOLD}2{W} - WLAN + Port Scanner
  {BOLD}3{W} - Netzwerk ASCII Map
  {BOLD}4{W} - Bluetooth Scan
  {BOLD}5{W} - Geräte-History (SQLite)
  {BOLD}6{W} - Alles scannen
  {BOLD}q{W} - Beenden
""")
    choice = input(f"{C}> {W}").strip().lower()

    if choice == "1":
        scan_wifi()
    elif choice == "2":
        scan_with_ports()
    elif choice == "3":
        network_map()
    elif choice == "4":
        scan_bluetooth()
    elif choice == "5":
        show_history()
    elif choice == "6":
        scan_wifi()
        network_map()
        scan_bluetooth()
        show_history()
    elif choice == "q":
        print(f"{Y}Tschüss!{W}")
        sys.exit(0)
    else:
        print(f"{R}Ungültig{W}")

    input(f"\n{Y}[Enter] zurück...{W}")
    menu()

if __name__ == "__main__":
    init_db()
    menu()
