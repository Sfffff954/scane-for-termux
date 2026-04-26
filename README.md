[README.md](https://github.com/user-attachments/files/27101478/README.md)
# 📡 scane-for-termux

WLAN & Bluetooth Gerätescanner für Termux (Android)

---

## Installation

```bash
# 1. Termux pakete installieren
pkg update && pkg install python git net-tools bluez termux-api -y

# 2. Repo klonen
git clone https://github.com/Sfffff954/scane-for-termux.git

# 3. In den Ordner wechseln
cd scane-for-termux

# 4. Starten
python scanner.py
```

---

## Voraussetzungen

| Was | Warum |
|-----|-------|
| [Termux](https://f-droid.org/packages/com.termux/) | Terminal App (aus F-Droid) |
| [Termux:API](https://f-droid.org/packages/com.termux.api/) | Für WLAN AP & Bluetooth Scan |
| `pkg install termux-api` | Termux-seitige API |
| `pkg install bluez` | Für Bluetooth Classic |
| `pkg install net-tools` | Für ARP (MAC-Adressen) |

> ⚠️ Termux aus **F-Droid** installieren, nicht Play Store!

---

## Features

- 🔍 **WLAN Ping Sweep** — alle Geräte im Netz (IP, MAC, Hostname)
- 📶 **WLAN Access Points** — alle sichtbaren Netzwerke mit Signal
- 🔵 **Bluetooth Classic** — via `bluetoothctl`
- 🔵 **Bluetooth via Termux:API** — einfacher auf Android

---

## Update

```bash
cd scane-for-termux
git pull
```

---

## Lizenz

MIT
