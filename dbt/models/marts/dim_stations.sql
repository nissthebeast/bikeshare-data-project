with station_events as (

    select start_station_id as station_id, start_station_name as station_name,
           start_lat as lat, start_lng as lng, started_at as seen_at
    from {{ ref('stg_trips') }}
    where start_station_id is not null

    union all

    select end_station_id, end_station_name,
           end_lat, end_lng, ended_at
    from {{ ref('stg_trips') }}
    where end_station_id is not null

)

select
    station_id,
    array_agg(station_name order by seen_at desc limit 1)[offset(0)] as station_name,
    array_agg(lat order by seen_at desc limit 1)[offset(0)] as lat,
    array_agg(lng order by seen_at desc limit 1)[offset(0)] as lng
from station_events
group by station_id