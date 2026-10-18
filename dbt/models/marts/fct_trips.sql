{{
    config(
        materialized='table',
        partition_by={'field': 'started_at', 'data_type': 'timestamp', 'granularity': 'day'},
        cluster_by=['start_station_id']
    )
}}

select
    ride_id,
    started_at,
    ended_at,
    date(started_at) as started_date,
    start_station_id,
    end_station_id,
    rideable_type,
    rider_type,
    timestamp_diff(ended_at, started_at, second) as trip_duration_seconds,
    start_lat,
    start_lng,
    end_lat,
    end_lng
from {{ ref('stg_trips') }}
where started_at is not null
  and ended_at >= started_at