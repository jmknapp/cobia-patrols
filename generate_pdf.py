#!/usr/bin/env python3
"""
Generate PDF version of the Cobia story with proper cartographic maps.
Uses cartopy for real coastlines and ETOPO2022 for bathymetry contours.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import Ellipse
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.colors import HexColor, Color
from io import BytesIO
import os
import re

# ============================================================
# LOAD BATHYMETRY DATA
# ============================================================

def load_bathymetry():
    """Load ETOPO2022 bathymetry data."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bathy_file = os.path.join(script_dir, 'south_china_sea_bathymetry.nc')
    
    if not os.path.exists(bathy_file):
        raise FileNotFoundError(
            f"Bathymetry file not found: {bathy_file}\n"
            "Run download_bathymetry.py first."
        )
    
    ds = xr.open_dataset(bathy_file)
    return ds


# ============================================================
# MAP GENERATION WITH CARTOPY AND REAL BATHYMETRY
# ============================================================

def create_south_china_sea_map():
    """Create an overview map of the South China Sea with real coastlines and bathymetry."""
    
    print("  Loading bathymetry data...")
    ds = load_bathymetry()
    
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # Set map extent [lon_min, lon_max, lat_min, lat_max]
    # Zoomed in to show the Vietnamese coast and attack area more clearly
    ax.set_extent([101, 110, 5, 14], crs=ccrs.PlateCarree())
    
    # Extract bathymetry data for our region
    z = ds['z'].values
    lons = ds['lon'].values
    lats = ds['lat'].values
    
    # Create meshgrid for plotting
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Mask land (positive values) for ocean coloring
    ocean_z = np.ma.masked_where(z > 0, z)
    
    # Custom colormap for ocean depth (light to dark blue)
    ocean_colors = ['#e6f3ff', '#cce7ff', '#b3dbff', '#99cfff', '#80c3ff',
                    '#66b7ff', '#4dabff', '#339fff', '#1a93ff', '#0087ff',
                    '#0077e6', '#0066cc', '#0055b3', '#004499', '#003380']
    ocean_cmap = LinearSegmentedColormap.from_list('ocean', ocean_colors)
    
    # Define depth levels for coloring
    depth_levels = [-5000, -4000, -3000, -2000, -1500, -1000, -500, -200, -100, -50, 0]
    norm = BoundaryNorm(depth_levels, ocean_cmap.N, extend='both')
    
    # Plot ocean bathymetry as filled contours
    cf = ax.contourf(lon_grid, lat_grid, ocean_z, levels=depth_levels,
                     cmap=ocean_cmap, norm=norm, transform=ccrs.PlateCarree(),
                     extend='min', zorder=0)
    
    # Add bathymetry contour LINES at key depths (must be increasing order)
    contour_depths = [-4000, -3000, -2000, -1000, -500, -200, -100, -50, -37]
    contour_colors = ['#666666'] * 8 + ['#996633']  # Gray for most, brown for 37m (20 fathoms)
    contour_widths = [0.5] * 8 + [1.5]  # Thicker for 20-fathom line
    
    # Draw contour lines
    cs = ax.contour(lon_grid, lat_grid, z, levels=contour_depths,
                    colors=contour_colors, linewidths=contour_widths,
                    linestyles='solid', transform=ccrs.PlateCarree(), zorder=2)
    
    # Label key contours
    label_depths = [-200, -1000, -2000, -3000]
    ax.clabel(cs, levels=label_depths, inline=True, fontsize=7, fmt='%dm', 
              colors='#444444')
    
    # Add land with Natural Earth
    land = cfeature.NaturalEarthFeature('physical', 'land', '50m',
                                         facecolor='#d4c4a8', edgecolor='none')
    ax.add_feature(land, zorder=5)
    
    # Add coastlines
    ax.coastlines(resolution='50m', linewidth=0.8, color='#5d4e37', zorder=6)
    
    # Add country borders
    borders = cfeature.NaturalEarthFeature('cultural', 'admin_0_boundary_lines_land', '50m',
                                            facecolor='none', edgecolor='#888888',
                                            linestyle=':')
    ax.add_feature(borders, linewidth=0.5, zorder=6)
    
    text_path_effect = [pe.withStroke(linewidth=3, foreground='white')]
    
    # Key coordinates from the patrol log
    may14_position = (101.53, 9.45)   # 09°27'N, 101°32'E - May 14 depth charging
    initial_contact = (105.33, 8.33)  # 08°20'N, 105°20'E - June 8 radar contact
    attack_position = (105.62, 8.93)  # 08°56'N, 105°37'E - June 8 attack (corrected from log's 108°37'E)
    end_position = (105.65, 7.08)     # 07°05'N, 105°39'E - June 8 withdrawal
    
    # Plot Cobia's track - showing the arc of the fifth patrol
    # From Gulf of Thailand (May 14) eastward to the attack position
    track_lons = [may14_position[0], initial_contact[0], attack_position[0], end_position[0]]
    track_lats = [may14_position[1], initial_contact[1], attack_position[1], end_position[1]]
    ax.plot(track_lons, track_lats, color='#000066', linestyle='--', linewidth=2.5, 
            alpha=0.9, transform=ccrs.PlateCarree(), zorder=10)
    
    # Mark May 14 depth charging position - simple marker
    ax.scatter(*may14_position, s=120, c='#cc6600', marker='X', 
               transform=ccrs.PlateCarree(), zorder=12, 
               edgecolors='#663300', linewidths=1.5)
    ax.text(may14_position[0], may14_position[1]+0.4, 'May 14', fontsize=8, 
            ha='center', color='#804000', fontweight='bold',
            transform=ccrs.PlateCarree(), zorder=20)
    
    # Mark the attack position with a prominent star
    ax.scatter(*attack_position, s=400, c='#cc0000', marker='*', 
               transform=ccrs.PlateCarree(), zorder=15, 
               edgecolors='#660000', linewidths=1.5)
    ax.text(attack_position[0]+0.3, attack_position[1]+0.3, 'ATTACK\nJune 8', fontsize=9, 
            ha='left', color='#990000', fontweight='bold',
            transform=ccrs.PlateCarree(), zorder=20)
    
    # Mark initial contact - simple
    ax.scatter(*initial_contact, s=100, c='#0066cc', marker='o', 
               transform=ccrs.PlateCarree(), zorder=12, 
               edgecolors='#003366', linewidths=1.5)
    ax.text(initial_contact[0]-0.3, initial_contact[1]-0.4, '0310', fontsize=8, 
            ha='right', color='#003366', fontweight='bold',
            transform=ccrs.PlateCarree(), zorder=20)
    
    # Mark end position - simple
    ax.scatter(*end_position, s=100, c='#006600', marker='s', 
               transform=ccrs.PlateCarree(), zorder=12,
               edgecolors='#003300', linewidths=1.5)
    ax.text(end_position[0]+0.3, end_position[1], '0830', fontsize=8, 
            ha='left', color='#003300', fontweight='bold',
            transform=ccrs.PlateCarree(), zorder=20)
    
    # Add place labels - adjusted for zoomed view
    ax.text(107.5, 12, 'VIETNAM', fontsize=12, fontweight='bold', style='italic',
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    ax.text(107.5, 11.3, '(French Indochina, 1945)', fontsize=9, style='italic',
            ha='center', color='#5d5d3d', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    # Mark key ports - potential convoy destinations
    saigon = (106.67, 10.75)  # Saigon (Ho Chi Minh City)
    cap_st_jacques = (107.07, 10.35)  # Cap Saint-Jacques (Vũng Tàu)
    
    ax.scatter(*saigon, s=80, c='#444444', marker='s', transform=ccrs.PlateCarree(), zorder=12)
    ax.text(saigon[0]+0.3, saigon[1]+0.2, 'Saigon', fontsize=9, fontweight='bold',
            color='#333333', transform=ccrs.PlateCarree(), zorder=18)
    
    ax.scatter(*cap_st_jacques, s=60, c='#444444', marker='s', transform=ccrs.PlateCarree(), zorder=12)
    ax.text(cap_st_jacques[0]+0.3, cap_st_jacques[1], 'Cap St-Jacques', fontsize=8,
            color='#333333', transform=ccrs.PlateCarree(), zorder=18)
    
    ax.text(102.5, 8, 'GULF OF\nTHAILAND', fontsize=10, style='italic', 
            ha='center', color='#1a4971', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(108.5, 7, 'SOUTH\nCHINA\nSEA', fontsize=14, style='italic', fontweight='bold',
            ha='center', color='#003366', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(110, 19, 'Hainan', fontsize=10, style='italic', 
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(101.5, 4, 'MALAY\nPENINSULA', fontsize=10, style='italic',
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(113, 5.5, 'BORNEO', fontsize=10, style='italic',
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(101.5, 14, 'THAILAND', fontsize=10, style='italic',
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    ax.text(104.5, 12, 'CAMBODIA', fontsize=9, style='italic',
            ha='center', color='#3d3d29', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                      alpha=0.5, linestyle='--', zorder=7)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}
    
    # Title
    ax.set_title('USS Cobia (SS-245) — Attack of June 8, 1945\nSouth China Sea', 
                 fontsize=14, fontweight='bold', pad=15)
    
    # Simplified legend - just track and depth curve
    legend_elements = [
        plt.Line2D([0], [0], color='#000066', linestyle='--', linewidth=2,
                   label="Cobia's track"),
        plt.Line2D([0], [0], color='#996633', linestyle='-', linewidth=1.5,
                   label='20-fathom curve (37m)'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8,
              framealpha=0.9, edgecolor='gray')
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=180, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()
    ds.close()
    
    return buf


def create_night_scene():
    """Create an artistic rendering of the initial convoy sighting at 0330."""
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set up the dark canvas
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Create gradient sky with STRONG lightning illumination
    # The lightning flash creates a bright glow that backlights the ships
    sky_gradient = np.zeros((200, 200, 3))
    lightning_center_x, lightning_center_y = 140, 140  # Center of lightning glow
    
    for i in range(200):
        for j in range(200):
            # Base sky - darker at top, lighter at horizon
            base_brightness = 0.05 + (i / 200) * 0.15
            
            # Strong lightning glow - radial gradient from lightning position
            dist = np.sqrt((j - lightning_center_x)**2 + ((i - lightning_center_y) * 0.7)**2)
            lightning_glow = max(0, 1.0 - dist / 120) * 0.7
            
            # Strong horizon illumination from lightning flash
            if i > 100:  # Lower part of sky near horizon
                horizon_boost = ((i - 100) / 100) ** 0.5 * 0.5
                # Spread across most of the sky
                horizontal_falloff = max(0, 1 - abs(j - 120) / 150)
                lightning_glow += horizon_boost * horizontal_falloff
            
            brightness = base_brightness + lightning_glow
            brightness = min(brightness, 0.85)  # Cap brightness
            
            # Bluish-white tint for lightning illumination
            sky_gradient[199-i, j] = [
                brightness * 0.8,   # R
                brightness * 0.85,  # G  
                brightness * 1.0    # B
            ]
    
    ax.imshow(sky_gradient, extent=[0, 100, 30, 60], aspect='auto', zorder=0)
    
    # Ocean - with strong lightning reflection
    ocean_gradient = np.zeros((100, 200, 3))
    for i in range(100):
        for j in range(200):
            # Base ocean
            base = 0.06 + (i / 100) * 0.04
            
            # Strong lightning reflection on water - bright band near horizon
            dist_from_horizon = i
            reflection_strength = max(0, 1 - dist_from_horizon / 40) * 0.4
            # Spread reflection across center
            horizontal_spread = max(0, 1 - abs(j - 120) / 120)
            reflection_strength *= horizontal_spread
            
            # Wave texture
            wave = np.sin(j * 0.15 + i * 0.1) * 0.01
            
            brightness = base + reflection_strength + wave
            ocean_gradient[99-i, j] = [brightness * 0.7, brightness * 0.8, brightness * 1.0]
    
    ax.imshow(ocean_gradient, extent=[0, 100, 0, 30], aspect='auto', zorder=0)
    
    # Lightning bolt - bright and forked
    lightning_x = np.array([72, 73.5, 71.5, 73, 70.5, 72, 69.5, 71, 69])
    lightning_y = np.array([58, 53, 50, 46, 43, 39, 36, 33, 30])
    ax.plot(lightning_x, lightning_y, color='#e0e8f8', linewidth=2.5, alpha=0.95, zorder=15)
    ax.plot(lightning_x, lightning_y, color='#ffffff', linewidth=1, alpha=0.8, zorder=16)
    
    # Lightning branch
    branch_x = [71.5, 74, 76, 77]
    branch_y = [50, 47, 45, 43]
    ax.plot(branch_x, branch_y, color='#c0c8e0', linewidth=1.5, alpha=0.7, zorder=15)
    
    # Clouds - brightly illuminated by lightning
    cloud1_x = [55, 60, 67, 74, 80, 85, 82, 76, 70, 64, 58, 53]
    cloud1_y = [50, 53, 52, 54, 52, 49, 47, 46, 47, 46, 47, 49]
    ax.fill(cloud1_x, cloud1_y, color='#5a6580', zorder=2)
    # Cloud bright edge from lightning
    ax.plot(cloud1_x[3:8], cloud1_y[3:8], color='#8090a8', linewidth=2, zorder=2)
    
    cloud2_x = [30, 36, 43, 50, 47, 40, 34, 28]
    cloud2_y = [47, 50, 49, 46, 44, 45, 46, 46]
    ax.fill(cloud2_x, cloud2_y, color='#384055', zorder=2)
    
    # Ship silhouettes - DISTANT (2-3 miles away, ~5000 yards)
    # At this range, a 500-foot ship subtends only ~3 degrees of arc
    # Ships appear as small dark shapes just above the horizon
    
    # Large tanker (500 feet) - center-right, the primary target
    # At 5000 yards, a 500ft ship appears about 3 degrees wide = small on horizon
    tanker1_x = [48, 49, 49.5, 52, 60, 61, 61.5, 61, 60, 52, 49.5, 49, 48]
    tanker1_y = [30, 30.4, 31.2, 31.5, 31.5, 31.2, 30.6, 30.4, 30.15, 30.15, 30.15, 30.1, 30]
    # Superstructure - small bump
    super1_x = [53, 53.3, 53.3, 57, 57, 56.7, 53]
    super1_y = [31.5, 31.8, 32.5, 32.5, 31.8, 31.5, 31.5]
    # Funnel - tiny
    funnel1_x = [54.5, 54.7, 55.8, 56, 54.5]
    funnel1_y = [32.5, 33.2, 33.2, 32.5, 32.5]
    
    # Draw rim light (bright edge) - thin line simulating backlight
    ax.plot(tanker1_x[1:8], tanker1_y[1:8], color='#7090b0', linewidth=1.5, zorder=6)
    ax.plot(super1_x[1:5], super1_y[1:5], color='#7090b0', linewidth=1, zorder=6)
    ax.plot(funnel1_x[1:4], funnel1_y[1:4], color='#7090b0', linewidth=1, zorder=6)
    
    # Draw tanker 1 as black silhouette
    ax.fill(tanker1_x, tanker1_y, color='#000000', zorder=7)
    ax.fill(super1_x, super1_y, color='#000000', zorder=7)
    ax.fill(funnel1_x, funnel1_y, color='#000000', zorder=7)
    # Mast - thin line
    ax.plot([55.2, 55.2], [33.2, 34.5], color='#000000', linewidth=1.2, zorder=8)
    ax.plot([55.2, 55.2], [33.2, 34.5], color='#6080a0', linewidth=0.6, zorder=6)
    
    # Second tanker - further left, similar size (430 feet)
    tanker2_x = [22, 23, 23.5, 26, 33, 34, 34.5, 34, 33, 26, 23.5, 23, 22]
    tanker2_y = [30, 30.35, 31, 31.3, 31.3, 31, 30.5, 30.35, 30.12, 30.12, 30.12, 30.08, 30]
    super2_x = [26, 26.3, 26.3, 30, 30, 29.7, 26]
    super2_y = [31.3, 31.5, 32.1, 32.1, 31.5, 31.3, 31.3]
    
    # Dimmer rim light - further from lightning
    ax.plot(tanker2_x[1:8], tanker2_y[1:8], color='#506070', linewidth=1.2, zorder=5)
    ax.plot(super2_x[1:5], super2_y[1:5], color='#506070', linewidth=0.8, zorder=5)
    
    ax.fill(tanker2_x, tanker2_y, color='#000000', zorder=6)
    ax.fill(super2_x, super2_y, color='#000000', zorder=6)
    ax.plot([28, 28], [32.1, 33], color='#000000', linewidth=1, zorder=6)
    
    # Third ship (coaster, 200 feet) - far right, smallest, closest to lightning
    coaster_x = [76, 76.5, 77, 78.5, 82, 82.5, 83, 82.5, 82, 78.5, 77, 76.5, 76]
    coaster_y = [30, 30.25, 30.7, 30.9, 30.9, 30.7, 30.35, 30.25, 30.1, 30.1, 30.1, 30.05, 30]
    super3_x = [78, 78.2, 78.2, 80.5, 80.5, 80.3, 78]
    super3_y = [30.9, 31.1, 31.5, 31.5, 31.1, 30.9, 30.9]
    
    # Brightest rim - closest to lightning
    ax.plot(coaster_x[1:8], coaster_y[1:8], color='#8098b8', linewidth=1.3, zorder=6)
    ax.plot(super3_x[1:5], super3_y[1:5], color='#8098b8', linewidth=1, zorder=6)
    
    ax.fill(coaster_x, coaster_y, color='#000000', zorder=7)
    ax.fill(super3_x, super3_y, color='#000000', zorder=7)
    
    # Subtle reflections on water - just dark smudges below each ship
    ax.fill([49, 60, 60, 49], [30, 30, 28.5, 28.5], color='#000000', alpha=0.12, zorder=1)
    ax.fill([23, 33, 33, 23], [30, 30, 28.8, 28.8], color='#000000', alpha=0.08, zorder=1)
    ax.fill([77, 82, 82, 77], [30, 30, 28.8, 28.8], color='#000000', alpha=0.1, zorder=1)
    
    # Foreground - Cobia's deck edge with more detail
    deck_x = [0, 5, 12, 18, 25, 28, 25]
    deck_y = [0, 3, 4, 3.5, 2, 0, 0]
    ax.fill(deck_x, deck_y, color='#08080a', zorder=10)
    
    # Deck railing
    for x_pos in [4, 10, 16, 22]:
        height = 3 + np.sin(x_pos * 0.3) * 0.5
        ax.plot([x_pos, x_pos], [height, height + 3], color='#151520', linewidth=2, zorder=11)
    # Railing wire
    ax.plot([4, 10, 16, 22], [6, 7, 6.5, 5.5], color='#151520', linewidth=1, zorder=11)
    
    # Caption
    caption_text = (
        "0330, approx. 2-3 miles distant: \"Barely visible in extreme black night,\n"
        "was a large heavily laden tanker, 500 feet long.\" — Commander Becker"
    )
    ax.text(50, 4, caption_text, ha='center', va='bottom', fontsize=9, 
            style='italic', color='#8090a0',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#0a0a12', 
                     edgecolor='#404050', alpha=0.95))
    
    # Title
    ax.text(50, 57, "The View from Cobia's Deck — Initial Sighting", 
            ha='center', va='bottom', fontsize=11, fontweight='bold',
            color='#9099aa')
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=180, bbox_inches='tight', 
                facecolor='#050508', edgecolor='none')
    buf.seek(0)
    plt.close()
    
    return buf


def create_detail_map():
    """Create a detailed map of the attack sequence with bathymetry."""
    
    print("  Loading bathymetry data for detail map...")
    ds = load_bathymetry()
    
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    # Zoom in on attack area
    ax.set_extent([106.5, 110.5, 7, 10.5], crs=ccrs.PlateCarree())
    
    # Extract bathymetry data
    z = ds['z'].values
    lons = ds['lon'].values
    lats = ds['lat'].values
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Mask land for ocean coloring
    ocean_z = np.ma.masked_where(z > 0, z)
    
    # Ocean colormap
    ocean_colors = ['#e6f3ff', '#cce7ff', '#b3dbff', '#99cfff', '#80c3ff',
                    '#66b7ff', '#4dabff', '#339fff', '#1a93ff', '#0087ff']
    ocean_cmap = LinearSegmentedColormap.from_list('ocean', ocean_colors)
    
    # Depth levels for this zoomed view (shallower focus)
    depth_levels = [-500, -200, -100, -50, -37, -20, -10, 0]
    
    # Plot bathymetry
    cf = ax.contourf(lon_grid, lat_grid, ocean_z, levels=depth_levels,
                     cmap=ocean_cmap, transform=ccrs.PlateCarree(),
                     extend='min', zorder=0)
    
    # Bathymetry contour lines - emphasize the 20-fathom (37m) curve (must be increasing)
    contour_depths = [-200, -100, -50, -37, -20]
    cs = ax.contour(lon_grid, lat_grid, z, levels=contour_depths,
                    colors=['#666666', '#666666', '#666666', '#996633', '#666666'],
                    linewidths=[0.5, 0.5, 0.8, 2.0, 0.5],
                    linestyles='solid', transform=ccrs.PlateCarree(), zorder=2)
    
    # Label the 20-fathom curve prominently
    ax.clabel(cs, levels=[-37], inline=True, fontsize=8, fmt='37m\n(20 fath.)',
              colors='#663300')
    ax.clabel(cs, levels=[-100, -200], inline=True, fontsize=7, fmt='%dm',
              colors='#444444')
    
    # Add land and coastlines
    land = cfeature.NaturalEarthFeature('physical', 'land', '50m',
                                         facecolor='#d4c4a8', edgecolor='none')
    ax.add_feature(land, zorder=5)
    ax.coastlines(resolution='50m', linewidth=1, color='#5d4e37', zorder=6)
    
    text_path_effect = [pe.withStroke(linewidth=3, foreground='white')]
    
    # First tanker position
    tanker1_pos = (108.62, 8.93)
    ax.scatter(*tanker1_pos, s=500, c='#ff6600', marker='s', 
               transform=ccrs.PlateCarree(), zorder=10,
               edgecolors='#cc3300', linewidths=2)
    ax.annotate('TANKER #1\n10,000 tons\n\nTorpedoed 0438\nSank slowly (stern up 20 min)\nCrew abandoned ship\nLifeboats visible', 
                xy=tanker1_pos, xytext=(tanker1_pos[0]+0.5, tanker1_pos[1]+0.45),
                fontsize=8, ha='left', fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#fff8dc', 
                         edgecolor='#ff6600', alpha=0.95),
                zorder=20)
    
    # Second tanker - exploded
    tanker2_pos = (108.45, 8.82)
    ax.scatter(*tanker2_pos, s=500, c='#cc0000', marker='s', 
               transform=ccrs.PlateCarree(), zorder=10,
               edgecolors='#800000', linewidths=2)
    ax.annotate('TANKER #2\n5,000 tons\nAviation gasoline\n\nExploded 0519\n"Most spectacular flash\nI have ever seen"\n—Cdr. Becker', 
                xy=tanker2_pos, xytext=(tanker2_pos[0]-1.65, tanker2_pos[1]-0.65),
                fontsize=8, ha='left', fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffe4e1', 
                         edgecolor='#cc0000', alpha=0.95),
                zorder=20)
    
    # Explosion effect
    explosion_circle = plt.Circle(tanker2_pos, 0.1, transform=ccrs.PlateCarree(),
                                   color='#ff4400', alpha=0.3, zorder=9)
    ax.add_patch(explosion_circle)
    
    # Third target escaped
    escape_start = (108.35, 8.88)
    escape_end = (107.8, 9.35)
    ax.annotate('', xy=escape_end, xytext=escape_start,
                transform=ccrs.PlateCarree(),
                arrowprops=dict(arrowstyle='->', color='#666666', lw=2.5, ls='--'))
    ax.scatter(*escape_start, s=150, c='#888888', marker='D',
               transform=ccrs.PlateCarree(), zorder=10,
               edgecolors='#444444', linewidths=1.5)
    ax.text(107.55, 9.55, 'Third target escaped\ntoward minefield\n(200 ft coaster)', 
            fontsize=8, style='italic', color='#555555', ha='center',
            transform=ccrs.PlateCarree(),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9),
            zorder=20)
    
    # Cobia's position
    cobia_pos = (108.85, 8.75)
    ax.scatter(*cobia_pos, s=300, c='#003399', marker='^', 
               transform=ccrs.PlateCarree(), zorder=12,
               edgecolors='#001a66', linewidths=2)
    ax.annotate('USS COBIA\n(SS-245)', xy=cobia_pos, 
                xytext=(cobia_pos[0]+0.2, cobia_pos[1]-0.4),
                fontsize=10, fontweight='bold', color='#003399',
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='#003399', alpha=0.95),
                zorder=20)
    
    # Lifeboats drifting
    lifeboat_positions = [
        (108.58, 9.08), (108.65, 9.15), (108.52, 9.12), (108.60, 9.22)
    ]
    for pos in lifeboat_positions:
        ax.scatter(*pos, s=50, c='#8b4513', marker='o', 
                   transform=ccrs.PlateCarree(), zorder=11, alpha=0.8)
    
    # Fog/haze
    fog_ellipse = Ellipse((108.58, 9.38), 0.45, 0.35, 
                          transform=ccrs.PlateCarree(),
                          facecolor='#aaaaaa', alpha=0.3, zorder=8)
    ax.add_patch(fog_ellipse)
    ax.text(108.58, 9.65, 'Lifeboats drifting\ninto monsoon fog...', 
            fontsize=9, style='italic', color='#5d4037', ha='center',
            transform=ccrs.PlateCarree(),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85),
            zorder=20)
    
    # Withdrawal track
    withdrawal_lons = [108.85, 108.2, 107.5, 106.8]
    withdrawal_lats = [8.75, 8.3, 7.8, 7.3]
    ax.plot(withdrawal_lons, withdrawal_lats, color='#000066', linestyle='--', 
            linewidth=2.5, alpha=0.8, transform=ccrs.PlateCarree(), zorder=10)
    ax.annotate('Withdrawal to\ndeep water →', 
                xy=(withdrawal_lons[-1], withdrawal_lats[-1]),
                xytext=(withdrawal_lons[-1]+0.2, withdrawal_lats[-1]-0.3),
                fontsize=8, color='#003399', fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9),
                zorder=20)
    
    # Gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                      alpha=0.5, linestyle='--', zorder=7)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 9}
    gl.ylabel_style = {'size': 9}
    
    ax.set_title('Attack Sequence — 0310 to 0830, June 8, 1945', 
                 fontsize=13, fontweight='bold', pad=12)
    
    # Timeline box
    timeline_text = """TIMELINE (local time)
━━━━━━━━━━━━━━━━━━━━━━━━
0310  Radar contact (3 ships)
0330  First target sighted
0410  Four torpedoes fired (duds)
0438  Six torpedoes — 2 hits
0500  First tanker sinks
0510  Second tanker sighted
0518  Three torpedoes fired
0519  EXPLOSION (avgas)
0637  Attack on third target
0644  Last torpedo expended
0830  Crossed 20-fathom curve"""
    
    props = dict(boxstyle='round,pad=0.5', facecolor='#f5f5f5', 
                 edgecolor='#333333', alpha=0.95)
    ax.text(0.02, 0.98, timeline_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', fontfamily='monospace', bbox=props, zorder=25)
    
    # Coast label
    ax.text(109.8, 10, 'Vietnamese\ncoast →', fontsize=8, style='italic',
            ha='center', color='#5d4e37', transform=ccrs.PlateCarree(),
            path_effects=text_path_effect, zorder=18)
    
    # Depth note
    ax.text(107, 7.3, 'Note: Attack occurred in\ndangerously shallow water\n(~50m depth)', 
            fontsize=7, style='italic', ha='left', color='#555555',
            transform=ccrs.PlateCarree(),
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85),
            zorder=18)
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=180, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()
    ds.close()
    
    return buf


