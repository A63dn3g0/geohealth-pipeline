# Example PostGIS schema for GeoHealth LGA Project
CREATE EXTENSION IF NOT EXISTS postgis;

-- LGA table
CREATE TABLE IF NOT EXISTS lga (
    lga_code VARCHAR PRIMARY KEY,
    lga_name VARCHAR,
    geometry geometry(MultiPolygon, 4326)
);

-- PHN table
CREATE TABLE IF NOT EXISTS phn (
    phn_code VARCHAR PRIMARY KEY,
    phn_name VARCHAR,
    geometry geometry(MultiPolygon, 4326)
);

-- Metrics table
CREATE TABLE IF NOT EXISTS lga_metrics (
    lga_code VARCHAR REFERENCES lga(lga_code),
    year INTEGER,
    population INTEGER,
    mh_any_12m_count INTEGER,
    aod_treatment_count INTEGER,
    mh_funding_total NUMERIC,
    aod_funding_total NUMERIC,
    PRIMARY KEY (lga_code, year)
);

-- Crosswalk table
CREATE TABLE IF NOT EXISTS lga_phn_crosswalk (
    lga_code VARCHAR REFERENCES lga(lga_code),
    phn_code VARCHAR REFERENCES phn(phn_code),
    area_weight DOUBLE PRECISION,
    pop_weight DOUBLE PRECISION,
    PRIMARY KEY (lga_code, phn_code)
);
