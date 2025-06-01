-- CREATE:listings
CREATE TABLE listings (
    listing_id BIGINT PRIMARY KEY,
    listing_type TEXT,
    -- COL:len_description
    len_description INTEGER,
    -- COL:num_photo
    num_photo INTEGER,
    active BOOLEAN DEFAULT TRUE,
    link TEXT,
    -- COL:phone_number
    phone_number TEXT
);   

-- CREATE:listing_features
CREATE TABLE listing_features (
    listing_id BIGINT REFERENCES listings(listing_id),
    floor INTEGER,
    num_rooms INTEGER,
    area NUMERIC(6, 2),
    elevator BOOLEAN
);

-- CREATE:location
CREATE TABLE location (
    listing_id BIGINT REFERENCES listings(listing_id),
    street TEXT,
    estate TEXT,
    district TEXT,
    city TEXT,
    province TEXT
);

-- CREATE:building_features
CREATE TABLE building_features (
    listing_id BIGINT REFERENCES listings(listing_id),
    building_material TEXT,
    building_type TEXT,
    building_year INTEGER,
    finish_level TEXT,
    heating TEXT,
    windows_type TEXT
);

-- CREATE:price_history
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    listing_id BIGINT REFERENCES listings(listing_id),
    scraped_at DATE,
    price NUMERIC(6, 2),
    rent NUMERIC(6, 2),
    deposit NUMERIC(6, 2)
);

-- CREATE:listing_stats
CREATE TABLE listing_stats (
    id SERIAL PRIMARY KEY,
    listing_id BIGINT REFERENCES listings(listing_id),
    scraped_at DATE,
    views INTEGER,
    likes INTEGER
);

-- CREATE:listing_equipment
CREATE TABLE listing_equipment (
    listing_id BIGINT REFERENCES listings(listing_id),
    value TEXT
);

-- CREATE:listing_security
CREATE TABLE listing_security (
    listing_id BIGINT REFERENCES listings(listing_id),
    value TEXT
);

-- CREATE:listing_additional
CREATE TABLE listing_additional (
    listing_id BIGINT REFERENCES listings(listing_id),
    value TEXT
);

-- CREATE:listing_media
CREATE TABLE listing_media (
    listing_id BIGINT REFERENCES listings(listing_id),
    value TEXT
);