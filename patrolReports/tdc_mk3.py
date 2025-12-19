#!/usr/bin/env python3
"""
TDC Mark III Torpedo Data Computer Simulator

Simulates the analog fire control computer used on US submarines in WWII.
The Mark III computed firing solutions for torpedo attacks.

Usage:
    python tdc_mk3.py --interactive
    python tdc_mk3.py --own-course 281 --own-speed 3 --target-bearing 291 --target-range 1300 
                      --target-course 115 --target-speed 10

References:
- Bureau of Ordnance OP 1631: Torpedo Data Computer Mark III
- Friedman, Norman. "U.S. Submarines Through 1945"
"""

import argparse
import math
from dataclasses import dataclass
from typing import Optional, Tuple

# Constants
MARK_14_SPEED_HIGH = 46.0  # knots (high speed setting)
MARK_14_SPEED_LOW = 31.5   # knots (low speed setting)
MARK_18_SPEED = 29.0       # knots (electric torpedo)
YARDS_PER_NAUTICAL_MILE = 2025.4
SECONDS_PER_HOUR = 3600


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
    torpedo_run: float          # Distance torpedo travels (yards)
    torpedo_run_time: float     # Time for torpedo to reach target (seconds)
    lead_angle: float           # Deflection angle (degrees)
    target_bearing_relative: float  # Target bearing relative to own bow
    torpedo_heading: float      # Final torpedo heading (degrees, 0-360)
    valid: bool                 # Whether solution is valid
    message: str                # Status/error message


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
    # The torpedo run can be approximated for small angles as:
    # run ≈ range / cos(lead_angle)
    # More precisely, using sine rule:
    # run / sin(180 - track - lead) = range / sin(lead)
    
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


def compute_firing_solution(inputs: TDCInputs) -> TDCSolution:
    """
    Compute the complete TDC firing solution.
    
    This simulates the Mark III's mechanical calculation of:
    1. Angle on Bow
    2. Lead angle (deflection)
    3. Gyro angle
    4. Track angle
    5. Torpedo run time
    """
    # Step 1: Compute Angle on Bow
    aob, aob_side = compute_angle_on_bow(
        inputs.own_course, 
        inputs.target_bearing, 
        inputs.target_course
    )
    
    # Step 2: Compute relative bearing to target
    target_bearing_rel = normalize_signed(inputs.target_bearing - inputs.own_course)
    
    # Step 3: Determine track angle from geometry
    # The track angle is the angle between torpedo path and target path
    # For the torpedo to hit, we need to solve the intercept problem
    
    # Initial estimate: track angle based on relative geometry
    # This is iteratively refined in the real TDC
    
    # The torpedo heading after gyro turn
    # We want to find the gyro angle that results in an intercept
    
    # Simplified approach: compute the bearing to the intercept point
    # The intercept point is where target will be when torpedo arrives
    
    # Time for torpedo to cover the range (initial estimate)
    torpedo_speed_yps = inputs.torpedo_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    target_speed_yps = inputs.target_speed * YARDS_PER_NAUTICAL_MILE / SECONDS_PER_HOUR
    
    estimated_run_time = inputs.target_range / torpedo_speed_yps
    
    # Where will target be after run_time?
    target_advance = target_speed_yps * estimated_run_time
    
    # Target's displacement vector
    target_course_rad = math.radians(inputs.target_course)
    target_dx = target_advance * math.sin(target_course_rad)
    target_dy = target_advance * math.cos(target_course_rad)
    
    # Current target position relative to us (using bearing and range)
    target_bearing_rad = math.radians(inputs.target_bearing)
    current_target_x = inputs.target_range * math.sin(target_bearing_rad)
    current_target_y = inputs.target_range * math.cos(target_bearing_rad)
    
    # Future target position
    future_target_x = current_target_x + target_dx
    future_target_y = current_target_y + target_dy
    
    # Bearing to intercept point
    intercept_bearing = math.degrees(math.atan2(future_target_x, future_target_y))
    intercept_bearing = normalize_angle(intercept_bearing)
    
    # Distance to intercept point
    intercept_range = math.sqrt(future_target_x**2 + future_target_y**2)
    
    # Gyro angle = intercept_bearing - own_course
    gyro_angle = normalize_signed(intercept_bearing - inputs.own_course)
    gyro_angle_360 = normalize_angle(gyro_angle)
    
    # Torpedo heading
    torpedo_heading = normalize_angle(inputs.own_course + gyro_angle)
    
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
            message="No solution - target speed exceeds torpedo capability at this angle"
        )
    
    # Refined torpedo run calculation
    torpedo_run = compute_torpedo_run(inputs.target_range, track_angle, lead_angle)
    torpedo_run_time = torpedo_run / torpedo_speed_yps
    
    # Iterate to refine solution (simulating TDC's continuous tracking)
    for _ in range(3):
        # Recalculate with refined run time
        target_advance = target_speed_yps * torpedo_run_time
        target_dx = target_advance * math.sin(target_course_rad)
        target_dy = target_advance * math.cos(target_course_rad)
        
        future_target_x = current_target_x + target_dx
        future_target_y = current_target_y + target_dy
        
        intercept_bearing = math.degrees(math.atan2(future_target_x, future_target_y))
        intercept_bearing = normalize_angle(intercept_bearing)
        intercept_range = math.sqrt(future_target_x**2 + future_target_y**2)
        
        gyro_angle = normalize_signed(intercept_bearing - inputs.own_course)
        torpedo_heading = normalize_angle(inputs.own_course + gyro_angle)
        
        track_angle_raw = normalize_signed(torpedo_heading - inputs.target_course + 180)
        track_angle = abs(track_angle_raw)
        if track_angle > 180:
            track_angle = 360 - track_angle
        
        lead_angle = compute_lead_angle(inputs.target_speed, inputs.torpedo_speed, track_angle)
        if lead_angle:
            torpedo_run = compute_torpedo_run(inputs.target_range, track_angle, lead_angle)
            torpedo_run_time = torpedo_run / torpedo_speed_yps
    
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
        message="Solution computed"
    )


