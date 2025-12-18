-- Convoy ships for Attack #4, Patrol 1 - Arizona Maru convoy
-- Based on the hand-drawn diagram on page 32a

-- Get the attack_id for P1A4
SET @attack_id = (SELECT id FROM torpedo_attacks WHERE patrol = 1 AND attack_number = 4);

INSERT INTO convoy_ships (
    attack_id, ship_letter, ship_name, ship_type, ship_class, tonnage,
    role, relative_bearing, relative_range, course, speed,
    was_hit, was_sunk, icon_type
) VALUES
    -- A: Arizona Maru - primary target (at origin, all positions relative to this)
    (@attack_id, 'A', 'Arizona Maru', 'AK', 'Arizona Maru Class', 9500,
     'target', 0, 0, 115, 8, TRUE, TRUE, 'cargo'),
    
    -- B: Large AK - starboard side, in line of bearing with A
    -- From diagram: roughly 1000 yards to starboard (bearing ~205° from A, meaning A sees B at 205°)
    (@attack_id, 'B', 'Large AK', 'AK', NULL, NULL,
     'secondary', 115, 1000, 115, 8, FALSE, FALSE, 'cargo'),
    
    -- C: Small AK - port quarter, 1000 tons
    -- From diagram: behind and to port of main formation
    (@attack_id, 'C', 'Small AK', 'AK', NULL, 1000,
     'secondary', 315, 1500, 115, 8, FALSE, FALSE, 'cargo'),
    
    -- D: CHIDORI - ahead, patrolling
    -- Torpedo boat, aggressive anti-sub vessel
    (@attack_id, 'D', 'CHIDORI', 'DE', 'CHIDORI class', 750,
     'escort', 295, 2000, 115, 12, FALSE, FALSE, 'escort'),
    
    -- E: Sampan - port side escort
    (@attack_id, 'E', 'Sampan', 'patrol', NULL, NULL,
     'escort', 25, 800, 115, 6, FALSE, FALSE, 'sampan');

