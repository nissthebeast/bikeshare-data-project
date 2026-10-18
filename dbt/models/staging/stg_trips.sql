with source as (

    select * from {{ source('raw', 'trips') }}

),

cleaned as (

    select
        ride_id,
        rideable_type,
        safe_cast(started_at as timestamp) as started_at,
        safe_cast(ended_at as timestamp) as ended_at,
        nullif(trim(start_station_name), '') as start_station_name,
        nullif(trim(start_station_id), '') as start_station_id,
        nullif(trim(end_station_name), '') as end_station_name,
        nullif(trim(end_station_id), '') as end_station_id,
        safe_cast(start_lat as float64) as start_lat,
        safe_cast(start_lng as float64) as start_lng,
        safe_cast(end_lat as float64) as end_lat,
        safe_cast(end_lng as float64) as end_lng,
        member_casual as rider_type,
        _source_file,
        _loaded_at
    from source

),

deduped as (

    select *
    from cleaned
    qualify row_number() over (
        partition by ride_id
        order by _loaded_at desc, ended_at desc
    ) = 1

)

select * from deduped