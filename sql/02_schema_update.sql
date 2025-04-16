-- Add humidity column to ClimateData table
ALTER TABLE ClimateData
ADD COLUMN humidity FLOAT NOT NULL AFTER precipitation;

-- Create index for humidity
CREATE INDEX idx_humidity ON ClimateData(humidity); 