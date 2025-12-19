#!/usr/bin/env python3
"""
TDC Mark III Torpedo Data Computer Simulator

Simulates the analog fire control computer used on US submarines in WWII.
The Mark III computed firing solutions for torpedo attacks.

This version includes accurate curved trajectory modeling:
- Initial straight run (torpedo exits tube, gyro spins up)
- Curved turn phase (torpedo turns according to gyro setting)
- Final straight run (torpedo travels to intercept)

Usage:
    python tdc_mk3.py --interactive
    python tdc_mk3.py --own-course 281 --own-speed 3 --target-bearing 291 --target-range 1300 
                      --target-course 115 --target-speed 10
    python tdc_mk3.py --own-course 281 --target-bearing 291 --target-range 1300 
                      --target-course 115 --target-speed 10 --plot

References:
- Bureau of Ordnance OP 1631: Torpedo Data Computer Mark III
- Friedman, Norman. "U.S. Submarines Through 1945"
- Wildenberg & Polmar. "Ship Killer: A History of the American Torpedo"
"""

import argparse
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

# Constants
MARK_14_SPEED_HIGH = 46.0  # knots (high speed setting)
MARK_14_SPEED_LOW = 31.5   # knots (low speed setting)
MARK_18_SPEED = 29.0       # knots (electric torpedo)
YARDS_PER_NAUTICAL_MILE = 2025.4
SECONDS_PER_HOUR = 3600

# Torpedo turn characteristics (Mark 14)
INITIAL_RUN_YARDS = 75       # Distance before gyro engages (~50-100 yards)
TURN_RATE_DEG_SEC = 4.0      # Turn rate in degrees per second
# At 46 knots and 4°/sec: turn radius ≈ 370 yards


@dataclass
class TorpedoTrajectory:
    """Detailed torpedo trajectory with all phases"""
    # Phase 1: Initial straight run
    initial_run_distance: float = 0.0      # yards
    initial_run_time: float = 0.0          # seconds
    initial_run_end_x: float = 0.0         # yards from launch
    initial_run_end_y: float = 0.0         # yards from launch
    
    # Phase 2: Turn
    turn_angle: float = 0.0                # degrees (same as gyro angle)
    turn_radius: float = 0.0               # yards
    turn_arc_length: float = 0.0           # yards
    turn_time: float = 0.0                 # seconds
    turn_center_x: float = 0.0             # center of turn circle
    turn_center_y: float = 0.0
    turn_end_x: float = 0.0                # position after turn
    turn_end_y: float = 0.0
    
    # Phase 3: Final straight run
    final_heading: float = 0.0             # degrees
    final_run_distance: float = 0.0        # yards
    final_run_time: float = 0.0            # seconds
    
    # Totals
    total_distance: float = 0.0            # yards
    total_time: float = 0.0                # seconds
    
    # Trajectory points for plotting (list of (x, y) tuples)
    trajectory_points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class TDCInputs:
    """Inputs to the TDC Mark III"""
    own_course: float        # Own ship's heading (degrees, 0-360)
    own_speed: float         # Own ship's speed (knots)
    target_bearing: float    # Bearing to target from own ship (degrees, 0-360)
    target_range: float      # Range to target (yards)
    target_course: float     # Target's heading (degrees, 0-360)
    target_speed: float      # Target's speed (knots)
    torpedo_speed: float = MARK_14_SPEED_HIGH  # Torpedo speed (knots)
    

@dataclass
class TDCSolution:
    """Firing solution output from TDC Mark III"""
    gyro_angle: float           # Gyro angle setting for torpedo (degrees, -180 to +180)
    gyro_angle_360: float       # Gyro angle in 0-360 format
    track_angle: float          # Angle torpedo crosses target track (degrees, 0-180)
    track_side: str             # Port (P) or Starboard (S)
    angle_on_bow: float         # Angle target sees own ship (degrees, 0-180)
    aob_side: str               # Port (P) or Starboard (S)
    torpedo_run: float          # Distance torpedo travels (yards) - simplified
    torpedo_run_time: float     # Time for torpedo to reach target (seconds) - simplified
    lead_angle: float           # Deflection angle (degrees)
    target_bearing_relative: float  # Target bearing relative to own bow
    torpedo_heading: float      # Final torpedo heading (degrees, 0-360)
    valid: bool                 # Whether solution is valid
    message: str                # Status/error message
    
    # Detailed trajectory (curved path)
    trajectory: Optional[TorpedoTrajectory] = None


def normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 range"""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def normalize_signed(angle: float) -> float:
    """Normalize angle to -180 to +180 range"""
    while angle < -180:
        angle += 360
    while angle > 180:
        angle -= 360
    return angle


def heading_to_vector(heading_deg: float) -> Tuple[float, float]:
    """Convert compass heading to unit vector (x=East, y=North)"""
    rad = math.radians(heading_deg)
    return (math.sin(rad), math.cos(rad))


def compute_turn_geometry(
    start_x: float, start_y: float,
    initial_heading: float,
    gyro_angle: float,
    turn_radius: float
) -> Tuple[float, float, float, float, float]:
    """
    Compute the geometry of the torpedo turn.
    
    Returns:
        (turn_center_x, turn_center_y, end_x, end_y, arc_length)
    """
    if abs(gyro_angle) < 0.1:
        # No turn - straight shot
        return (0, 0, start_x, start_y, 0)
    
    # Determine turn direction
    turn_right = gyro_angle > 0  # Positive gyro = starboard turn
    
    # Initial heading vector
    init_rad = math.radians(initial_heading)
    
    # Perpendicular vector to find turn center
    # For right turn: center is 90° clockwise from heading
    # For left turn: center is 90° counter-clockwise from heading
    if turn_right:
        perp_rad = init_rad + math.pi / 2
    else:
        perp_rad = init_rad - math.pi / 2
    
    # Turn center position
    center_x = start_x + turn_radius * math.sin(perp_rad)
    center_y = start_y + turn_radius * math.cos(perp_rad)
    
    # Arc length
    arc_length = abs(math.radians(gyro_angle)) * turn_radius
    
    # Final heading after turn
    final_heading = normalize_angle(initial_heading + gyro_angle)
    
    # End position: rotate around center by gyro_angle
    # Vector from center to start
    rel_x = start_x - center_x
    rel_y = start_y - center_y
    
    # Rotate this vector by gyro_angle
    rot_rad = math.radians(gyro_angle)
    end_rel_x = rel_x * math.cos(rot_rad) - rel_y * math.sin(rot_rad)
    end_rel_y = rel_x * math.sin(rot_rad) + rel_y * math.cos(rot_rad)
    
    end_x = center_x + end_rel_x
    end_y = center_y + end_rel_y
    
    return (center_x, center_y, end_x, end_y, arc_length)


def compute_curved_trajectory(
    own_course: float,
    gyro_angle: float,
    torpedo_speed: float,
    target_x: float,
    target_y: float
) -> TorpedoTrajectory:
    """
    Compute the detailed curved torpedo trajectory.
    
    Phases:
    1. Initial straight run along own_course for INITIAL_RUN_YARDS
    2. Curved turn according to gyro_angle
    3. Final straight run to intercept point
    
    Args:
        own_course: Submarine heading (compass degrees)
        gyro_angle: Gyro angle setting (signed degrees, + = starboard)
        torpedo_speed: Torpedo speed in knots
        target_x, target_y: Intercept point coordinates (yards, x=East, y=North)
    
    Returns:
        TorpedoTrajectory with all phase details
    """
    traj = TorpedoTrajectory()
    torpedo_speed_yps = torpedo_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    
    # Starting point is origin (submarine position)
    start_x, start_y = 0.0, 0.0
    traj.trajectory_points.append((start_x, start_y))
    
    # Phase 1: Initial straight run
    traj.initial_run_distance = INITIAL_RUN_YARDS
    traj.initial_run_time = INITIAL_RUN_YARDS / torpedo_speed_yps
    
    dx, dy = heading_to_vector(own_course)
    traj.initial_run_end_x = start_x + dx * INITIAL_RUN_YARDS
    traj.initial_run_end_y = start_y + dy * INITIAL_RUN_YARDS
    
    # Add points along initial run
    for d in range(0, int(INITIAL_RUN_YARDS), 10):
        traj.trajectory_points.append((start_x + dx * d, start_y + dy * d))
    traj.trajectory_points.append((traj.initial_run_end_x, traj.initial_run_end_y))
    
    # Phase 2: Turn
    traj.turn_angle = gyro_angle
    
    if abs(gyro_angle) < 0.1:
        # No turn needed
        traj.turn_radius = 0
        traj.turn_arc_length = 0
        traj.turn_time = 0
        traj.turn_end_x = traj.initial_run_end_x
        traj.turn_end_y = traj.initial_run_end_y
        traj.turn_center_x = 0
        traj.turn_center_y = 0
    else:
        # Calculate turn radius from speed and turn rate
        # v = ω * r, so r = v / ω
        omega_rad_per_sec = math.radians(TURN_RATE_DEG_SEC)
        traj.turn_radius = torpedo_speed_yps / omega_rad_per_sec
        
        # Compute turn geometry
        (traj.turn_center_x, traj.turn_center_y, 
         traj.turn_end_x, traj.turn_end_y, 
         traj.turn_arc_length) = compute_turn_geometry(
            traj.initial_run_end_x, traj.initial_run_end_y,
            own_course, gyro_angle, traj.turn_radius
        )
        
        traj.turn_time = abs(gyro_angle) / TURN_RATE_DEG_SEC
        
        # Add points along the arc
        num_arc_points = max(10, int(abs(gyro_angle) / 5))  # Point every ~5 degrees
        for i in range(1, num_arc_points + 1):
            fraction = i / num_arc_points
            partial_angle = gyro_angle * fraction
            
            # Vector from center to initial run end
            rel_x = traj.initial_run_end_x - traj.turn_center_x
            rel_y = traj.initial_run_end_y - traj.turn_center_y
            
            # Rotate by partial angle
            rot_rad = math.radians(partial_angle)
            arc_x = traj.turn_center_x + rel_x * math.cos(rot_rad) - rel_y * math.sin(rot_rad)
            arc_y = traj.turn_center_y + rel_x * math.sin(rot_rad) + rel_y * math.cos(rot_rad)
            traj.trajectory_points.append((arc_x, arc_y))
    
    # Phase 3: Final straight run
    traj.final_heading = normalize_angle(own_course + gyro_angle)
    
    # Distance from turn end to target
    dx_to_target = target_x - traj.turn_end_x
    dy_to_target = target_y - traj.turn_end_y
    traj.final_run_distance = math.sqrt(dx_to_target**2 + dy_to_target**2)
    traj.final_run_time = traj.final_run_distance / torpedo_speed_yps
    
    # Add points along final run
    final_dx, final_dy = heading_to_vector(traj.final_heading)
    num_final_points = max(10, int(traj.final_run_distance / 100))
    for i in range(1, num_final_points + 1):
        fraction = i / num_final_points
        d = traj.final_run_distance * fraction
        fx = traj.turn_end_x + final_dx * d
        fy = traj.turn_end_y + final_dy * d
        traj.trajectory_points.append((fx, fy))
    
    # Totals
    traj.total_distance = (traj.initial_run_distance + 
                           traj.turn_arc_length + 
                           traj.final_run_distance)
    traj.total_time = (traj.initial_run_time + 
                       traj.turn_time + 
                       traj.final_run_time)
    
    return traj


def compute_angle_on_bow(own_course: float, target_bearing: float, target_course: float) -> Tuple[float, str]:
    """
    Compute the Angle on Bow (AoB) - the angle at which the target sees our ship.
    
    Returns:
        Tuple of (angle in degrees 0-180, side 'P' or 'S')
    """
    # Bearing FROM target TO us (reciprocal of our bearing to target)
    bearing_to_us = normalize_angle(target_bearing + 180)
    
    # Relative bearing from target's bow
    relative = normalize_signed(bearing_to_us - target_course)
    
    if relative >= 0:
        return abs(relative), 'S'  # We're on target's starboard side
    else:
        return abs(relative), 'P'  # We're on target's port side


def compute_lead_angle(target_speed: float, torpedo_speed: float, track_angle: float) -> float:
    """
    Compute the lead (deflection) angle using the torpedo triangle.
    
    The lead angle is how far ahead of the target we must aim.
    
    sin(lead) / target_speed = sin(track_angle) / torpedo_speed
    
    Returns:
        Lead angle in degrees
    """
    # Convert to radians
    track_rad = math.radians(track_angle)
    
    # Sine rule from torpedo triangle
    sin_lead = (target_speed / torpedo_speed) * math.sin(track_rad)
    
    # Check if solution exists
    if abs(sin_lead) > 1:
        return None  # No solution - target too fast
    
    lead_rad = math.asin(sin_lead)
    return math.degrees(lead_rad)


def compute_torpedo_run(target_range: float, track_angle: float, lead_angle: float) -> float:
    """
    Compute the torpedo run distance.
    
    Using the torpedo triangle geometry.
    """
    track_rad = math.radians(track_angle)
    lead_rad = math.radians(lead_angle)
    
    # Angle at target vertex
    target_vertex = math.pi - track_rad - lead_rad
    
    if lead_rad == 0:
        # Direct shot
        return target_range
    
    # Sine rule
    run = target_range * math.sin(target_vertex) / math.sin(track_rad)
    return abs(run)


def compute_firing_solution(inputs: TDCInputs, compute_trajectory: bool = True) -> TDCSolution:
    """
    Compute the complete TDC firing solution.
    
    This simulates the Mark III's mechanical calculation of:
    1. Angle on Bow
    2. Lead angle (deflection)
    3. Gyro angle (accounting for curved trajectory)
    4. Track angle
    5. Torpedo run time
    
    Args:
        inputs: TDC input parameters
        compute_trajectory: If True, compute detailed curved trajectory
    """
    # Step 1: Compute Angle on Bow
    aob, aob_side = compute_angle_on_bow(
        inputs.own_course, 
        inputs.target_bearing, 
        inputs.target_course
    )
    
    # Step 2: Compute relative bearing to target
    target_bearing_rel = normalize_signed(inputs.target_bearing - inputs.own_course)
    
    # Convert speeds to yards per second
    torpedo_speed_yps = inputs.torpedo_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    target_speed_yps = inputs.target_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    
    # Current target position relative to us (using bearing and range)
    target_bearing_rad = math.radians(inputs.target_bearing)
    current_target_x = inputs.target_range * math.sin(target_bearing_rad)
    current_target_y = inputs.target_range * math.cos(target_bearing_rad)
    
    # Target velocity vector
    target_course_rad = math.radians(inputs.target_course)
    target_vx = target_speed_yps * math.sin(target_course_rad)
    target_vy = target_speed_yps * math.cos(target_course_rad)
    
    # Initial estimate of run time (straight line)
    estimated_run_time = inputs.target_range / torpedo_speed_yps
    
    # Iteratively solve for intercept (accounting for curved path)
    gyro_angle = 0.0
    torpedo_heading = inputs.own_course
    
    for iteration in range(10):
        # Where will target be after run_time?
        target_advance = target_speed_yps * estimated_run_time
        target_dx = target_advance * math.sin(target_course_rad)
        target_dy = target_advance * math.cos(target_course_rad)
        
        future_target_x = current_target_x + target_dx
        future_target_y = current_target_y + target_dy
        
        # Compute trajectory to this intercept point
        if compute_trajectory and iteration > 0:
            # Refine gyro angle accounting for curved path
            traj = compute_curved_trajectory(
                inputs.own_course,
                gyro_angle,
                inputs.torpedo_speed,
                future_target_x,
                future_target_y
            )
            
            # Check if torpedo can actually reach target with this trajectory
            # Adjust intercept point based on actual torpedo travel time
            if traj.total_time > 0:
                estimated_run_time = traj.total_time
        
        # Bearing to intercept point from turn end position
        if compute_trajectory and abs(gyro_angle) > 0.1:
            # Account for displacement during turn
            omega_rad_per_sec = math.radians(TURN_RATE_DEG_SEC)
            turn_radius = torpedo_speed_yps / omega_rad_per_sec
            
            # Approximate turn end position
            init_dx, init_dy = heading_to_vector(inputs.own_course)
            turn_start_x = init_dx * INITIAL_RUN_YARDS
            turn_start_y = init_dy * INITIAL_RUN_YARDS
            
            _, _, turn_end_x, turn_end_y, _ = compute_turn_geometry(
                turn_start_x, turn_start_y,
                inputs.own_course, gyro_angle, turn_radius
            )
            
            # Bearing from turn end to intercept
            dx_to_intercept = future_target_x - turn_end_x
            dy_to_intercept = future_target_y - turn_end_y
            required_heading = math.degrees(math.atan2(dx_to_intercept, dy_to_intercept))
            required_heading = normalize_angle(required_heading)
            
            # New gyro angle needed
            new_gyro = normalize_signed(required_heading - inputs.own_course)
            
            # Blend for stability
            gyro_angle = 0.7 * new_gyro + 0.3 * gyro_angle
        else:
            # Simple straight-line bearing
            intercept_bearing = math.degrees(math.atan2(future_target_x, future_target_y))
            intercept_bearing = normalize_angle(intercept_bearing)
            gyro_angle = normalize_signed(intercept_bearing - inputs.own_course)
        
        torpedo_heading = normalize_angle(inputs.own_course + gyro_angle)
    
    # Final trajectory calculation
    if compute_trajectory:
        trajectory = compute_curved_trajectory(
            inputs.own_course,
            gyro_angle,
            inputs.torpedo_speed,
            future_target_x,
            future_target_y
        )
        torpedo_run = trajectory.total_distance
        torpedo_run_time = trajectory.total_time
    else:
        trajectory = None
        torpedo_run = math.sqrt(future_target_x**2 + future_target_y**2)
        torpedo_run_time = torpedo_run / torpedo_speed_yps
    
    # Track angle = angle between torpedo heading and target course
    track_angle_raw = normalize_signed(torpedo_heading - inputs.target_course + 180)
    track_angle = abs(track_angle_raw)
    if track_angle > 180:
        track_angle = 360 - track_angle
    
    # Determine track side (port or starboard of target)
    if track_angle_raw >= 0:
        track_side = 'S'
    else:
        track_side = 'P'
    
    # Compute lead angle
    lead_angle = compute_lead_angle(inputs.target_speed, inputs.torpedo_speed, track_angle)
    if lead_angle is None:
        return TDCSolution(
            gyro_angle=0, gyro_angle_360=0, track_angle=0, track_side='',
            angle_on_bow=aob, aob_side=aob_side,
            torpedo_run=0, torpedo_run_time=0, lead_angle=0,
            target_bearing_relative=target_bearing_rel,
            torpedo_heading=0, valid=False,
            message="No solution - target speed exceeds torpedo capability at this angle",
            trajectory=None
        )
    
    gyro_angle_360 = normalize_angle(gyro_angle)
    
    return TDCSolution(
        gyro_angle=round(gyro_angle, 1),
        gyro_angle_360=round(gyro_angle_360, 1),
        track_angle=round(track_angle, 1),
        track_side=track_side,
        angle_on_bow=round(aob, 1),
        aob_side=aob_side,
        torpedo_run=round(torpedo_run, 0),
        torpedo_run_time=round(torpedo_run_time, 1),
        lead_angle=round(lead_angle, 1) if lead_angle else 0,
        target_bearing_relative=round(target_bearing_rel, 1),
        torpedo_heading=round(torpedo_heading, 1),
        valid=True,
        message="Solution computed",
        trajectory=trajectory
    )


def print_solution(inputs: TDCInputs, solution: TDCSolution, show_trajectory: bool = True):
    """Pretty print the TDC solution"""
    print("\n" + "=" * 70)
    print("       TDC MARK III - TORPEDO FIRE CONTROL SOLUTION")
    print("=" * 70)
    
    print("\n┌─ INPUTS ─────────────────────────────────────────────────────────┐")
    print(f"│  Own Course:      {inputs.own_course:>6.1f}°                                    │")
    print(f"│  Own Speed:       {inputs.own_speed:>6.1f} knots                                │")
    print(f"│  Target Bearing:  {inputs.target_bearing:>6.1f}°                                    │")
    print(f"│  Target Range:    {inputs.target_range:>6.0f} yards                               │")
    print(f"│  Target Course:   {inputs.target_course:>6.1f}°                                    │")
    print(f"│  Target Speed:    {inputs.target_speed:>6.1f} knots                                │")
    print(f"│  Torpedo Speed:   {inputs.torpedo_speed:>6.1f} knots                                │")
    print("└───────────────────────────────────────────────────────────────────┘")
    
    if not solution.valid:
        print(f"\n⚠️  NO SOLUTION: {solution.message}")
        return
    
    print("\n┌─ FIRING SOLUTION ────────────────────────────────────────────────┐")
    print(f"│  Gyro Angle:      {solution.gyro_angle:>+7.1f}° ({solution.gyro_angle_360:.1f}°)                      │")
    print(f"│  Torpedo Heading: {solution.torpedo_heading:>7.1f}°                               │")
    print(f"│  Lead Angle:      {solution.lead_angle:>7.1f}°                               │")
    print("└───────────────────────────────────────────────────────────────────┘")
    
    print("\n┌─ GEOMETRY ───────────────────────────────────────────────────────┐")
    print(f"│  Angle on Bow:    {solution.angle_on_bow:>7.1f}° {solution.aob_side}                             │")
    print(f"│  Track Angle:     {solution.track_angle:>7.1f}° {solution.track_side}                             │")
    side_text = '(stbd)' if solution.target_bearing_relative > 0 else '(port)'
    print(f"│  Relative Brg:    {solution.target_bearing_relative:>+7.1f}° {side_text}                       │")
    print("└───────────────────────────────────────────────────────────────────┘")
    
    if solution.trajectory and show_trajectory:
        traj = solution.trajectory
        print("\n┌─ TORPEDO TRAJECTORY (CURVED PATH) ───────────────────────────────┐")
        print("│                                                                   │")
        print(f"│  Phase 1: INITIAL RUN (straight, along own course)               │")
        print(f"│           Distance:  {traj.initial_run_distance:>6.0f} yards                          │")
        print(f"│           Time:      {traj.initial_run_time:>6.1f} seconds                         │")
        print("│                                                                   │")
        
        if abs(traj.turn_angle) > 0.1:
            turn_dir = "RIGHT (stbd)" if traj.turn_angle > 0 else "LEFT (port)"
            print(f"│  Phase 2: GYRO TURN ({turn_dir})                          │")
            print(f"│           Turn Angle: {abs(traj.turn_angle):>5.1f}°                               │")
            print(f"│           Turn Radius: {traj.turn_radius:>5.0f} yards                          │")
            print(f"│           Arc Length:  {traj.turn_arc_length:>5.0f} yards                          │")
            print(f"│           Turn Time:   {traj.turn_time:>5.1f} seconds                         │")
        else:
            print(f"│  Phase 2: NO TURN (gyro angle ≈ 0°)                             │")
        
        print("│                                                                   │")
        print(f"│  Phase 3: FINAL RUN (straight, to intercept)                     │")
        print(f"│           Heading:   {traj.final_heading:>6.1f}°                              │")
        print(f"│           Distance:  {traj.final_run_distance:>6.0f} yards                          │")
        print(f"│           Time:      {traj.final_run_time:>6.1f} seconds                         │")
        print("│                                                                   │")
        print("├───────────────────────────────────────────────────────────────────┤")
        print(f"│  TOTAL RUN:         {traj.total_distance:>6.0f} yards                          │")
        print(f"│  TOTAL TIME:        {traj.total_time:>6.1f} seconds                         │")
        min_sec = f"{int(traj.total_time // 60)}:{int(traj.total_time % 60):02d}"
        print(f"│                     {min_sec:>6} (mm:ss)                          │")
        print("└───────────────────────────────────────────────────────────────────┘")
    else:
        print("\n┌─ TORPEDO RUN (SIMPLIFIED) ───────────────────────────────────────┐")
        print(f"│  Run Distance:    {solution.torpedo_run:>7.0f} yards                          │")
        print(f"│  Run Time:        {solution.torpedo_run_time:>7.1f} seconds                        │")
        min_sec = f"{int(solution.torpedo_run_time // 60)}:{int(solution.torpedo_run_time % 60):02d}"
        print(f"│                   {min_sec:>7} (mm:ss)                         │")
        print("└───────────────────────────────────────────────────────────────────┘")
    
    print()


def plot_trajectory(inputs: TDCInputs, solution: TDCSolution):
    """Plot the torpedo trajectory using matplotlib"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
    except ImportError:
        print("Error: matplotlib is required for plotting. Install with: pip install matplotlib")
        return
    
    if not solution.trajectory:
        print("No trajectory data available")
        return
    
    traj = solution.trajectory
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Get trajectory points
    traj_x = [p[0] for p in traj.trajectory_points]
    traj_y = [p[1] for p in traj.trajectory_points]
    
    # Calculate target position and movement
    torpedo_speed_yps = inputs.torpedo_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    target_speed_yps = inputs.target_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    
    target_bearing_rad = math.radians(inputs.target_bearing)
    target_x = inputs.target_range * math.sin(target_bearing_rad)
    target_y = inputs.target_range * math.cos(target_bearing_rad)
    
    # Target movement during torpedo run
    target_course_rad = math.radians(inputs.target_course)
    target_end_x = target_x + target_speed_yps * traj.total_time * math.sin(target_course_rad)
    target_end_y = target_y + target_speed_yps * traj.total_time * math.cos(target_course_rad)
    
    # Plot submarine
    ax.plot(0, 0, 'b^', markersize=15, label='Submarine', zorder=5)
    
    # Plot submarine heading
    sub_dx, sub_dy = heading_to_vector(inputs.own_course)
    ax.arrow(0, 0, sub_dx * 200, sub_dy * 200, head_width=30, head_length=20, 
             fc='blue', ec='blue', alpha=0.5)
    
    # Plot torpedo trajectory
    # Phase 1: Initial run (green)
    phase1_end = min(len(traj_x), int(INITIAL_RUN_YARDS / 10) + 1)
    ax.plot(traj_x[:phase1_end], traj_y[:phase1_end], 'g-', linewidth=2, 
            label='Phase 1: Initial Run')
    
    # Phase 2: Turn (orange)
    if abs(traj.turn_angle) > 0.1:
        turn_points = int(abs(traj.turn_angle) / 5) + 1
        phase2_end = phase1_end + turn_points
        ax.plot(traj_x[phase1_end-1:phase2_end], traj_y[phase1_end-1:phase2_end], 
                'orange', linewidth=2, label='Phase 2: Gyro Turn')
        
        # Draw turn circle (dashed)
        circle = plt.Circle((traj.turn_center_x, traj.turn_center_y), 
                            traj.turn_radius, fill=False, 
                            linestyle='--', color='orange', alpha=0.3)
        ax.add_patch(circle)
    else:
        phase2_end = phase1_end
    
    # Phase 3: Final run (red)
    ax.plot(traj_x[phase2_end-1:], traj_y[phase2_end-1:], 'r-', linewidth=2, 
            label='Phase 3: Final Run')
    
    # Plot target initial position
    ax.plot(target_x, target_y, 'rs', markersize=12, label='Target (initial)')
    
    # Plot target path
    ax.plot([target_x, target_end_x], [target_y, target_end_y], 'r--', 
            linewidth=1.5, alpha=0.7)
    ax.plot(target_end_x, target_end_y, 'r*', markersize=15, label='Target (at impact)')
    
    # Draw target heading arrow
    tgt_dx, tgt_dy = heading_to_vector(inputs.target_course)
    ax.arrow(target_x, target_y, tgt_dx * 200, tgt_dy * 200, 
             head_width=30, head_length=20, fc='red', ec='red', alpha=0.5)
    
    # Mark key points
    ax.plot(traj.initial_run_end_x, traj.initial_run_end_y, 'go', markersize=8)
    ax.plot(traj.turn_end_x, traj.turn_end_y, 'o', color='orange', markersize=8)
    
    # Add annotations
    ax.annotate(f'Gyro: {solution.gyro_angle:+.1f}°', 
                xy=(traj.turn_end_x, traj.turn_end_y),
                xytext=(traj.turn_end_x + 100, traj.turn_end_y + 100),
                fontsize=9, ha='left')
    
    # Set axis properties
    all_x = traj_x + [target_x, target_end_x, 0]
    all_y = traj_y + [target_y, target_end_y, 0]
    
    margin = max(max(all_x) - min(all_x), max(all_y) - min(all_y)) * 0.15
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('East (yards)')
    ax.set_ylabel('North (yards)')
    ax.set_title(f'TDC Mark III - Torpedo Trajectory\n'
                 f'Own Course: {inputs.own_course}° | Target Course: {inputs.target_course}° | '
                 f'Gyro: {solution.gyro_angle:+.1f}°')
    ax.legend(loc='upper left')
    
    # Add text box with stats
    stats_text = (f'Total Run: {traj.total_distance:.0f} yards\n'
                  f'Run Time: {traj.total_time:.1f} sec\n'
                  f'Turn Radius: {traj.turn_radius:.0f} yards\n'
                  f'Track Angle: {solution.track_angle:.1f}° {solution.track_side}')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.98, 0.02, stats_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', horizontalalignment='right', bbox=props)
    
    plt.tight_layout()
    plt.savefig('torpedo_trajectory.png', dpi=150)
    print("\nTrajectory plot saved to: torpedo_trajectory.png")
    plt.show()


