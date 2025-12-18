-- Torpedo Attack Schema for USS Cobia Patrol Reports
-- Run this to create the attack tables

-- Main attack table (one row per attack)
CREATE TABLE IF NOT EXISTS torpedo_attacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patrol INT NOT NULL,
    attack_number INT NOT NULL,  -- Attack #1, #2, etc. within patrol
    
    -- Date/Time/Position
    attack_date DATE NOT NULL,
    attack_time TIME,
    timezone VARCHAR(10),  -- e.g., "-9", "ITEM"
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    latitude_deg INT,
    latitude_min DECIMAL(5,2),
    latitude_hemisphere CHAR(1),
    longitude_deg INT,
    longitude_min DECIMAL(5,2),
    longitude_hemisphere CHAR(1),
    
    -- Target information
    target_name VARCHAR(100),  -- e.g., "HIJMS Noshima"
    target_type VARCHAR(50),   -- e.g., "AF4" (naval auxiliary)
    target_tonnage INT,        -- e.g., 8751
    target_description TEXT,   -- Full description from report
    
    -- Target geometry at firing
    target_course INT,         -- degrees
    target_speed DECIMAL(4,1), -- knots
    target_draft DECIMAL(4,1), -- feet
    target_range INT,          -- yards at firing
    target_bearing INT,        -- degrees from Cobia
    angle_on_bow VARCHAR(20),  -- e.g., "1° down", "80° starboard"
    
    -- Own ship (Cobia) data
    own_course INT,            -- degrees
    own_speed DECIMAL(4,1),    -- knots
    own_depth INT,             -- feet (0 if surfaced)
    
    -- Attack context
    attack_type VARCHAR(50),   -- "Submerged", "Surface", "Night surface"
    sea_condition VARCHAR(100),
    visibility VARCHAR(100),
    convoy_info TEXT,          -- Other ships, escorts, etc.
    
    -- Results
    result VARCHAR(50),        -- "Sunk", "Damaged", "Missed", "Unknown"
    damage_description TEXT,   -- What was observed
    
    -- Metadata
    pdf_page INT,              -- Page in patrol report
    remarks TEXT,
    
    UNIQUE KEY patrol_attack (patrol, attack_number)
);

-- Individual torpedo data (multiple rows per attack)
CREATE TABLE IF NOT EXISTS torpedoes_fired (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_id INT NOT NULL,
    
    -- Tube and sequence
    tube_number INT NOT NULL,  -- 1-10 (forward or aft tubes)
    fire_sequence INT,         -- Order fired (1st, 2nd, 3rd...)
    
    -- Fire control settings
    track_angle INT,           -- degrees
    track_side CHAR(1),        -- 'P' port, 'S' starboard
    gyro_angle INT,            -- degrees
    depth_setting INT,         -- feet
    power_setting VARCHAR(10), -- "High", "Low"
    spread_type VARCHAR(20),   -- "None", "3° Divergent"
    firing_interval INT,       -- seconds since previous torpedo
    
    -- Torpedo specs
    mk_torpedo VARCHAR(10),    -- e.g., "23"
    torpedo_serial VARCHAR(20),
    mk_exploder VARCHAR(10),   -- e.g., "6-4"
    exploder_serial VARCHAR(20),
    actuation_set VARCHAR(20), -- "Contact", "Magnetic"
    mk_warhead VARCHAR(10),    -- e.g., "16-1"
    warhead_serial VARCHAR(20),
    explosive_type VARCHAR(20),-- "Torpex", "TNT"
    
    -- Result
    hit_miss VARCHAR(10),      -- "Hit", "Miss", "Unknown"
    erratic VARCHAR(10),       -- "Yes", "No"
    actual_actuation VARCHAR(20), -- How it actually detonated
    
    FOREIGN KEY (attack_id) REFERENCES torpedo_attacks(id) ON DELETE CASCADE
);

-- Index for quick lookups
CREATE INDEX idx_attacks_patrol ON torpedo_attacks(patrol);
CREATE INDEX idx_attacks_date ON torpedo_attacks(attack_date);
CREATE INDEX idx_torpedoes_attack ON torpedoes_fired(attack_id);

