-- Schema for narrative page index
-- Maps patrol report pages to their starting date/time

CREATE TABLE IF NOT EXISTS narrative_page_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patrol INT NOT NULL,
    page INT NOT NULL,
    observation_date DATE NOT NULL,
    observation_time VARCHAR(4),  -- Time as HHMM string (e.g., "0823", "1326")
    UNIQUE KEY unique_patrol_page (patrol, page),
    INDEX idx_patrol (patrol),
    INDEX idx_date (observation_date)
);

