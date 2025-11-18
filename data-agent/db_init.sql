CREATE TABLE shelters (
    id SERIAL PRIMARY KEY,
    name TEXT,
    address TEXT,
    town TEXT,
    zip TEXT,
    status TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOGRAPHY(POINT, 4326)
);

CREATE TABLE hazards (
    id SERIAL PRIMARY KEY,
    type TEXT,
    severity TEXT,
    geom GEOMETRY(POLYGON, 4326)
);
