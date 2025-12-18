-- Torpedo Attack #1, Patrol 1 - July 9, 1944
-- Failed attack on CM (cargo ship) escorted by Fubuki-class DD near Iwo Jima
-- Kate bomber damaged TDC just before firing

INSERT INTO torpedo_attacks (
    patrol, attack_number, attack_date, attack_time, timezone,
    latitude, longitude,
    latitude_deg, latitude_min, latitude_hemisphere,
    longitude_deg, longitude_min, longitude_hemisphere,
    target_name, target_type, target_description,
    target_course, target_speed, target_draft, target_range, target_bearing,
    angle_on_bow,
    own_course, own_speed, own_depth,
    attack_type, sea_condition, visibility,
    result, damage_description, pdf_page, remarks
) VALUES (
    1, 1, '1944-07-09', '08:20:00', -9,
    24.866667, 141.300000,
    24, 52, 'N',
    141, 18, 'E',
    NULL, 'CM',
    'One CM similar attached sketch led by one FUBUKI class DD escort. Ships in line of bearing about 1,000 yards apart, with Kate air escort standing toward Iwo Jima from north west.',
    100, 19, 10, 1200, NULL,
    'Large port',
    180, 2, 63,
    'Submerged', 'Glassy calm', 'Unlimited visibility, about 70% clouds and little or no wind',
    'Miss', 'No damage. Torpedo fired with malfunctioning TDC after bomb damaged gyro low speed transmitter.',
    25,
    'Just prior to firing, Jap plane dropped bomb which blew fuses on the gyro low speed transmitter and caused the TDC and steering repeater to spin wildly. Torpedo was fired at this time, so gyro is only approximate. CM turned toward at 20 knots, range 900 yards and closing fast. Went deep to 300 feet rigging for depth charge.'
);

-- Get the attack ID for the torpedo insert
SET @attack_id = LAST_INSERT_ID();

-- Only one torpedo fired in this attack
INSERT INTO torpedoes_fired (
    attack_id, tube_number, fire_sequence,
    track_angle, track_side, gyro_angle,
    depth_setting, power_setting,
    mk_torpedo, torpedo_serial,
    mk_exploder, exploder_serial,
    actuation_set, mk_warhead, warhead_serial,
    explosive_type, hit_miss, erratic, actual_actuation
) VALUES (
    @attack_id, 1, 1,
    129, 'P', 331,
    61, 'High',
    '23', '61830',
    '6-7', '21820',
    'Contact', '16-1', '13767',
    'Torpex', 'Miss', 'No', 'None'
);