def interactive_mode():
    """Run TDC in interactive mode"""
    print("\n" + "=" * 70)
    print("       TDC MARK III - TORPEDO DATA COMPUTER SIMULATOR")
    print("              (with curved trajectory modeling)")
    print("=" * 70)
    print("\nEnter firing problem parameters (or 'q' to quit)\n")
    
    while True:
        try:
            print("-" * 40)
            own_course = input("Own Course (degrees): ")
            if own_course.lower() == 'q':
                break
            own_course = float(own_course)
            
            own_speed = float(input("Own Speed (knots): "))
            target_bearing = float(input("Target Bearing (degrees): "))
            target_range = float(input("Target Range (yards): "))
            target_course = float(input("Target Course (degrees): "))
            target_speed = float(input("Target Speed (knots): "))
            
            torp_speed_input = input(f"Torpedo Speed (knots) [{MARK_14_SPEED_HIGH}]: ")
            torpedo_speed = float(torp_speed_input) if torp_speed_input else MARK_14_SPEED_HIGH
            
            inputs = TDCInputs(
                own_course=own_course,
                own_speed=own_speed,
                target_bearing=target_bearing,
                target_range=target_range,
                target_course=target_course,
                target_speed=target_speed,
                torpedo_speed=torpedo_speed
            )
            
            solution = compute_firing_solution(inputs)
            print_solution(inputs, solution)
            
            plot_input = input("Plot trajectory? (y/n) [n]: ")
            if plot_input.lower() == 'y':
                plot_trajectory(inputs, solution)
            
        except ValueError as e:
            print(f"Invalid input: {e}")
        except KeyboardInterrupt:
            break
    
    print("\nTDC secured.")


