# TATA - Creative Writing Evaluation System

## Project Overview

TATA - Creative Writing Evaluation System is a Django-based platform that uses AI to professionally evaluate creative writing submissions. The system currently follows the metric configuration defined in the project (metrics.py) and provides per-item scoring and professional commentary for each submission based on four core evaluation metrics.

## Key Features

### 📝 Evaluation
- Four core evaluation metrics: The system uses the 4 metrics defined in metrics.py (for example: hook appeal, character authenticity, core idea direction, escalation of conflict).  
- Intelligent analysis: AI-based professional literary evaluation (scores required on a 1–10 scale).  
- Detailed feedback: Each metric returns a 1–10 score plus a concise explanation.  
- Front-end compatibility: The front-end reserves 10 slots to remain compatible with historical structure; undefined or unscored metric slots are shown as 0 (e.g., 8/7/7/8/0/0/0/0/0/0).  
- User grouping: Supports writer groups A-1, A-2, B-1, B-2.

### 🎯 User Interface
- Simple submission form: User-friendly text submission interface.  
- Real-time evaluation: Submissions automatically call the AI for evaluation and return structured results.  
- Results display: Clear evaluation result pages. Score color mapping is compressed to the 0–40 range on the front end (the front-end color scale treats 0–40 as the full color range; unscored items show 0).  
- Data export: Supports downloading evaluation results (CSV/export).

## Architecture

- Backend framework: Django 4.x  
- Database: SQLite3  
- AI API: OpenAI API (supports custom API base)  
- Frontend: Bootstrap 5 + custom CSS  
- Deployment: systemd service + autostart on boot

## Quick Deployment

### 1. Environment Preparation

System requirements:
- Ubuntu 18.04+ / CentOS 7+ / Debian 9+  
- Python 3.8+  
- Network access (for AI API calls)

Install dependencies:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install system tools
sudo apt install git curl wget -y
```

### 2. Project Deployment

Clone the project:
```bash
cd /home/your_username/projects
git clone <your-repo-url>
cd bench/Django
```

Install Python dependencies:
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install django langchain-openai python-dotenv
```

Configure environment variables:
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=your_api_base_url_here
OPENAI_MODEL=gpt-4o
EOF
```

Initialize the database:
```bash
# Run migrations
python manage.py migrate

# Create superuser
python create_superuser.py
```

### 3. Service Installation

One-step service install:
```bash
# Install and start service
sudo ./manage_service.sh install
```

Manual install (optional):
```bash
# Make scripts executable
chmod +x start_service.py start_production.py

# Install service
sudo bash install_service.sh
```

### 4. Access the Application

Once the service is running, access:
- Main app: http://your_server_ip:8003/  
- Admin: http://your_server_ip:8003/admin/  
- Management: http://your_server_ip:8003/management/

Default admin account:
- Username: admin  
- Password: admin123

## Service Management

Basic commands:
```bash
# Check service status
sudo systemctl status django-evaluation

# Start service
sudo systemctl start django-evaluation

# Stop service
sudo systemctl stop django-evaluation

# Restart service
sudo systemctl restart django-evaluation

# Follow service logs
sudo journalctl -u django-evaluation -f

# Show recent logs
sudo journalctl -u django-evaluation -n 50
```

Using management scripts:
```bash
# List available commands
./manage_service.sh

# Check status
./manage_service.sh status

# Show live logs
./manage_service.sh logs

# Restart service
sudo ./manage_service.sh restart

# Stop service
sudo ./manage_service.sh stop

# Uninstall service
sudo ./manage_service.sh uninstall
```

Autostart on boot:
```bash
# Enable autostart
sudo systemctl enable django-evaluation

# Disable autostart
sudo systemctl disable django-evaluation

# Check autostart status
sudo systemctl is-enabled django-evaluation
```

## Configuration

### Port configuration
- Default port: 8003  
- Change the port by editing the port number in start_service.py

### Firewall rules
```bash
# Ubuntu/Debian
sudo ufw allow 8003
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --reload
```

### API configuration
Configure AI API settings in the .env file:
```bash
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base
OPENAI_MODEL=gpt-4o
```

## Troubleshooting

### Common issues

1. Service fails to start
```bash
# View recent errors
sudo journalctl -u django-evaluation -n 20

# Check port usage
sudo netstat -tulpn | grep :8003

# Test start manually
cd /path/to/project
python start_service.py
```

2. API calls fail
- Verify .env API configuration  
- Confirm network connectivity  
- Check logs for detailed errors

3. Permission problems
```bash
# Change file owner
sudo chown -R your_username:your_username /path/to/project

# Check service file permissions
ls -la /etc/systemd/system/django-evaluation.service
```

4. Database issues
```bash
# Re-run migrations
python manage.py migrate

# Check database file permissions
ls -la db.sqlite3
```

### Debug mode

Enable verbose logging by setting DEBUG = True in settings.py (development only).

Run manually:
```bash
# Development server
python manage.py runserver 0.0.0.0:8003

# View detailed output
python start_service.py
```

## Backups

### Regular backups
```bash
# Backup database
cp db.sqlite3 backup/db_$(date +%Y%m%d_%H%M%S).sqlite3

# Backup evaluation results
tar -czf backup/evaluation_results_$(date +%Y%m%d).tar.gz evaluation_results/

# Backup config
cp .env backup/env_backup_$(date +%Y%m%d).txt
```

### Restore data
```bash
# Stop service
sudo systemctl stop django-evaluation

# Restore database
cp backup/db_backup.sqlite3 db.sqlite3

# Start service
sudo systemctl start django-evaluation
```

## Updates & Maintenance

### Update code
```bash
# Stop service
sudo systemctl stop django-evaluation

# Pull latest code
git pull origin main

# Run migrations if needed
python manage.py migrate

# Restart service
sudo systemctl start django-evaluation
```

### Monitoring recommendations
- Regularly check service status  
- Monitor disk usage  
- Backup important data frequently  
- Inspect system logs

## Support

### Log locations
- System logs: sudo journalctl -u django-evaluation  
- Django logs: check the log files configured by the application

### Performance monitoring
```bash
# Check process resource usage
top -p $(pgrep -f django-evaluation)

# Check port connections
sudo ss -tulpn | grep :8003

---