# ============================================================
# PDF GENERATION  
# ============================================================

def read_markdown_file(filepath):
    """Read and parse the markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def markdown_to_paragraphs(md_text):
    """Convert markdown text to a list of styled paragraphs for reportlab."""
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=HexColor('#1a1a1a'),
        fontName='Times-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#444444'),
        fontName='Times-Italic'
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=HexColor('#2c3e50'),
        fontName='Times-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        fontName='Times-Roman'
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=6
    )
    
    # Style for blockquote text (used inside the shaded box)
    blockquote_style = ParagraphStyle(
        'BlockQuote',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
        fontName='Courier',
        textColor=HexColor('#333333')
    )
    
    elements = []
    
    lines = md_text.split('\n')
    i = 0
    current_para = []
    blockquote_lines = []
    in_blockquote = False
    
    def flush_blockquote():
        """Create a shaded inset box for blockquote content."""
        if not blockquote_lines:
            return None
        
        # Join all blockquote lines
        quote_text = ' '.join(blockquote_lines)
        quote_para = Paragraph(quote_text, blockquote_style)
        
        # Create a table with the paragraph to add background shading
        table = Table([[quote_para]], colWidths=[6.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), Color(0.93, 0.93, 0.90)),  # Light tan/gray
            ('BOX', (0, 0), (-1, -1), 1, Color(0.7, 0.65, 0.55)),  # Border
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        return table
    
    while i < len(lines):
        line = lines[i]
        
        # Handle blockquotes (lines starting with >)
        if line.strip().startswith('>'):
            # First, flush any pending regular paragraph
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            
            # Extract blockquote content (remove > prefix)
            quote_content = line.strip()[1:].strip()
            blockquote_lines.append(quote_content)
            in_blockquote = True
            i += 1
            continue
        
        # If we were in a blockquote and hit a non-blockquote line, flush it
        if in_blockquote and not line.strip().startswith('>'):
            table = flush_blockquote()
            if table:
                elements.append(Spacer(1, 8))
                elements.append(table)
                elements.append(Spacer(1, 8))
            blockquote_lines = []
            in_blockquote = False
        
        # Skip horizontal rules
        if line.strip() == '---':
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            elements.append(Spacer(1, 12))
            i += 1
            continue
        
        # Main title
        if line.startswith('# ') and not line.startswith('## '):
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            title_text = line[2:].strip()
            elements.append(Paragraph(title_text, title_style))
            i += 1
            continue
        
        # Subtitle (italic line after title)
        if line.startswith('*') and line.endswith('*') and not line.startswith('**'):
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            subtitle_text = line.strip('*').strip()
            elements.append(Paragraph(subtitle_text, subtitle_style))
            i += 1
            continue
        
        # Section headers
        if line.startswith('## '):
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            header_text = line[3:].strip()
            elements.append(Paragraph(header_text, h2_style))
            i += 1
            continue
        
        # Bullet points
        if line.strip().startswith('- '):
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            bullet_text = line.strip()[2:]
            elements.append(Paragraph('• ' + convert_inline_markdown(bullet_text), bullet_style))
            i += 1
            continue
        
        # Empty line = end of paragraph
        if line.strip() == '':
            if current_para:
                text = ' '.join(current_para)
                if text.strip():
                    elements.append(Paragraph(convert_inline_markdown(text), body_style))
                current_para = []
            i += 1
            continue
        
        # Regular text - accumulate for paragraph
        current_para.append(line.strip())
        i += 1
    
    # Don't forget last paragraph
    if current_para:
        text = ' '.join(current_para)
        if text.strip():
            elements.append(Paragraph(convert_inline_markdown(text), body_style))
    
    # Don't forget any trailing blockquote
    if blockquote_lines:
        table = flush_blockquote()
        if table:
            elements.append(Spacer(1, 8))
            elements.append(table)
            elements.append(Spacer(1, 8))
    
    return elements


def convert_inline_markdown(text):
    """Convert inline markdown (bold, italic) to reportlab XML tags."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Italic: *text* -> <i>text</i>  (but not if already processed as bold)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    return text


