# 🖥️ ServerOS: The Ultimate Pi Zero 2 W Command Center

**A lightweight, modular, and mobile-first server dashboard designed for the Raspberry Pi Zero 2 W.**

ServerOS transforms your Raspberry Pi into a powerful portable command center. Engineered to run efficiently on 512MB of RAM, it provides a high-fidelity glassmorphic interface to manage your homelab, education, and daily utilities from any device, anywhere in the world.

---

## ✨ Features at a Glance

*   **🚀 Instant Auto-Discovery**: Modular architecture allows you to add features by simply dropping a folder into `/apps`.
*   **📟 Stateful Web Terminal**: A full bash shell in your browser with directory tracking (`cd` works!).
*   **🧪 Chem Suite Pro**: A comprehensive chemistry assistant with experiment generators, Year 10 ion databases, and smart revision quizzes.
*   **🛰️ Phone Beacon**: Real-time GPS tracking that syncs your mobile location to the dashboard's live map.
*   **📂 DropShare**: Drag-and-drop file transfers directly from your phone to a connected USB drive.
*   **🎨 Theme Engine**: Instant UI switching between **Midnight**, **Glassic**, and **Cyberpunk** engineered with CSS variables.
*   **🌡️ Resource Guard**: Automated browser notifications for system health (High Temp/Low Storage).
*   **🛠️ App Smith**: Create your own dashboard icons and web-links visually without touching code.
*   **📡 Dual-Network Logic**: Seamless switching between Local Hotspot, Home Wi-Fi, and Global Tailscale access.

---

## 🚀 Complete Setup Guide

### 1. Hardware Requirements
*   Raspberry Pi Zero 2 W (recommended) or any Linux/macOS server.
*   microSD Card (16GB+ recommended).
*   USB Power Supply.
*   *Optional*: External USB Drive (for DropShare).

### 2. Initial Installation
Clone the repository and run the automated "All-in-One" installer.

```bash
# Clone the repository
git clone https://github.com/ithig124-hub/ServerOS.git
cd ServerOS

# Make the setup script executable
chmod +x setup.sh

# Run the installer (this handles system tools, Python deps, and tailscale)
sudo ./setup.sh
```

### 3. Connection Modes

| Mode | Address | Use Case |
|---|---|---|
| **Local Network** | `http://serveros.local:5000` | Home Wi-Fi connection. |
| **Hotspot Mode** | `http://10.42.0.1:5000` | Direct connection to Pi's Wi-Fi. |
| **Remote Mode** | `http://<tailscale-ip>:5000` | Access from 5G/Global internet. |

#### **Setting up the Hotspot**
To make your Pi broadcast its own Wi-Fi (SSID: `ServerOS`, Pass: `SeRVEROS`):
```bash
sudo nmcli device wifi hotspot ssid ServerOS password SeRVEROS
```

---

## 📱 Built-in Application Guide

### 🧪 Chem Suite
The crown jewel of ServerOS. Includes:
*   **Experiment Gen**: Structured school-level lab procedures.
*   **Ions DB**: Year 10 reference for Cations and Anions with charge info.
*   **Revision Mode**: Active recall system with scores and streaks.
*   **Formula Panel**: Quick reference for n=m/M and c=n/V.

### 📂 DropShare
Stop worrying about phone storage while traveling.
*   Plug a USB drive into your Pi.
*   Open DropShare on your phone.
*   Select "Upload" or drag files into the zone.
*   Files are saved instantly to the physical USB drive.

### 📟 Web Terminal
Run updates, check logs, or manage system services without an SSH client.
*   Full support for standard bash commands.
*   Current Working Directory (CWD) persistence across commands.

### 🚀 Speed Checker
Track your network health.
*   Runs real-world speed tests.
*   Saves a 24-hour history graph of your Download/Upload speeds.

---

## 🛠️ System Maintenance

### **Auto-Start on Boot**
ServerOS is configured to start automatically. You can manage the service using:
```bash
sudo systemctl status severos   # Check if running
sudo systemctl restart severos  # Restart the dashboard
```

### **One-Click Updates**
Open the **Power Control** app on your dashboard and tap **"One-Click Update"**. This will:
1.  Perform a `git pull` from origin.
2.  Update all Python requirements.
3.  Prepare the system for a refresh.

### **Manual Backups**
Your recipes, notes, and logs live in the `/data"folder. To backup:
```bash
zip -r serveros_backup_$(date +%F).zip data/
```

---

## 👨‍💻 Developer Guide: Adding Apps
Want to add a new tool? It's simple:
1.  Create `apps/my-app/manifest.json`.
2.  Add an icon, color, and name.
3.  (Optional) Add a `routes.py` for backend logic.
4.  Restart the server—your app is now live!

---

## 📄 License
MIT License. Built with ❤️ for the Raspberry Pi community by Ithiel.
---

## 🔒 Local HTTPS Setup (Recommended)

Since ServerOS runs as a local dashboard, it uses plain `http` by default. If your browser is forcing `https` and causing a "Secure Connection" error, you have two options:

### 1. Disable HTTPS-Only Mode
Open your dashboard in an **Incognito/Private window**, or check your browser settings to disable "HTTPS-Only Mode" for `serveros.local`.

### 2. Set up an Nginx Reverse Proxy (Advanced)
To get a real padlock and enable secure features (like Geolocation or Camera), you can set up Nginx on your Pi:

```bash
# 1. Install Nginx
sudo apt install nginx -y

# 2. Create a self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt

# 3. Configure Nginx
sudo nano /etc/nginx/sites-available/serveros
```

**Paste this config:**
```nginx
server {
    listen 443 ssl;
    server_name serveros.local;

    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 4. Enable and restart
sudo ln -s /etc/nginx/sites-available/serveros /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```
---
