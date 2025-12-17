#!/bin/bash
#
# Deploy USS Cobia Patrol Reports web app to production
# Usage: sudo ./deploy.sh
#

set -e  # Exit on error

# Configuration
APP_NAME="cobiapatrols"
APP_DIR="/var/www/html/$APP_NAME"
SOURCE_DIR="/home/jmknapp/cobia/patrolReports"
USER="www-data"
GROUP="www-data"
PYTHON_VERSION="python3"

echo "=== Deploying USS Cobia Patrol Reports ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Create app directory
echo "Creating app directory..."
mkdir -p "$APP_DIR"

# Copy application files
echo "Copying application files..."
rsync -av --exclude='venv' --exclude='.venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' \
    "$SOURCE_DIR/" "$APP_DIR/"

# Copy PDFs if they exist (needed for the viewer)
if [ -d "$SOURCE_DIR" ]; then
    echo "Copying PDF files..."
    cp -f "$SOURCE_DIR"/*.pdf "$APP_DIR/" 2>/dev/null || echo "No PDFs to copy"
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
cd "$APP_DIR"
$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file (you'll need to edit this with actual credentials)
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating .env template..."
    cat > "$APP_DIR/.env" << 'EOF'
DB_HOST=localhost
DB_USER=jmknapp
DB_PASSWORD=CHANGE_ME
DB_NAME=cobia
EOF
    echo "WARNING: Edit $APP_DIR/.env with your database credentials!"
fi

# Create gunicorn config
echo "Creating gunicorn configuration..."
cat > "$APP_DIR/gunicorn.conf.py" << 'EOF'
import multiprocessing

bind = "127.0.0.1:5012"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/var/log/cobiapatrols/error.log"
accesslog = "/var/log/cobiapatrols/access.log"
loglevel = "info"
EOF

# Create log directory
mkdir -p /var/log/$APP_NAME
chown -R $USER:$GROUP /var/log/$APP_NAME

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=USS Cobia Patrol Reports Web App
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set ownership
echo "Setting file ownership..."
chown -R $USER:$GROUP "$APP_DIR"

# Create nginx config
echo "Creating nginx configuration..."
cat > /etc/nginx/sites-available/$APP_NAME << 'EOF'
server {
    listen 80;
    server_name _;  # Change to your domain

    location / {
        proxy_pass http://127.0.0.1:5012;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /var/www/html/cobiapatrols/static;
        expires 1d;
    }

    # Increase max upload size for PDFs if needed
    client_max_body_size 500M;
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/

# Reload systemd and start services
echo "Starting services..."
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME
systemctl reload nginx

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "IMPORTANT: Edit $APP_DIR/.env with your database credentials"
echo ""
echo "Commands:"
echo "  View status:  sudo systemctl status $APP_NAME"
echo "  View logs:    sudo journalctl -u $APP_NAME -f"
echo "  Restart:      sudo systemctl restart $APP_NAME"
echo ""
echo "App should be running at: http://localhost/"

