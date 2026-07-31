CREATE TABLE gtfs_rt_feed_snapshots (
    snapshot_id INT IDENTITY(1,1) NOT NULL,
    feed_timestamp DATETIME2 NOT NULL,
    gtfs_realtime_version NVARCHAR(20) NULL,
    incrementality INT NULL,
    imported_at DATETIME2 NOT NULL,

    CONSTRAINT pk_gtfs_rt_feed_snapshots PRIMARY KEY (snapshot_id)
);

CREATE TABLE gtfs_rt_trip_updates (
    trip_update_id INT IDENTITY(1,1) NOT NULL,
    snapshot_id INT NOT NULL,
    entity_id NVARCHAR(500) NOT NULL,
    trip_id NVARCHAR(500) NULL,
    start_date CHAR(8) NULL,
    start_time NVARCHAR(20) NULL,
    schedule_relationship INT NULL,
    trip_update_timestamp DATETIME2 NULL,

    CONSTRAINT pk_gtfs_rt_trip_updates PRIMARY KEY (trip_update_id),

    CONSTRAINT fk_gtfs_rt_trip_updates_snapshot
        FOREIGN KEY (snapshot_id)
        REFERENCES gtfs_rt_feed_snapshots(snapshot_id)
);

CREATE TABLE gtfs_rt_stop_time_updates (
    stop_time_update_id INT IDENTITY(1,1) NOT NULL,
    trip_update_id INT NOT NULL,
    stop_id NVARCHAR(255) NULL,
    stop_sequence INT NULL,
    schedule_relationship INT NULL,
    arrival_time DATETIME2 NULL,
    arrival_delay_seconds INT NULL,
    departure_time DATETIME2 NULL,
    departure_delay_seconds INT NULL,

    CONSTRAINT pk_gtfs_rt_stop_time_updates PRIMARY KEY (stop_time_update_id),

    CONSTRAINT fk_gtfs_rt_stop_time_updates_trip_update
        FOREIGN KEY (trip_update_id)
        REFERENCES gtfs_rt_trip_updates(trip_update_id)
);
