-- Create the ClimateData table with initial structure
CREATE TABLE IF NOT EXISTS ClimateData (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    location VARCHAR(100) NOT NULL,
    record_date DATE NOT NULL,
    temperature FLOAT NOT NULL,
    precipitation FLOAT NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_location ON ClimateData(location);
CREATE INDEX idx_record_date ON ClimateData(record_date);
CREATE INDEX idx_temperature ON ClimateData(temperature); 