def print_solution(inputs: TDCInputs, solution: TDCSolution):
    """Pretty print the TDC solution"""
    print("\n" + "=" * 60)
    print("    TDC MARK III - TORPEDO FIRE CONTROL SOLUTION")
    print("=" * 60)
    
    print("\n┌─ INPUTS ─────────────────────────────────────────────────┐")
    print(f"│  Own Course:      {inputs.own_course:>6.1f}°                            │")
    print(f"│  Own Speed:       {inputs.own_speed:>6.1f} knots                        │")
    print(f"│  Target Bearing:  {inputs.target_bearing:>6.1f}°                            │")
    print(f"│  Target Range:    {inputs.target_range:>6.0f} yards                       │")
    print(f"│  Target Course:   {inputs.target_course:>6.1f}°                            │")
    print(f"│  Target Speed:    {inputs.target_speed:>6.1f} knots                        │")
    print(f"│  Torpedo Speed:   {inputs.torpedo_speed:>6.1f} knots                        │")
    print("└──────────────────────────────────────────────────────────┘")
    
    if not solution.valid:
        print(f"\n⚠️  NO SOLUTION: {solution.message}")
        return
    
    print("\n┌─ FIRING SOLUTION ────────────────────────────────────────┐")
    print(f"│  Gyro Angle:      {solution.gyro_angle:>+7.1f}° ({solution.gyro_angle_360:.1f}°)                  │")
    print(f"│  Torpedo Heading: {solution.torpedo_heading:>7.1f}°                           │")
    print(f"│  Lead Angle:      {solution.lead_angle:>7.1f}°                           │")
    print("└──────────────────────────────────────────────────────────┘")
    
    print("\n┌─ GEOMETRY ───────────────────────────────────────────────┐")
    print(f"│  Angle on Bow:    {solution.angle_on_bow:>7.1f}° {solution.aob_side}                         │")
    print(f"│  Track Angle:     {solution.track_angle:>7.1f}° {solution.track_side}                         │")
    print(f"│  Relative Brg:    {solution.target_bearing_relative:>+7.1f}° {'(stbd)' if solution.target_bearing_relative > 0 else '(port)'}                   │")
    print("└──────────────────────────────────────────────────────────┘")
    
    print("\n┌─ TORPEDO RUN ────────────────────────────────────────────┐")
    print(f"│  Run Distance:    {solution.torpedo_run:>7.0f} yards                      │")
    print(f"│  Run Time:        {solution.torpedo_run_time:>7.1f} seconds                    │")
    min_sec = f"{int(solution.torpedo_run_time // 60)}:{int(solution.torpedo_run_time % 60):02d}"
    print(f"│                   {min_sec:>7} (mm:ss)                     │")
    print("└──────────────────────────────────────────────────────────┘")
    print()


def interactive_mode():
    """Run TDC in interactive mode"""
    print("\n" + "=" * 60)
    print("    TDC MARK III - TORPEDO DATA COMPUTER SIMULATOR")
    print("=" * 60)
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
    
    print(f"\n{'='*60}")
    print(f"VERIFYING P{patrol} ATTACK #{attack}: {row['target_name'] or 'Unknown Target'}")
    print(f"{'='*60}")
    
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
    
    print(f"\nTDC Computed Solution:")
    print(f"  Gyro Angle: {solution.gyro_angle}° (historical: {row['torp_gyro']}°)")
    print(f"  Track Angle: {solution.track_angle}° {solution.track_side} (historical: {row['torp_track']}° {row['track_side']})")
    print(f"  Angle on Bow: {solution.angle_on_bow}° {solution.aob_side} (historical: {row['angle_on_bow']})")
    print(f"  Torpedo Run: {solution.torpedo_run} yards")
    print(f"  Run Time: {solution.torpedo_run_time:.1f} sec ({solution.torpedo_run_time/60:.1f} min)")
    
    cursor.close()
    conn.close()


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
    
    args = parser.parse_args()
    
    if args.verify:
        # Parse P1A4 format
        import re
        match = re.match(r'P(\d+)A(\d+)', args.verify, re.IGNORECASE)
        if match:
            verify_against_historical(int(match.group(1)), int(match.group(2)))
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
    else:
        parser.print_help()
        print("\n\nExample - P1 Attack #4 (convoy attack):")
        print("  python tdc_mk3.py --own-course 281 --target-bearing 291 --target-range 1300 \\")
        print("                    --target-course 115 --target-speed 10")


if __name__ == '__main__':
    main()