def verify_against_historical(patrol: int, attack: int):
    """Verify TDC calculations against historical patrol report data"""
    from db_config import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ta.*, tf.gyro_angle as torp_gyro, tf.track_angle as torp_track, tf.track_side
        FROM torpedo_attacks ta
        JOIN torpedoes_fired tf ON ta.id = tf.attack_id
        WHERE ta.patrol = %s AND ta.attack_number = %s
        ORDER BY tf.fire_sequence
        LIMIT 1
    """, (patrol, attack))
    
    row = cursor.fetchone()
    if not row:
        print(f"Attack P{patrol} #{attack} not found in database")
        return
    
    print(f"\n{'='*70}")
    print(f"VERIFYING P{patrol} ATTACK #{attack}: {row['target_name'] or 'Unknown Target'}")
    print(f"{'='*70}")
    
    # Historical values
    print(f"\nHistorical data from patrol report:")
    print(f"  Own Course: {row['own_course']}°")
    print(f"  Target Course: {row['target_course']}°")
    print(f"  Target Speed: {row['target_speed']} knots")
    print(f"  Range: {row['target_range']} yards")
    print(f"  Recorded Gyro: {row['torp_gyro']}°")
    print(f"  Recorded Track: {row['torp_track']}° {row['track_side']}")
    print(f"  Recorded AoB: {row['angle_on_bow']}")
    
    # We don't have target_bearing in all records, try to compute
    target_bearing = row.get('target_bearing')
    if not target_bearing:
        # Estimate from gyro angle
        target_bearing = normalize_angle(row['own_course'] + row['torp_gyro'])
        print(f"  Target Bearing (estimated): {target_bearing}°")
    else:
        print(f"  Target Bearing: {target_bearing}°")
    
    # Compute solution
    inputs = TDCInputs(
        own_course=float(row['own_course']),
        own_speed=3.0,  # Typical attack speed
        target_bearing=float(target_bearing),
        target_range=float(row['target_range']),
        target_course=float(row['target_course']),
        target_speed=float(row['target_speed']),
        torpedo_speed=MARK_14_SPEED_HIGH
    )
    
    solution = compute_firing_solution(inputs)
    
    print(f"\nTDC Computed Solution (with curved trajectory):")
    print(f"  Gyro Angle: {solution.gyro_angle}° (historical: {row['torp_gyro']}°)")
    print(f"  Track Angle: {solution.track_angle}° {solution.track_side} (historical: {row['torp_track']}° {row['track_side']})")
    print(f"  Angle on Bow: {solution.angle_on_bow}° {solution.aob_side} (historical: {row['angle_on_bow']})")
    
    if solution.trajectory:
        traj = solution.trajectory
        print(f"\n  Trajectory Details:")
        print(f"    Initial Run: {traj.initial_run_distance:.0f} yards ({traj.initial_run_time:.1f} sec)")
        print(f"    Turn Arc: {traj.turn_arc_length:.0f} yards, radius {traj.turn_radius:.0f} yards ({traj.turn_time:.1f} sec)")
        print(f"    Final Run: {traj.final_run_distance:.0f} yards ({traj.final_run_time:.1f} sec)")
        print(f"    Total: {traj.total_distance:.0f} yards ({traj.total_time:.1f} sec = {traj.total_time/60:.1f} min)")
    
    cursor.close()
    conn.close()
    
    return inputs, solution


def main():
    parser = argparse.ArgumentParser(description='TDC Mark III Torpedo Data Computer Simulator')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--own-course', type=float, help='Own ship course (degrees)')
    parser.add_argument('--own-speed', type=float, default=3.0, help='Own ship speed (knots)')
    parser.add_argument('--target-bearing', type=float, help='Target bearing (degrees)')
    parser.add_argument('--target-range', type=float, help='Target range (yards)')
    parser.add_argument('--target-course', type=float, help='Target course (degrees)')
    parser.add_argument('--target-speed', type=float, help='Target speed (knots)')
    parser.add_argument('--torpedo-speed', type=float, default=MARK_14_SPEED_HIGH, help='Torpedo speed (knots)')
    parser.add_argument('--verify', type=str, help='Verify against historical attack (format: P1A4 for Patrol 1 Attack 4)')
    parser.add_argument('--plot', action='store_true', help='Plot the torpedo trajectory')
    
    args = parser.parse_args()
    
    if args.verify:
        # Parse P1A4 format
        import re
        match = re.match(r'P(\d+)A(\d+)', args.verify, re.IGNORECASE)
        if match:
            inputs, solution = verify_against_historical(int(match.group(1)), int(match.group(2)))
            if args.plot and solution and solution.valid:
                plot_trajectory(inputs, solution)
        else:
            print("Invalid verify format. Use P1A4 for Patrol 1 Attack 4")
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    if all([args.own_course is not None, args.target_bearing is not None,
            args.target_range is not None, args.target_course is not None,
            args.target_speed is not None]):
        
        inputs = TDCInputs(
            own_course=args.own_course,
            own_speed=args.own_speed,
            target_bearing=args.target_bearing,
            target_range=args.target_range,
            target_course=args.target_course,
            target_speed=args.target_speed,
            torpedo_speed=args.torpedo_speed
        )
        
        solution = compute_firing_solution(inputs)
        print_solution(inputs, solution)
        
        if args.plot and solution.valid:
            plot_trajectory(inputs, solution)
    else:
        parser.print_help()
        print("\n\nExample - P1 Attack #4 (convoy attack):")
        print("  python tdc_mk3.py --own-course 281 --target-bearing 291 --target-range 1300 \\")
        print("                    --target-course 115 --target-speed 10 --plot")


if __name__ == '__main__':
    main()
