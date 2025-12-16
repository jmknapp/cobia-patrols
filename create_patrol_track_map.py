#!/usr/bin/env python3
"""Create a detailed track map of USS Cobia's 5th War Patrol from extracted positions."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import json

# Manually cleaned positions from the patrol report OCR
# Format: (date, lat, lon, note)
positions = [
    ("May 8", 14.80, 120.28, "Departed Subic Bay"),
    ("May 9", 14.80, 120.28, "Alongside Gilmore"),
    ("May 10", 14.77, 115.30, "Transit"),
    ("May 11", 11.87, 112.03, "Transit"),
    ("May 12", 8.93, 106.48, "Transit"),
    ("May 13", 7.47, 104.42, "Entered patrol area"),
    ("May 14", 9.73, 103.98, "DEPTH CHARGING"),
    ("May 15", 9.45, 101.53, "After depth charging"),
    ("May 16", 6.88, 101.95, "Patrol"),
    ("May 17", 8.75, 100.92, "Patrol"),
    ("May 18", 10.53, 100.50, "Patrol"),
    ("May 19", 9.53, 103.32, "Patrol"),
    ("May 20", 9.32, 103.48, "Patrol"),
    ("May 21", 11.37, 102.43, "Patrol"),
    ("May 22", 11.60, 100.12, "Patrol"),
    ("May 23", 10.53, 99.53, "Patrol"),
    ("May 24", 10.08, 101.17, "Patrol"),
    ("May 25", 8.20, 102.82, "Patrol"),
    ("May 26", 8.35, 102.25, "Patrol"),
    ("May 27", 9.68, 102.35, "Patrol"),
    ("May 28", 8.90, 101.40, "Patrol"),
    ("May 29", 10.77, 102.98, "Patrol"),
    ("May 30", 10.27, 99.42, "Patrol"),
    ("May 31", 7.97, 101.05, "Patrol"),
    ("Jun 1", 7.90, 101.10, "Patrol"),
    ("Jun 2", 8.08, 100.98, "Patrol"),
    ("Jun 3", 9.72, 102.52, "Patrol"),
    ("Jun 4", 9.68, 103.20, "Patrol"),
    ("Jun 5", 8.92, 103.08, "Patrol"),
    ("Jun 6", 9.23, 102.77, "Patrol"),
    ("Jun 7", 7.97, 105.00, "Headed for barn"),
    ("Jun 8", 7.08, 105.65, "TANKER ATTACK"),
    ("Jun 9", 1.98, 107.08, "Transit south"),
    ("Jun 10", -2.60, 109.27, "Transit"),
    ("Jun 11", -5.43, 112.40, "Transit"),
    ("Jun 12", -8.08, 115.58, "Transit"),
    ("Jun 13", -12.37, 115.20, "Transit"),
    ("Jun 14", -17.50, 113.83, "Transit"),
    ("Jun 15", -21.63, 115.00, "Onslow"),
    ("Jun 16", -25.18, 112.03, "Transit"),
    ("Jun 17", -29.92, 113.45, "Transit"),
    ("Jun 18", -32.05, 115.75, "Arrived Fremantle"),
]

# Attack position detail
attack_position = (8.93, 108.62)  # June 8 attack at 08°56'N, 108°37'E

# Create the figure
fig = plt.figure(figsize=(14, 16))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent to cover entire patrol
ax.set_extent([95, 125, -35, 20], crs=ccrs.PlateCarree())

# Add map features
ax.add_feature(cfeature.LAND, facecolor='#d4c4a8', zorder=5)
ax.add_feature(cfeature.OCEAN, facecolor='#cce0f0', zorder=0)
ax.coastlines(resolution='50m', linewidth=0.8, color='#5d4e37', zorder=6)
ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, zorder=6)

# Text effects for labels
text_effect = [pe.withStroke(linewidth=3, foreground='white')]

# Extract coordinates
lats = [p[1] for p in positions]
lons = [p[2] for p in positions]

# Plot the track
ax.plot(lons, lats, 'b-', linewidth=2, alpha=0.7, transform=ccrs.PlateCarree(), zorder=10)

# Mark noon positions with small dots
ax.scatter(lons, lats, s=30, c='#003366', marker='o', transform=ccrs.PlateCarree(), zorder=11)

# Special markers for key events
# Departure - Subic Bay
ax.scatter(120.28, 14.80, s=150, c='green', marker='^', transform=ccrs.PlateCarree(), zorder=15,
           edgecolors='darkgreen', linewidths=1.5)
ax.annotate('DEPARTED\nSubic Bay\nMay 8', xy=(120.28, 14.80), xytext=(122, 16),
            fontsize=8, color='darkgreen', fontweight='bold', transform=ccrs.PlateCarree(),
            arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='green', alpha=0.9),
            zorder=20)

# Depth charging - May 14
ax.scatter(103.98, 9.73, s=200, c='#cc6600', marker='X', transform=ccrs.PlateCarree(), zorder=15,
           edgecolors='#663300', linewidths=1.5)
ax.annotate('DEPTH CHARGING\nMay 14\nStuck in mud', xy=(103.98, 9.73), xytext=(100.5, 12),
            fontsize=8, color='#804000', fontweight='bold', transform=ccrs.PlateCarree(),
            arrowprops=dict(arrowstyle='->', color='#804000', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#cc6600', alpha=0.9),
            zorder=20)

# Attack position - June 8
ax.scatter(108.62, 8.93, s=300, c='#cc0000', marker='*', transform=ccrs.PlateCarree(), zorder=15,
           edgecolors='#660000', linewidths=1.5)
ax.annotate('TANKER ATTACK\nJune 8, 1945\n2 tankers sunk', xy=(108.62, 8.93), xytext=(111, 11),
            fontsize=9, color='#990000', fontweight='bold', transform=ccrs.PlateCarree(),
            arrowprops=dict(arrowstyle='->', color='#990000', lw=2),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#cc0000', alpha=0.95),
            zorder=20)

# Arrival - Fremantle
ax.scatter(115.75, -32.05, s=150, c='green', marker='s', transform=ccrs.PlateCarree(), zorder=15,
           edgecolors='darkgreen', linewidths=1.5)
ax.annotate('ARRIVED\nFremantle\nJune 18', xy=(115.75, -32.05), xytext=(118, -30),
            fontsize=8, color='darkgreen', fontweight='bold', transform=ccrs.PlateCarree(),
            arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='green', alpha=0.9),
            zorder=20)

# Add date labels for key positions
date_labels = [
    (120.28, 14.80, "May 8"),
    (112.03, 11.87, "May 11"),
    (104.42, 7.47, "May 13"),
    (101.53, 9.45, "May 15"),
    (99.53, 10.53, "May 23"),
    (105.00, 7.97, "Jun 7"),
    (107.08, 1.98, "Jun 9"),
    (112.40, -5.43, "Jun 11"),
    (115.75, -32.05, "Jun 18"),
]

for lon, lat, label in date_labels:
    ax.text(lon + 0.5, lat - 0.5, label, fontsize=7, color='#333333',
            transform=ccrs.PlateCarree(), path_effects=text_effect, zorder=18)

# Place labels
places = [
    (107, 16, 'VIETNAM\n(French Indochina)', 11),
    (101.5, 14, 'THAILAND', 10),
    (104.5, 12, 'CAMBODIA', 9),
    (102, 5, 'MALAY\nPENINSULA', 9),
    (110, 19, 'Hainan', 9),
    (118, 5, 'BORNEO', 10),
    (108, -3, 'JAVA SEA', 9),
    (122, 12, 'PHILIPPINES', 10),
    (115, -25, 'AUSTRALIA', 12),
    (113, 9, 'SOUTH\nCHINA\nSEA', 14),
    (102, 9, 'GULF OF\nTHAILAND', 9),
]

for lon, lat, name, size in places:
    ax.text(lon, lat, name, fontsize=size, style='italic', ha='center',
            color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_effect, zorder=17)

# Subic Bay label
ax.text(120.5, 15.5, 'Subic Bay', fontsize=8, style='italic',
        transform=ccrs.PlateCarree(), path_effects=text_effect)

# Fremantle label
ax.text(115.5, -33.5, 'Fremantle', fontsize=8, style='italic',
        transform=ccrs.PlateCarree(), path_effects=text_effect)

# Gridlines
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
gl.top_labels = False
gl.right_labels = False
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
gl.xlabel_style = {'size': 9}
gl.ylabel_style = {'size': 9}

# Title
ax.set_title('USS Cobia (SS-245) — Fifth War Patrol Track\nMay 8 – June 18, 1945', 
             fontsize=16, fontweight='bold', pad=15)

# Legend
legend_elements = [
    plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', 
               markersize=12, label='Departure (Subic Bay)'),
    plt.Line2D([0], [0], marker='X', color='w', markerfacecolor='#cc6600', 
               markersize=12, label='May 14 depth charging'),
    plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#cc0000', 
               markersize=15, label='June 8 tanker attack'),
    plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='green', 
               markersize=10, label='Arrival (Fremantle)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#003366',
               markersize=8, label='Daily noon positions'),
    plt.Line2D([0], [0], color='blue', linestyle='-', linewidth=2, label='Patrol track'),
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)

# Stats box
stats_text = """PATROL STATISTICS
Duration: 42 days
Distance: ~6,000 nm
Torpedoes expended: 17
Ships sunk: 2 tankers (15,000 tons)
Crew: ~70 men"""
ax.text(0.02, 0.25, stats_text, transform=ax.transAxes, fontsize=8,
        fontfamily='monospace', verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f5f5f5', edgecolor='gray', alpha=0.95))

plt.tight_layout()
plt.savefig('USS_Cobia_5th_Patrol_Track.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('USS_Cobia_5th_Patrol_Track.pdf', bbox_inches='tight', facecolor='white')
print("Created: USS_Cobia_5th_Patrol_Track.png")
print("Created: USS_Cobia_5th_Patrol_Track.pdf")








