-- Convoy ships table for multi-ship attack visualizations
CREATE TABLE IF NOT EXISTS convoy_ships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_id INT NOT NULL,
    ship_letter CHAR(1),           -- A, B, C, D, E from patrol report diagrams
    ship_name VARCHAR(100),
    ship_type VARCHAR(50),         -- AK, DD, DE, CV, sampan, etc.
    ship_class VARCHAR(100),       -- e.g., CHIDORI class
    tonnage INT,
    role VARCHAR(50),              -- 'target', 'escort', 'secondary'
    relative_bearing INT,          -- bearing from primary target (degrees)
    relative_range INT,            -- range from primary target (yards)
    course INT,                    -- ship's heading
    speed DECIMAL(4,1),            -- ship's speed in knots
    was_hit BOOLEAN DEFAULT FALSE,
    was_sunk BOOLEAN DEFAULT FALSE,
    icon_type VARCHAR(20),         -- 'cargo', 'escort', 'sampan' for visualization
    FOREIGN KEY (attack_id) REFERENCES torpedo_attacks(id) ON DELETE CASCADE
);

CREATE INDEX idx_convoy_attack ON convoy_ships(attack_id);

