import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
import pyodbc
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


SNCB_TRIP_UPDATE_URL = (
    "https://api-management-opendata-production.azure-api.net"
    "/api/gtfs/feed/nmbssncb/rt/trip-update/"
)


def unix_to_datetime(value):
    if value is None:
        return None

    if isinstance(value, dict):
        value = value.get("low")

    if value is None:
        return None

    return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)


def get_required_setting(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing {name} environment variable.")
    return value


def fetch_sncb_trip_updates():
    partner_key = get_required_setting("BMC_PARTNER_KEY")

    response = requests.get(
        SNCB_TRIP_UPDATE_URL,
        params={"format": "json"},
        headers={
            "bmc-partner-key": partner_key,
            "User-Agent": "RailPulse Azure Function",
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            "SNCB trip-update request failed with "
            f"status {response.status_code} for {response.url}: "
            f"{response.text[:1000]}"
        )

    return response.json()


def insert_feed_snapshot(cursor, header):
    cursor.execute(
        """
        INSERT INTO gtfs_rt_feed_snapshots (
            feed_timestamp,
            gtfs_realtime_version,
            incrementality,
            imported_at
        )
        OUTPUT INSERTED.snapshot_id
        VALUES (?, ?, ?, ?)
        """,
        unix_to_datetime(header.get("timestamp")),
        header.get("gtfsRealtimeVersion"),
        header.get("incrementality"),
        datetime.now(timezone.utc).replace(tzinfo=None),
    )
    return cursor.fetchone()[0]


def insert_trip_update(cursor, snapshot_id, entity):
    trip_update = entity.get("tripUpdate", {})
    trip = trip_update.get("trip", {})

    cursor.execute(
        """
        INSERT INTO gtfs_rt_trip_updates (
            snapshot_id,
            entity_id,
            trip_id,
            start_date,
            start_time,
            schedule_relationship,
            trip_update_timestamp
        )
        OUTPUT INSERTED.trip_update_id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        snapshot_id,
        entity.get("id"),
        trip.get("tripId"),
        trip.get("startDate"),
        trip.get("startTime"),
        trip.get("scheduleRelationship"),
        unix_to_datetime(trip_update.get("timestamp")),
    )
    return cursor.fetchone()[0]


def insert_stop_time_update(cursor, trip_update_id, stop_update):
    arrival = stop_update.get("arrival", {})
    departure = stop_update.get("departure", {})

    cursor.execute(
        """
        INSERT INTO gtfs_rt_stop_time_updates (
            trip_update_id,
            stop_id,
            stop_sequence,
            schedule_relationship,
            arrival_time,
            arrival_delay_seconds,
            departure_time,
            departure_delay_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        trip_update_id,
        stop_update.get("stopId"),
        stop_update.get("stopSequence"),
        stop_update.get("scheduleRelationship"),
        unix_to_datetime(arrival.get("time")),
        arrival.get("delay"),
        unix_to_datetime(departure.get("time")),
        departure.get("delay"),
    )


@app.route(route="ingest_liveboard")
def ingest_liveboard(req: func.HttpRequest) -> func.HttpResponse:
    try:
        result = ingest_sncb_trip_updates()
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as error:
        logging.exception("SNCB trip-update ingestion failed.")
        error_response = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        return func.HttpResponse(
            json.dumps(error_response),
            mimetype="application/json",
            status_code=500,
        )


@app.timer_trigger(
    schedule="0 0 */4 * * *",
    arg_name="timer",
    run_on_startup=False,
)
def timer_ingest_liveboard(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.info("Timer trigger is running later than scheduled.")

    result = ingest_sncb_trip_updates()
    logging.info("Timer ingestion completed: %s", json.dumps(result))


def ingest_sncb_trip_updates():
    logging.info("Starting SNCB GTFS-RT trip-update ingestion.")

    connection_string = get_required_setting("SQL_CONNECTION_STRING")
    feed_data = fetch_sncb_trip_updates()
    entities = feed_data.get("entity", [])

    trip_update_count = 0
    stop_time_update_count = 0

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()

        snapshot_id = insert_feed_snapshot(cursor, feed_data.get("header", {}))

        for entity in entities:
            if "tripUpdate" not in entity:
                continue

            trip_update_id = insert_trip_update(cursor, snapshot_id, entity)
            trip_update_count += 1

            stop_updates = entity.get("tripUpdate", {}).get("stopTimeUpdate", [])
            for stop_update in stop_updates:
                insert_stop_time_update(cursor, trip_update_id, stop_update)
                stop_time_update_count += 1

        connection.commit()

    result = {
        "source": "sncb_gtfs_rt_trip_update",
        "snapshot_id": snapshot_id,
        "trip_updates": trip_update_count,
        "stop_time_updates": stop_time_update_count,
        "feed_timestamp": unix_to_datetime(
            feed_data.get("header", {}).get("timestamp")
        ).isoformat(),
    }
    return result
