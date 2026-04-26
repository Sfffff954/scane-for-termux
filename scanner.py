#!/usr/bin/env python3
"""
NetScan - WLAN & Bluetooth Gerätescanner für Termux
Benötigt: pip install scapy bluetooth (oder termux-api)
"""

import subprocess
import sys
import os
import socket
import struct
import time
from datetime import datetime

# ─── Farben ───────────────────────────────────────────────
R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
B = "\033[94m"; C = "\033[96m"; W = "\033[0m"; BOLD = "\033[1m"

def banner():
    print(f"""
{C}{BOLD}╔══════════════════════════════════╗
║     NetScan für Termux           ║
║  WLAN + Bluetooth Erkennung      ║
╚══════════════════════════════════╝{W}
""")

# ─── WLAN: Eigene IP & Subnetz ermitteln ──────────────────
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
    parts = ip.split(".")
    return ".".join(parts[:3])

# ─── WLAN: Ping Sweep ─────────────────────────────────────
def ping_host(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unbekannt"

def get_mac_from_arp(ip):
    try:
        result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if ip in line:
                parts = line.split()
                for p in parts:
                    if ":" in p and len(p) == 17:
                        return p
        return "??:??:??:??:??:??"
    except:
        return "??:??:??:??:??:??"

def scan_wifi():
    print(f"{BOLD}{Y}[*] WLAN-Scan gestartet...{W}")
    local_ip = get_local_ip()
    if not local_ip:
        print(f"{R}[!] Keine IP-Adresse gefunden. Mit WLAN verbunden?{W}")
        return

    subnet = get_subnet(local_ip)
    print(f"{G}[+] Eigene IP: {local_ip} | Subnetz: {subnet}.0/24{W}")
    print(f"{Y}[*] Scanne {subnet}.1 - {subnet}.254 ...{W}\n")

    found = []
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        if ping_host(ip):
            mac = get_mac_from_arp(ip)
            host = get_hostname(ip)
            marker = f"{G}← DU{W}" if ip == local_ip else ""
            print(f"  {G}[+]{W} {ip:<16} MAC: {C}{mac}{W}  Host: {Y}{host}{W} {marker}")
            found.append(ip)

    print(f"\n{BOLD}Gefunden: {len(found)} Geräte{W}")

# ─── Bluetooth Scan ───────────────────────────────────────
def scan_bluetooth_classic():
    """Versucht klassisches Bluetooth via bluetoothctl"""
    print(f"\n{BOLD}{B}[*] Bluetooth Classic Scan (10s)...{W}")
    try:
        # bluetoothctl scan
        proc = subprocess.Popen(
            ["bluetoothctl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.stdin.write("scan on\n")
        proc.stdin.flush()
        time.sleep(10)
        proc.stdin.write("devices\n")
        proc.stdin.flush()
        time.sleep(1)
        proc.stdin.write("scan off\nexit\n")
        proc.stdin.flush()
        out, _ = proc.communicate(timeout=5)

        devices = []
        for line in out.split("\n"):
            if "Device" in line and ":" in line:
                parts = line.strip().split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2] if len(parts) > 2 else "Unbekannt"
                    if mac not in [d[0] for d in devices]:
                        devices.append((mac, name))
                        print(f"  {B}[BT]{W} {C}{mac}{W}  Name: {Y}{name}{W}")

        if not devices:
            print(f"  {Y}Keine Geräte gefunden (Bluetooth aktiv?){W}")
    except FileNotFoundError:
        print(f"  {R}bluetoothctl nicht gefunden. Installiere: pkg install bluez{W}")
    except Exception as e:
        print(f"  {R}Fehler: {e}{W}")

def scan_bluetooth_termux_api():
    """Bluetooth über Termux:API (einfacher auf Android)"""
    print(f"\n{BOLD}{B}[*] Bluetooth Scan via Termux:API...{W}")
    try:
        result = subprocess.run(
            ["termux-bluetooth-scanmode", "scan"],
            capture_output=True, text=True, timeout=5
        )
        result2 = subprocess.run(
            ["termux-bluetooth-deviceinfo"],
            capture_output=True, text=True, timeout=15
        )
        if result2.stdout:
            print(result2.stdout)
        else:
            print(f"  {Y}Keine Ausgabe. termux-api App installiert?{W}")
    except FileNotFoundError:
        print(f"  {R}termux-api nicht gefunden.{W}")
        print(f"  {Y}Installiere: pkg install termux-api{W}")
        print(f"  {Y}+ Termux:API App aus F-Droid{W}")
    except Exception as e:
        print(f"  {R}Fehler: {e}{W}")

# ─── WLAN-Nachbarn via termux-wifi-scaninfo ───────────────
def scan_wifi_aps():
    print(f"\n{BOLD}{Y}[*] WLAN Access Points via Termux:API...{W}")
    try:
        result = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout:
            import json
            aps = json.loads(result.stdout)
            for ap in aps:
                ssid = ap.get("ssid", "?")
                bssid = ap.get("bssid", "?")
                level = ap.get("level", "?")
                freq = ap.get("frequency", "?")
                print(f"  {G}[AP]{W} {Y}{ssid:<25}{W} BSSID: {C}{bssid}{W}  Signal: {level} dBm  Freq: {freq} MHz")
        else:
            print(f"  {Y}Keine Daten. termux-api installiert?{W}")
    except FileNotFoundError:
        print(f"  {R}termux-api nicht gefunden: pkg install termux-api{W}")
    except Exception as e:
        print(f"  {R}Fehler: {e}{W}")

# ─── Menü ─────────────────────────────────────────────────
def menu():
    banner()
    print(f"""  {BOLD}1{W} - WLAN Geräte scannen (Ping Sweep)
  {BOLD}2{W} - WLAN Access Points (Termux:API)
  {BOLD}3{W} - Bluetooth Scan (bluetoothctl)
  {BOLD}4{W} - Bluetooth Scan (Termux:API)
  {BOLD}5{W} - Alles scannen
  {BOLD}q{W} - Beenden
""")
    choice = input(f"{C}> {W}").strip().lower()

    if choice == "1":
        scan_wifi()
    elif choice == "2":
        scan_wifi_aps()
    elif choice == "3":
        scan_bluetooth_classic()
    elif choice == "4":
        scan_bluetooth_termux_api()
    elif choice == "5":
        scan_wifi()
        scan_wifi_aps()
        scan_bluetooth_classic()
        scan_bluetooth_termux_api()
    elif choice == "q":
        sys.exit(0)
    else:
        print(f"{R}Ungültige Eingabe{W}")

    input(f"\n{Y}[Enter] zurück...{W}")
    menu()

if __name__ == "__main__":
    menu()
