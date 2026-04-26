# 📡 NetScan v2 für Termux

WLAN & Bluetooth Gerätescanner für Android (Termux)

---

## Features

| # | Feature | Beschreibung |
|---|---------|-------------|
| 1 | WLAN Scan | Alle Geräte im Netz (IP, MAC, Hostname) |
| 2 | Port Scanner | 17 bekannte Ports pro Gerät (SSH, HTTP, VNC...) |
| 3 | Netzwerk-Map | ASCII Baum aller Geräte vom Router aus |
| 4 | Bluetooth Scan | Erkennt BT-Geräte in der Nähe |
| 5 | History (SQLite) | Speichert alle gefundenen Geräte lokal |

---

## Installation

```bash
# 1. Pakete installieren
pkg update && pkg install python git net-tools bluez termux-api -y

# 2. Repo klonen
git clone https://github.com/Sfffff954/scane-for-termux.git

# 3. Rein
cd scane-for-termux

# 4. Starten
python scanner.py
```

---

## Update

```bash
cd scane-for-termux
git pull
python scanner.py
```

---

## Voraussetzungen

| Paket | Installation |
|-------|-------------|
| Termux | [F-Droid](https://f-droid.org/packages/com.termux/) (nicht Play Store!) |
| Termux:API App | [F-Droid](https://f-droid.org/packages/com.termux.api/) |
| termux-api | `pkg install termux-api` |
| bluez | `pkg install bluez` |
| net-tools | `pkg install net-tools` |

---

## Menü

```
╔══════════════════════════════════╗
║      NetScan v2 für Termux       ║
║  WLAN · BT · Ports · Map · Log   ║
╚══════════════════════════════════╝

  1 - WLAN Geräte scannen
  2 - WLAN + Port Scanner
  3 - Netzwerk ASCII Map
  4 - Bluetooth Scan
  5 - Geräte-History (SQLite)
  6 - Alles scannen
  q - Beenden
```

---

## Netzwerk-Map Beispiel

```
[Router/Gateway]
192.168.1.1
      │
      ├── [ICH]   192.168.1.100    meinhandy
      │    MAC: aa:bb:cc:dd:ee:ff
      ├── [Gerät] 192.168.1.101    laptop
      │    MAC: 11:22:33:44:55:66
      └── [Gerät] 192.168.1.102    unbekannt
           MAC: ??:??:??:??:??:??
```

---

## Lizenz

MIT
## upgrade 
cd scane-for-termux
git pull
python scanner.py
