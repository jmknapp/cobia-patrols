#!/bin/bash
# Quick update script for attack_demo.html during development

sudo cp /home/jmknapp/cobia/patrolReports/static/attack_demo.html /var/www/html/cobiapatrols/static/attack_demo.html
sudo chown www-data:www-data /var/www/html/cobiapatrols/static/attack_demo.html

echo "Updated attack_demo.html on production"

