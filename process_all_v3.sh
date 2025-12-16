#!/bin/bash
cd /home/jmknapp/cobia
source patrolReports/venv/bin/activate

reports=(
    "cobia_1st_patrol_report:USS_Cobia_1st_Patrol_Report"
    "cobia_2nd_patrol_report:USS_Cobia_2nd_Patrol_Report"  
    "cobia_3rd_patrol_report:USS_Cobia_3rd_Patrol_Report"
    "cobia_4th_patrol_report:USS_Cobia_4th_Patrol_Report"
    "cobia_5th_patrol_report:USS_Cobia_5th_Patrol_Report"
    "cobia_6th_patrol_report:USS_Cobia_6th_Patrol_Report"
)

for entry in "${reports[@]}"; do
    folder="${entry%%:*}"
    name="${entry##*:}"
    echo "=========================================="
    echo "Processing: $folder -> $name"
    echo "=========================================="
    if [ -d "$folder" ]; then
        python ocr_v3.py "$folder" "patrolReports/${name}_v3.pdf"
    else
        echo "Folder $folder not found, skipping"
    fi
done

echo "All done!"
