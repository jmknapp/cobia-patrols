-- Sample data: Torpedo Attack #2 from Patrol 1
-- Attack on HIJMS Noshima, 13 July 1944

INSERT INTO torpedo_attacks (
    patrol, attack_number,
    attack_date, attack_time, timezone,
    latitude_deg, latitude_min, latitude_hemisphere,
    longitude_deg, longitude_min, longitude_hemisphere,
    latitude, longitude,
    target_name, target_type, target_tonnage, target_description,
    target_course, target_speed, target_draft, target_range, angle_on_bow,
    own_course, own_speed, own_depth,
    attack_type, sea_condition, visibility, convoy_info,
    result, damage_description,
    pdf_page, remarks
) VALUES (
    1, 2,
    '1944-07-13', '07:28:00', '-9',
    27, 23, 'N',
    140, 33, 'E',
    27.383333, 140.55,
    'HIJMS Noshima', 'AF4', 8751,
    'One stack, well deck, split superstructure, MFM, straight bow naval auxiliary with grey stack and large white "4" painted on stack. Target very heavily laden. Lookouts in whites manning the rail.',
    100, 8, 24, 1100, '1° down',
    333, 3.9, 64,
    'Submerged',
    'Calm and smooth',
    'No wind, no clouds, visibility unlimited',
    'Another ship in column; three escorts, one similar to Corvette, others sampans. One escort plane.',
    'Sunk',
    'First hit heard. Swung scope around and saw target with all of after end obscured by a huge cloud of black smoke. He was already listing to starboard showing a beautiful snowy forecastle deck. Second torpedo hit forward of stack just as scope dipped. Very loud sounds of grinding and tearing metal heard through hull for about four minutes. Bubbling and gurgling noises heard through sound gear. Long rolling explosion - boilers?',
    28, NULL
);

-- Get the attack ID for foreign key
SET @attack_id = LAST_INSERT_ID();

-- Torpedo 1
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle, depth_setting, power_setting,
    spread_type, firing_interval,
    mk_torpedo, torpedo_serial, mk_exploder, exploder_serial,
    actuation_set, mk_warhead, warhead_serial, explosive_type,
    hit_miss, erratic, actual_actuation
) VALUES (
    @attack_id, 1, 1,
    83, 'S', 30, 12, 'High',
    'None', NULL,
    '23', '61858', '6-4', '8530',
    'Contact', '16-1', '13808', 'Torpex',
    'Hit', 'No', 'Contact'
);

-- Torpedo 2
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle, depth_setting, power_setting,
    spread_type, firing_interval,
    mk_torpedo, torpedo_serial, mk_exploder, exploder_serial,
    actuation_set, mk_warhead, warhead_serial, explosive_type,
    hit_miss, erratic, actual_actuation
) VALUES (
    @attack_id, 2, 2,
    88, 'S', 350, 12, 'High',
    '3° Divergent', 8,
    '23', '52828', '6-4', '21893',
    'Contact', '16-1', '13812', 'Torpex',
    'Hit', 'No', 'Contact'
);

-- Torpedo 3
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle, depth_setting, power_setting,
    spread_type, firing_interval,
    mk_torpedo, torpedo_serial, mk_exploder, exploder_serial,
    actuation_set, mk_warhead, warhead_serial, explosive_type,
    hit_miss, erratic, actual_actuation
) VALUES (
    @attack_id, 3, 3,
    84, 'S', 31, 12, 'High',
    '3° Divergent', 8,
    '23', '49859', '6-4', '2987',
    'Contact', '16-1', '13854', 'Torpex',
    'Miss', 'No', NULL
);

