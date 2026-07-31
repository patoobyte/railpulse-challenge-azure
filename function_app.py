import json
import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import azure.functions as func
import pyodbc
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


IRAIL_LIVEBOARD_URL = "https://api.irail.be/liveboard/"
BELGIUM_TIMEZONE = ZoneInfo("Europe/Brussels")
DEFAULT_STATION_ID = "BE.NMBS.008821006"


def unix_to_datetime(value):
    return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)


def text_to_bit(value):
    return 1 if str(value) == "1" else 0


def upsert_station(cursor, station_info):
    cursor.execute(
        """
        IF EXISTS (SELECT 1 FROM live_stations WHERE station_id = ?)
            UPDATE live_stations
            SET station_uri = ?,
                station_name = ?,
                standard_name = ?,
                longitude = ?,
                latitude = ?
            WHERE station_id = ?
        ELSE
            INSERT INTO live_stations (
                station_id,
                station_uri,
                station_name,
                standard_name,
                longitude,
                latitude
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        station_info.get("id"),
        station_info.get("@id"),
        station_info.get("name"),
        station_info.get("standardname"),
        station_info.get("locationX"),
        station_info.get("locationY"),
        station_info.get("id"),
        station_info.get("id"),
        station_info.get("@id"),
        station_info.get("name"),
        station_info.get("standardname"),
        station_info.get("locationX"),
        station_info.get("locationY"),
    )


def upsert_vehicle(cursor, vehicle_info):
    cursor.execute(
        """
        IF EXISTS (SELECT 1 FROM live_vehicles WHERE vehicle_id = ?)
            UPDATE live_vehicles
            SET vehicle_uri = ?,
                vehicle_name = ?,
                vehicle_shortname = ?,
                vehicle_number = ?,
                vehicle_type = ?
            WHERE vehicle_id = ?
        ELSE
            INSERT INTO live_vehicles (
                vehicle_id,
                vehicle_uri,
                vehicle_name,
                vehicle_shortname,
                vehicle_number,
                vehicle_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        vehicle_info.get("name"),
        vehicle_info.get("@id"),
        vehicle_info.get("name"),
        vehicle_info.get("shortname"),
        vehicle_info.get("number"),
        vehicle_info.get("type"),
        vehicle_info.get("name"),
        vehicle_info.get("name"),
        vehicle_info.get("@id"),
        vehicle_info.get("name"),
        vehicle_info.get("shortname"),
        vehicle_info.get("number"),
        vehicle_info.get("type"),
    )


def insert_liveboard_record(cursor, snapshot_time, queried_station_id, departure):
    platform_info = departure.get("platforminfo", {})
    occupancy = departure.get("occupancy", {})
    destination_station = departure.get("stationinfo", {})
    vehicle_info = departure.get("vehicleinfo", {})

    cursor.execute(
        """
        INSERT INTO liveboard_records (
            snapshot_time,
            queried_station_id,
            destination_station_id,
            vehicle_id,
            departure_api_id,
            scheduled_time,
            delay_seconds,
            platform,
            platform_is_normal,
            is_canceled,
            has_left,
            is_extra,
            occupancy,
            departure_connection
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        snapshot_time,
        queried_station_id,
        destination_station.get("id"),
        vehicle_info.get("name"),
        departure.get("id"),
        unix_to_datetime(departure.get("time")),
        int(departure.get("delay", 0)),
        departure.get("platform"),
        text_to_bit(platform_info.get("normal")),
        text_to_bit(departure.get("canceled")),
        text_to_bit(departure.get("left")),
        text_to_bit(departure.get("isExtra")),
        occupancy.get("name"),
        departure.get("departureConnection"),
    )


@app.route(route="ingest_liveboard")
def ingest_liveboard(req: func.HttpRequest) -> func.HttpResponse:
    try:
        station_id = req.params.get("id", DEFAULT_STATION_ID)
        result = ingest_station_liveboard(station_id)
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as error:
        logging.exception("Liveboard ingestion failed.")
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

    result = ingest_station_liveboard(DEFAULT_STATION_ID)
    logging.info("Timer ingestion completed: %s", json.dumps(result))


def ingest_station_liveboard(station_id):
    logging.info("Starting iRail liveboard ingestion.")

    connection_string = os.environ.get("SQL_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("Missing SQL_CONNECTION_STRING environment variable.")

    belgium_now = datetime.now(BELGIUM_TIMEZONE)

    response = requests.get(
        IRAIL_LIVEBOARD_URL,
        params={
            "id": station_id,
            "date": belgium_now.strftime("%d%m%y"),
            "time": belgium_now.strftime("%H%M"),
            "arrdep": "departure",
            "format": "json",
            "lang": "en",
        },
        headers={"User-Agent": "RailPulse Azure Function"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            "iRail request failed with "
            f"status {response.status_code} for {response.url}: "
            f"{response.text[:1000]}"
        )

    liveboard_data = response.json()
    snapshot_time = unix_to_datetime(liveboard_data["timestamp"])
    queried_station_info = liveboard_data["stationinfo"]
    departures = liveboard_data["departures"]["departure"]

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()

        upsert_station(cursor, queried_station_info)

        for departure in departures:
            upsert_station(cursor, departure["stationinfo"])
            upsert_vehicle(cursor, departure["vehicleinfo"])
            insert_liveboard_record(
                cursor,
                snapshot_time,
                queried_station_info["id"],
                departure,
            )

        connection.commit()

    result = {
        "station_id": station_id,
        "inserted_records": len(departures),
        "snapshot_time": snapshot_time.isoformat(),
    }
    return result
