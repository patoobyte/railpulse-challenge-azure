CREATE TABLE agency (
    agency_id NVARCHAR(255) NOT NULL,
    agency_fare_url NVARCHAR(1000) NULL,
    agency_lang NVARCHAR(20) NOT NULL,
    agency_name NVARCHAR(255) NOT NULL,
    agency_phone NVARCHAR(100) NULL,
    agency_timezone NVARCHAR(100) NOT NULL,
    agency_url NVARCHAR(1000) NOT NULL,
    CONSTRAINT pk_agency PRIMARY KEY (agency_id)
);

CREATE TABLE calendar (
    service_id NVARCHAR(255) NOT NULL,
    start_date CHAR(8) NOT NULL,
    end_date CHAR(8) NOT NULL,
    monday BIT NOT NULL,
    tuesday BIT NOT NULL,
    wednesday BIT NOT NULL,
    thursday BIT NOT NULL,
    friday BIT NOT NULL,
    saturday BIT NOT NULL,
    sunday BIT NOT NULL,
    CONSTRAINT pk_calendar PRIMARY KEY (service_id)
);

CREATE TABLE routes (
    route_id NVARCHAR(255) NOT NULL,
    agency_id NVARCHAR(255) NOT NULL,
    route_color NVARCHAR(20) NOT NULL,
    route_desc NVARCHAR(1000) NULL,
    route_long_name NVARCHAR(255) NOT NULL,
    route_short_name NVARCHAR(255) NOT NULL,
    route_text_color NVARCHAR(20) NOT NULL,
    route_type INT NOT NULL,
    route_url NVARCHAR(1000) NULL,
    CONSTRAINT pk_routes PRIMARY KEY (route_id),
    CONSTRAINT fk_routes_agency
        FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
);

CREATE TABLE stops (
    stop_id NVARCHAR(255) NOT NULL,
    parent_station NVARCHAR(255) NULL,
    location_type INT NOT NULL,
    platform_code NVARCHAR(100) NULL,
    stop_code NVARCHAR(100) NULL,
    stop_desc NVARCHAR(1000) NOT NULL,
    stop_lat FLOAT NOT NULL,
    stop_lon FLOAT NOT NULL,
    stop_name NVARCHAR(255) NOT NULL,
    stop_url NVARCHAR(1000) NULL,
    wheelchair_boarding INT NULL,
    zone_id NVARCHAR(255) NULL,
    CONSTRAINT pk_stops PRIMARY KEY (stop_id),
    CONSTRAINT fk_stops_parent_station
        FOREIGN KEY (parent_station) REFERENCES stops(stop_id)
);

CREATE TABLE trips (
    trip_id NVARCHAR(255) NOT NULL,
    route_id NVARCHAR(255) NOT NULL,
    service_id NVARCHAR(255) NOT NULL,
    bikes_allowed INT NULL,
    block_id NVARCHAR(255) NOT NULL,
    direction_id INT NULL,
    shape_id NVARCHAR(255) NULL,
    trip_headsign NVARCHAR(255) NOT NULL,
    trip_short_name NVARCHAR(255) NOT NULL,
    wheelchair_accessible INT NULL,
    CONSTRAINT pk_trips PRIMARY KEY (trip_id),
    CONSTRAINT fk_trips_routes
        FOREIGN KEY (route_id) REFERENCES routes(route_id),
    CONSTRAINT fk_trips_calendar
        FOREIGN KEY (service_id) REFERENCES calendar(service_id)
);

CREATE TABLE calendar_dates (
    [date] CHAR(8) NOT NULL,
    exception_type INT NOT NULL,
    service_id NVARCHAR(255) NOT NULL,
    CONSTRAINT pk_calendar_dates PRIMARY KEY ([date], service_id),
    CONSTRAINT fk_calendar_dates_calendar
        FOREIGN KEY (service_id) REFERENCES calendar(service_id)
);

CREATE TABLE stop_times (
    arrival_time NVARCHAR(20) NOT NULL,
    departure_time NVARCHAR(20) NOT NULL,
    drop_off_type INT NOT NULL,
    pickup_type INT NOT NULL,
    shape_dist_traveled FLOAT NULL,
    stop_headsign NVARCHAR(255) NULL,
    stop_id NVARCHAR(255) NOT NULL,
    stop_sequence INT NOT NULL,
    trip_id NVARCHAR(255) NOT NULL,
    CONSTRAINT pk_stop_times PRIMARY KEY (stop_sequence, trip_id),
    CONSTRAINT fk_stop_times_stops
        FOREIGN KEY (stop_id) REFERENCES stops(stop_id),
    CONSTRAINT fk_stop_times_trips
        FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
);