def create_pdf(output_path, md_filepath):
    """Create the complete PDF document."""
    
    print("Generating maps with cartopy and ETOPO2022 bathymetry...")
    overview_map = create_south_china_sea_map()
    print("  Overview map complete.")
    detail_map = create_detail_map()
    print("  Detail map complete.")
    print("  Generating night scene illustration...")
    night_scene = create_night_scene()
    print("  Night scene complete.")
    
    print("Reading markdown content...")
    md_content = read_markdown_file(md_filepath)
    
    print("Building PDF...")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Build story (content list)
    story = []
    
    # Convert markdown to paragraphs
    content_elements = markdown_to_paragraphs(md_content)
    
    # Insert maps after the Sources section
    map_inserted = False
    for i, elem in enumerate(content_elements):
        story.append(elem)
        
        # After Sources section, insert the maps
        if not map_inserted and isinstance(elem, Paragraph):
            if 'stayed with him for the rest of his life' in elem.text:
                map_inserted = True
                story.append(Spacer(1, 20))
                
                # Add map section
                map_title_style = ParagraphStyle(
                    'MapTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceBefore=12,
                    spaceAfter=8,
                    alignment=TA_CENTER,
                    textColor=HexColor('#2c3e50')
                )
                
                story.append(Paragraph("Maps", map_title_style))
                story.append(Spacer(1, 10))
                
                # Overview map
                story.append(Image(overview_map, width=6.5*inch, height=6.5*inch))
                story.append(Spacer(1, 8))
                
                caption_style = ParagraphStyle(
                    'Caption',
                    parent=styles['Normal'],
                    fontSize=9,
                    alignment=TA_CENTER,
                    textColor=HexColor('#666666'),
                    fontName='Times-Italic'
                )
                story.append(Paragraph(
                    "Figure 1: USS Cobia's track on June 8, 1945. Bathymetry contours from ETOPO 2022. "
                    "The brown line marks the 20-fathom (37m) curve—the critical depth limit mentioned in the patrol log.", 
                    caption_style))
                
                story.append(PageBreak())
                
                # Detail map
                story.append(Image(detail_map, width=6.5*inch, height=5*inch))
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    "Figure 2: The attack sequence showing the two tanker positions, "
                    "the gasoline explosion, the escaping third target, and the lifeboats "
                    "drifting into monsoon fog. Note the shallow water depth at the attack site.", 
                    caption_style))
                
                story.append(PageBreak())
                
                # Night scene illustration
                story.append(Image(night_scene, width=6.5*inch, height=3.9*inch))
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    "Figure 3: Artist's rendering of the initial convoy sighting at 0330. "
                    "In the \"extreme black night,\" the tankers would have been barely visible—"
                    "dark silhouettes against a marginally lighter sky, revealed only in brief "
                    "flashes of monsoon lightning. The view is from Cobia's deck, looking toward "
                    "the horizon where three ships await.", 
                    caption_style))
                
                story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    print(f"PDF created: {output_path}")


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(script_dir, 'cobia_story.md')
    pdf_file = os.path.join(script_dir, 'cobia_story.pdf')
    
    create_pdf(pdf_file, md_file)
