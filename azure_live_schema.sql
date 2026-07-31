CREATE TABLE live_stations (
    station_id NVARCHAR(100) NOT NULL,
    station_uri NVARCHAR(500) NULL,
    station_name NVARCHAR(255) NOT NULL,
    standard_name NVARCHAR(255) NULL,
    longitude FLOAT NULL,
    latitude FLOAT NULL,

    CONSTRAINT pk_live_stations PRIMARY KEY (station_id)
);

CREATE TABLE live_vehicles (
    vehicle_id NVARCHAR(100) NOT NULL,
    vehicle_uri NVARCHAR(500) NULL,
    vehicle_name NVARCHAR(255) NULL,
    vehicle_shortname NVARCHAR(100) NULL,
    vehicle_number NVARCHAR(50) NULL,
    vehicle_type NVARCHAR(50) NULL,

    CONSTRAINT pk_live_vehicles PRIMARY KEY (vehicle_id)
);

CREATE TABLE liveboard_records (
    record_id INT IDENTITY(1,1) NOT NULL,

    snapshot_time DATETIME2 NOT NULL,

    queried_station_id NVARCHAR(100) NOT NULL,
    destination_station_id NVARCHAR(100) NOT NULL,
    vehicle_id NVARCHAR(100) NOT NULL,

    departure_api_id NVARCHAR(50) NULL,
    scheduled_time DATETIME2 NOT NULL,
    delay_seconds INT NOT NULL,

    platform NVARCHAR(50) NULL,
    platform_is_normal BIT NULL,

    is_canceled BIT NOT NULL,
    has_left BIT NOT NULL,
    is_extra BIT NOT NULL,

    occupancy NVARCHAR(50) NULL,
    departure_connection NVARCHAR(500) NULL,

    CONSTRAINT pk_liveboard_records PRIMARY KEY (record_id),

    CONSTRAINT fk_liveboard_queried_station
        FOREIGN KEY (queried_station_id)
        REFERENCES live_stations(station_id),

    CONSTRAINT fk_liveboard_destination_station
        FOREIGN KEY (destination_station_id)
        REFERENCES live_stations(station_id),

    CONSTRAINT fk_liveboard_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES live_vehicles(vehicle_id)
);