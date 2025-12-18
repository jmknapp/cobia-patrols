-- Torpedo Attack #3, Patrol 1 - July 18, 1944
-- Night radar surface attack on Kiso Maru
-- 4 torpedoes fired, 2 hits, ship sunk

INSERT INTO torpedo_attacks (
    patrol, attack_number, attack_date, attack_time, timezone,
    latitude, longitude,
    latitude_deg, latitude_min, latitude_hemisphere,
    longitude_deg, longitude_min, longitude_hemisphere,
    target_name, target_type, target_tonnage, target_description,
    target_course, target_speed, target_draft, target_range, target_bearing,
    angle_on_bow,
    own_course, own_speed, own_depth,
    attack_type, sea_condition, visibility,
    result, damage_description, pdf_page, remarks
) VALUES (
    1, 3, '1944-07-18', '02:05:00', -9,
    29.200000, 139.166667,
    29, 12, 'N',
    139, 10, 'E',
    'Kiso Maru', 'AK',  4070,
    'Single three island freighter similar to Kiso Maru, Mago 131 ONI 1208-J, with two escorts. Contact made by radar, range 11,000 yards.',
    145, 6.5, 24, 2400, NULL,
    NULL,
    250, 12.8, 0,
    'Radar surface', 'Calm', 'Visibility by starlight, no moon',
    'Sunk', 'Two hits seen, heard, and felt; target soon to sink; pip disappeared from radar. The whole attack from first pip to sinking took less than one hour.',
    30,
    'Torpedo #4 should have hit from all data including spacing of #1 & 2 hits. Never saw wake of this torpedo after firing so believe it sank at firing point.'
);

-- Get the attack ID for the torpedo inserts
SET @attack_id = LAST_INSERT_ID();

-- Four torpedoes fired from forward tubes
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle,
    depth_setting, power_setting,
    mk_torpedo, torpedo_serial,
    mk_exploder, exploder_serial,
    actuation_set, mk_warhead, warhead_serial,
    explosive_type, firing_interval, spread_type,
    hit_miss, erratic, actual_actuation
) VALUES
    (@attack_id, 1, 1, 75, 'P', 0, 6, 'High', '23', '49232', '6-4', '8239', 'Contact', '16-1', '13816', 'Torpex', NULL, 'None', 'Hit', 'No', 'Contact'),
    (@attack_id, 2, 2, 73, 'P', 2, 6, 'High', '23', '49771', '6-4', '2876', 'Contact', '16-1', '12720', 'Torpex', 8, '2° Divergent', 'Hit', 'No', 'Contact'),
    (@attack_id, 3, 3, 77, 'P', 358, 6, 'High', '23', '61663', '6-4', '8320', 'Contact', '16-1', '13820', 'Torpex', 8, '2° Divergent', 'Miss', 'No', NULL),
    (@attack_id, 4, 4, 75, 'P', 0, 6, 'High', '23', '52926', '6-4', '3202', 'Contact', '16-1', '13800', 'Torpex', 8, '2° Divergent', 'Miss', 'Sank', NULL);

