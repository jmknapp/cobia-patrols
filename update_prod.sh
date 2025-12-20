#!/bin/bash
#
# Update USS Cobia Patrol Reports web app on production server
# Usage: sudo ./update_prod.sh
#

set -e  # Exit on error

# Configuration
APP_NAME="cobiapatrols"
APP_DIR="/var/www/html/$APP_NAME"
SOURCE_DIR="/home/jmknapp/cobia/patrolReports"

echo "=== Updating USS Cobia Patrol Reports ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./update_prod.sh)"
    exit 1
fi

# Stop the service
echo "Stopping $APP_NAME service..."
systemctl stop $APP_NAME

# Backup .env if it exists
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" /tmp/$APP_NAME.env.bak
fi

# Copy updated application files
echo "Copying updated files..."
rsync -av --exclude='venv' --exclude='.venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' --exclude='gunicorn.conf.py' \
    "$SOURCE_DIR/" "$APP_DIR/"

# Copy PDFs if they exist
echo "Copying PDF files..."
for pdf in "$SOURCE_DIR"/*.pdf; do
    [ -f "$pdf" ] && cp -f "$pdf" "$APP_DIR/" && echo "  Copied: $(basename $pdf)"
done

# Copy TDC simulator
echo "Copying TDC simulator..."
cp -r "$SOURCE_DIR/tdc_simulator" "$APP_DIR/"

# Restore .env
if [ -f /tmp/$APP_NAME.env.bak ]; then
    cp /tmp/$APP_NAME.env.bak "$APP_DIR/.env"
fi

# Update dependencies
echo "Updating Python dependencies..."
cd "$APP_DIR"
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Regenerate the patrol map
echo "Regenerating patrol map..."
source venv/bin/activate
python generate_patrol_map.py
deactivate

# Fix ownership
chown -R www-data:www-data "$APP_DIR"

# Restart service
echo "Restarting $APP_NAME service..."
systemctl start $APP_NAME

echo ""
echo "=== Update Complete ==="
echo ""
echo "Check status: sudo systemctl status $APP_NAME"
