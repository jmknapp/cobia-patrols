-- Torpedo Attack #2, Patrol 1 - HIJMS Noshima
-- USS Cobia (SS-245), 13 July 1944

-- Insert the main attack record
INSERT INTO torpedo_attacks (
    patrol, attack_number,
    attack_date, attack_time, timezone,
    latitude_deg, latitude_min, latitude_hemisphere,
    longitude_deg, longitude_min, longitude_hemisphere,
    latitude, longitude,
    target_name, target_type, target_tonnage, target_description,
    target_course, target_speed, target_range,
    angle_on_bow,
    own_course, own_speed, own_depth,
    attack_type, convoy_info,
    result, damage_description,
    remarks
) VALUES (
    1, 2,  -- Patrol 1, Attack #2
    '1944-07-13', '07:28:00', 'I',  -- ITEM time zone
    27, 23.0, 'N',  -- 27°23'N
    140, 33.0, 'E', -- 140°33'E
    27.383333, 140.550000,  -- Decimal degrees
    'HIJMS Noshima', 'AF4', 8751, 'Naval Auxiliary (Provisions Storeship)',
    100, 8.0, 1100,  -- Target: course 100°, speed 8 knots, range 1100 yds
    'Big starboard',  -- Angle on bow from narrative
    333, 3.9, 64,  -- Cobia: course 333°, speed 3.9 kts, depth 64 ft
    'Submerged',
    'Two large AFs with three escorts - two similar to PC boats, one sampan',
    'Sunk',
    'Huge cloud of black smoke, listing to starboard showing snowy forecastle deck. Second torpedo hit forward of stack. Loud sounds of grinding and tearing metal. Bubbling and gurgling noises through sound gear. Long rolling explosion - boilers?',
    'Yeoman typed gyro 350 for tube 2, should be 035 (confirmed by track angle pattern)'
);

-- Get the attack ID for the torpedo records
SET @attack_id = LAST_INSERT_ID();

-- Insert torpedo #1 (Tube 1)
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle,
    spread_type, firing_interval,
    mk_torpedo, depth_setting,
    hit_miss
) VALUES (
    @attack_id, 1, 1,
    83, 'S', 30,  -- Track 83°S, Gyro 030°
    'None', 0,    -- First torpedo, no interval
    '18', 10,     -- Mk 18 electric, 10ft depth
    'Hit'
);

-- Insert torpedo #2 (Tube 2)
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle,
    spread_type, firing_interval,
    mk_torpedo, depth_setting,
    hit_miss
) VALUES (
    @attack_id, 2, 2,
    88, 'S', 35,  -- Track 88°S, Gyro 035° (corrected from 350°)
    'None', 8,    -- ~8 second interval
    '18', 10,
    'Hit'
);

-- Insert torpedo #3 (Tube 3)
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle,
    spread_type, firing_interval,
    mk_torpedo, depth_setting,
    hit_miss
) VALUES (
    @attack_id, 3, 3,
    84, 'S', 31,  -- Track 84°S, Gyro 031°
    '3° Divergent', 8,  -- 3° divergent spread
    '18', 10,
    'Miss'
);

SELECT 'Attack data inserted successfully!' AS status;
SELECT * FROM torpedo_attacks WHERE patrol = 1 AND attack_number = 2;
SELECT * FROM torpedoes_fired WHERE attack_id = @attack_id;

