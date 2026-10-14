import argparse
import os
import shutil
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT = os.environ["GCP_PROJECT_ID"]
BASE_URL = "https://s3.amazonaws.com/capitalbikeshare-data"
DATA_DIR = Path("data")
TARGET = f"{PROJECT}.raw.trips"
TEMP = f"{PROJECT}.raw.trips_load_tmp"

COLUMNS = [
    "ride_id", "rideable_type", "started_at", "ended_at",
    "start_station_name", "start_station_id",
    "end_station_name", "end_station_id",
    "start_lat", "start_lng", "end_lat", "end_lng", "member_casual",
]

client = bigquery.Client(project=PROJECT, location="US")


def months_between(start, end):
    y, m = int(start[:4]), int(start[4:])
    end_y, end_m = int(end[:4]), int(end[4:])
    while (y, m) <= (end_y, end_m):
        yield f"{y}{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def download_and_extract(month):
    DATA_DIR.mkdir(exist_ok=True)
    name = f"{month}-capitalbikeshare-tripdata"
    csv_path = DATA_DIR / f"{name}.csv"
    if csv_path.exists():
        return csv_path

    url = f"{BASE_URL}/{name}.zip"
    resp = requests.get(url, stream=True, timeout=60)
    if resp.status_code != 200:
        print(f"{month}: download failed ({resp.status_code}) for {url}")
        return None

    zip_path = DATA_DIR / f"{name}.zip"
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)

    with zipfile.ZipFile(zip_path) as z:
        member = next(
            n for n in z.namelist()
            if n.endswith(".csv") and not n.startswith("__MACOSX")
        )
        with z.open(member) as src, open(csv_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
    return csv_path


def load_month(csv_path):
    source_file = csv_path.name

    # 1. Load the CSV into a temp table (all strings, replaced each time)
    job_config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(c, "STRING") for c in COLUMNS],
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        allow_quoted_newlines=True,
        write_disposition="WRITE_TRUNCATE",
    )
    with open(csv_path, "rb") as f:
        client.load_table_from_file(f, TEMP, job_config=job_config).result()

    # 2. Make sure the target exists, then replace this file's rows
    col_defs = ", ".join(f"{c} STRING" for c in COLUMNS)
    client.query(
        f"CREATE TABLE IF NOT EXISTS `{TARGET}` "
        f"({col_defs}, _source_file STRING, _loaded_at TIMESTAMP)"
    ).result()

    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("f", "STRING", source_file)]
    )
    client.query(f"DELETE FROM `{TARGET}` WHERE _source_file = @f", job_config=cfg).result()
    client.query(
        f"INSERT INTO `{TARGET}` "
        f"SELECT {', '.join(COLUMNS)}, @f, CURRENT_TIMESTAMP() FROM `{TEMP}`",
        job_config=cfg,
    ).result()
    print(f"Loaded {source_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYYMM")
    parser.add_argument("--end", required=True, help="YYYYMM")
    args = parser.parse_args()

    for month in months_between(args.start, args.end):
        path = download_and_extract(month)
        if path:
            load_month(path)