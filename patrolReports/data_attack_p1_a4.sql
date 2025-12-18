-- Torpedo Attack #4, Patrol 1 - July 18, 1944
-- "Down the throat" attack on Arizona Maru convoy
-- 10 torpedoes fired (6 forward, 4 aft), 4 hits, ship sunk
-- Same day as Attack #3!

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
    1, 4, '1944-07-18', '07:00:00', -9,
    28.716667, 139.400000,
    28, 43, 'N',
    139, 24, 'E',
    'Arizona Maru Class', 'AK', 9500,
    'Arizona Maru Class (DC) Mago 174 ONI 208J with one large AK on line of bearing, escorted by one CHIDORI ahead, small escort on port side and 1,000 ton AK on starboard side.',
    115, 8, 28, 900, NULL,
    '4° port',
    281, 2.8, 64,
    'Submerged periscope', 'Calm', 'Intermittent rain squalls and low clouds, visibility 30 miles between squalls',
    'Sunk', 'Four hits seen and heard. Two at port side amidships and two in starboard quarter at screws. Target was listing when torpedoes hit in stern. Prolonged breaking up noises heard for about 10 minutes through hull. SHARK attacked same convoy next morning with only one large AK remaining.',
    31,
    'Down the throat attack - fired 6 forward then swung to fire 4 aft. Tubes 4,5,6 probably ran under target. Target manned bow gun and was firing wildly. Received 21 depth charges.'
);

-- Get the attack ID for the torpedo inserts
SET @attack_id = LAST_INSERT_ID();

-- 10 torpedoes fired: 6 forward (Mk 23), 4 aft (Mk 18-1)
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
    -- Forward tubes (Mk 23 torpedoes) - "down the throat"
    (@attack_id, 1, 1, 5, 'P', 9, 12, 'High', '23', '53009', '6-4', '2373', 'Contact', '16-1', '13833', 'Torpex', NULL, 'None', 'Hit', 'No', 'Contact'),
    (@attack_id, 2, 2, 5, 'T', 9, 12, 'High', '23', '49250', '6-4', '8005', 'Contact', '16-1', '13789', 'Torpex', 8, '½° Divg.', 'Hit', 'No', 'Contact'),
    (@attack_id, 3, 3, 5, 'P', 10, 12, 'High', '23', '52939', '6-4', '3847', 'Contact', '16-1', '12729', 'Torpex', 8, '½° Divg.', 'Miss', 'No', NULL),
    (@attack_id, 4, 4, 5, 'P', 9, 12, 'High', '23', '49404', '6-4', '3284', 'Contact', '16-1', '13790', 'Torpex', 13, '½° Divg.', 'Miss', 'No', NULL),
    (@attack_id, 5, 5, 5, 'P', 9, 12, 'High', '23', '26847', '6-4', '1790', 'Contact', '16-1', '10288', 'Torpex', 14, '½° Divg.', 'Miss', 'No', NULL),
    (@attack_id, 6, 6, 5, 'P', 10, 12, 'High', '23', '53208', '6-4', '168', 'Contact', '16-1', '3925', 'Torpex', 19, '½° Divg.', 'Miss', 'No', NULL),
    -- Aft tubes (Mk 18-1 torpedoes) - stern shot after swinging
    (@attack_id, 7, 7, 144, 'S', 223, 12, 'High', '18-1', '55242', '8-5', '8294', 'Contact', '18-1', '1462', 'Torpex', NULL, '0', 'Miss', 'No', NULL),
    (@attack_id, 8, 8, 150, 'S', 229, 12, 'High', '18-1', '54956', '8-5', '8220', 'Contact', '18-1', '1863', 'Torpex', 10, '4R', 'Hit', 'No', 'Contact'),
    (@attack_id, 9, 9, 148, 'S', 227, 12, 'High', '18-1', '55095', '8-5', '7970', 'Contact', '18-1', '2202', 'Torpex', 13, '0', 'Miss', 'No', NULL),
    (@attack_id, 10, 10, 154, 'S', 233, 12, 'High', '18-1', '54366', '8-5', '8044', 'Contact', '18-1', '1776', 'Torpex', 12, '4R', 'Hit', 'No', 'Contact');

