# MediVault

## Clean-Slate Installation Manual

MediVault is a Flask-based medical record management system deployed using Gunicorn, Nginx, MySQL, and Ubuntu Linux. The system provides user authentication, session management, and CRUD functionality for managing patient records.

This guide provides a complete clean-slate installation procedure for setting up the MediVault application inside an Ubuntu Linux environment.

---

# Table of Contents

- [System Requirements](#system-requirements)
- [Step 1 – Update Ubuntu Packages](#step-1--update-ubuntu-packages)
- [Step 2 – Install Python and Required Packages](#step-2--install-python-and-required-packages)
- [Step 3 – Install MySQL Server](#step-3--install-mysql-server)
- [Step 4 – Install Nginx](#step-4--install-nginx)
- [Step 5 – Configure Firewall Rules](#step-5--configure-firewall-rules)
- [Step 6 – Create Project Directory](#step-6--create-project-directory)
- [Step 7 – Create Python Virtual Environment](#step-7--create-python-virtual-environment)
- [Step 8 – Install Python Dependencies](#step-8--install-python-dependencies)
- [Step 9 – Create MySQL Database](#step-9--create-mysql-database)
- [Step 10 – Configure Flask Application](#step-10--configure-flask-application)
- [Step 11 – Test Gunicorn](#step-11--test-gunicorn)
- [Step 12 – Configure Nginx Reverse Proxy](#step-12--configure-nginx-reverse-proxy)
- [Step 13 – Configure systemd Service](#step-13--configure-systemd-service)
- [Step 14 – Verify Deployment](#step-14--verify-deployment)
- [Step 15 – Verify Persistence and Recovery](#step-15--verify-persistence-and-recovery)
- [Security Features](#security-features)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Maintenance Commands](#maintenance-commands)

---

# System Requirements

## Hardware Requirements

| Component | Recommended |
|---|---|
| RAM | 2GB or higher |
| Storage | 10GB free space |
| CPU | Dual-core processor |
| Network | Internet connection |

---

## Software Requirements

| Software | Purpose |
|---|---|
| Ubuntu Linux | Operating System |
| Python 3 | Backend Runtime |
| Flask | Web Framework |
| MySQL Server | Database |
| Gunicorn | Production WSGI Server |
| Nginx | Reverse Proxy Web Server |
| systemd | Service Management |

---

# Step 1 – Update Ubuntu Packages

Update all Ubuntu packages.

```bash
sudo apt update
sudo apt upgrade -y
```

---

# Step 2 – Install Python and Required Packages

Install Python, pip, and virtual environment tools.

```bash
sudo apt install python3 python3-pip python3-venv -y
```

Verify installation:

```bash
python3 --version
pip3 --version
```

---

# Step 3 – Install MySQL Server

Install MySQL database server.

```bash
sudo apt install mysql-server -y
```

Start and enable MySQL:

```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

Check MySQL status:

```bash
sudo systemctl status mysql
```

---

# Step 4 – Install Nginx

Install Nginx.

```bash
sudo apt install nginx -y
```

Start and enable Nginx:

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

Check Nginx status:

```bash
sudo systemctl status nginx
```

---

# Step 5 – Configure Firewall Rules

Allow SSH and Nginx traffic using UFW.

```bash
sudo ufw allow 22/tcp
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Check firewall status:

```bash
sudo ufw status
```

Expected output:

```text
22/tcp                     ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
```

---

# Step 6 – Create Project Directory

Create the MediVault project folder.

```bash
mkdir ~/medivault
cd ~/medivault
```

---

# Step 7 – Create Python Virtual Environment

Create the Python virtual environment.

```bash
python3 -m venv venv
```

Activate the environment:

```bash
source venv/bin/activate
```

Expected terminal output:

```text
(venv)
```

---

# Step 8 – Install Python Dependencies

Install required Python packages.

```bash
pip install Flask
pip install flask-cors
pip install Flask-MySQLdb
pip install gunicorn
```

Or install using requirements.txt:

```bash
pip install -r requirements.txt
```

Installed packages include:

| Package | Purpose |
|---|---|
| Flask | Backend Framework |
| Flask-MySQLdb | MySQL Integration |
| flask-cors | Cross-Origin Support |
| gunicorn | Production WSGI Server |
| Werkzeug | Password Hashing |
| Jinja2 | HTML Templating |

---

# Step 9 – Create MySQL Database

Access MySQL:

```bash
sudo mysql
```

Create database:

```sql
CREATE DATABASE medivault;
```

Select database:

```sql
USE medivault;
```

Create users table:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL
);
```

Create patients table:

```sql
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(255),
    age INT,
    diagnosis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Exit MySQL:

```sql
EXIT;
```

---

# Step 10 – Configure Flask Application

Create the Flask backend file:

```text
app.py
```

Example MySQL configuration:

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'medivault'
```

Run Flask application:

```bash
python3 app.py
```

Open browser:

```text
http://SERVER_IP:5000
```

---

# Step 11 – Test Gunicorn

Run Gunicorn manually.

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

Open browser:

```text
http://SERVER_IP:8000
```

---

# Step 12 – Configure Nginx Reverse Proxy

Create Nginx configuration file.

```bash
sudo nano /etc/nginx/sites-available/medivault
```

Add configuration:

```nginx
server {
    listen 80;

    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable configuration:

```bash
sudo ln -s /etc/nginx/sites-available/medivault /etc/nginx/sites-enabled
```

Test configuration:

```bash
sudo nginx -t
```

Restart Nginx:

```bash
sudo systemctl restart nginx
```

---

# Step 13 – Configure systemd Service

Create the service file:

```bash
sudo nano /etc/systemd/system/medivault.service
```

Add configuration:

```ini
[Unit]
Description=MediVault Gunicorn Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/medivault
ExecStart=/home/ubuntu/medivault/venv/bin/gunicorn --bind 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable service:

```bash
sudo systemctl enable medivault
```

Start service:

```bash
sudo systemctl start medivault
```

Check service status:

```bash
sudo systemctl status medivault
```

Expected output:

```text
Active: active (running)
```

---

# Step 14 – Verify Deployment

Open browser:

```text
http://SERVER_IP
```

The MediVault application should now be accessible through Nginx.

---

# Step 15 – Verify Persistence and Recovery

Reboot Ubuntu VM:

```bash
sudo reboot
```

After reboot:

```bash
sudo systemctl status medivault
```

If output shows:

```text
Active: active (running)
```

then persistence and recovery are functioning correctly.

---

# Security Features

The MediVault system includes the following security mechanisms:

- Password hashing using Werkzeug
- Session-based authentication
- UFW firewall protection
- Server-side input validation
- Parameterized SQL queries
- Protected application routes

---

# Troubleshooting Guide

## Gunicorn Fails to Start

Check logs:

```bash
journalctl -u medivault -f
```

---

## Nginx Configuration Error

Test Nginx configuration:

```bash
sudo nginx -t
```

---

## MySQL Connection Error

Verify MySQL service:

```bash
sudo systemctl status mysql
```

---

## Firewall Access Problem

Check firewall rules:

```bash
sudo ufw status
```

---

# Maintenance Commands

## Restart MediVault Service

```bash
sudo systemctl restart medivault
```

## Stop MediVault Service

```bash
sudo systemctl stop medivault
```

## Start MediVault Service

```bash
sudo systemctl start medivault
```

## Check Service Status

```bash
sudo systemctl status medivault
```

---

# Deployment Architecture

```text
User Browser
      ↓
Nginx Reverse Proxy
      ↓
Gunicorn WSGI Server
      ↓
Flask Backend Application
      ↓
MySQL Database
```

---

# Conclusion

The MediVault deployment environment successfully integrates Flask, MySQL, Gunicorn, Nginx, and Ubuntu Linux into a production-style medical record management system. Through the implementation of persistent background services, firewall protection, and secure authentication mechanisms, the system achieves reliable deployment and structured web-based healthcare record management.