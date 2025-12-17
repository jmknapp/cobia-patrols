#!/bin/bash
#
# Deploy USS Cobia Patrol Reports web app to production (Apache2)
# Usage: sudo ./deploy_apache.sh
#

set -e  # Exit on error

# Configuration
APP_NAME="cobiapatrols"
DOMAIN="cobiapatrols.com"
APP_DIR="/var/www/html/$APP_NAME"
SOURCE_DIR="/home/jmknapp/cobia/patrolReports"
USER="www-data"
GROUP="www-data"
PYTHON_VERSION="python3"

echo "=== Deploying USS Cobia Patrol Reports (Apache2) ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./deploy_apache.sh)"
    exit 1
fi

# Enable required Apache modules
echo "Enabling Apache modules..."
a2enmod proxy proxy_http rewrite expires headers
systemctl restart apache2

# Create app directory
echo "Creating app directory..."
mkdir -p "$APP_DIR"

# Copy application files
echo "Copying application files..."
rsync -av --exclude='venv' --exclude='.venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' \
    "$SOURCE_DIR/" "$APP_DIR/"

# Copy PDFs if they exist (needed for the viewer)
echo "Copying PDF files..."
for pdf in "$SOURCE_DIR"/*.pdf; do
    [ -f "$pdf" ] && cp -f "$pdf" "$APP_DIR/" && echo "  Copied: $(basename $pdf)"
done

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
    chmod 600 "$APP_DIR/.env"
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
errorlog = "/var/log/cobiapatrols/gunicorn_error.log"
accesslog = "/var/log/cobiapatrols/gunicorn_access.log"
loglevel = "info"
EOF

# Create log directory
mkdir -p /var/log/$APP_NAME
chown -R $USER:$GROUP /var/log/$APP_NAME

# Create systemd service for gunicorn
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

# Install Apache virtual host config
echo "Installing Apache virtual host..."
cp /home/jmknapp/cobia/cobiapatrols.conf /etc/apache2/sites-available/$APP_NAME.conf

# Enable the site
a2ensite $APP_NAME.conf

# Disable default site if it exists (optional)
# a2dissite 000-default.conf

# Reload systemd and start services
echo "Starting services..."
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME
systemctl reload apache2

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "IMPORTANT NEXT STEPS:"
echo ""
echo "1. Edit database credentials:"
echo "   sudo nano $APP_DIR/.env"
echo ""
echo "2. Make sure DNS for $DOMAIN points to this server"
echo ""
echo "3. Install SSL certificate with certbot:"
echo "   sudo certbot --apache -d $DOMAIN -d www.$DOMAIN"
echo ""
echo "Commands:"
echo "  View app status:    sudo systemctl status $APP_NAME"
echo "  View app logs:      sudo journalctl -u $APP_NAME -f"
echo "  View Apache logs:   tail -f /var/log/apache2/${APP_NAME}_*.log"
echo "  Restart app:        sudo systemctl restart $APP_NAME"
echo ""
echo "App should be running at: http://$DOMAIN/"

