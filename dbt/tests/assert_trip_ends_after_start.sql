-- Returns trips that end before they start. The test passes when this returns zero rows.
{{ config(severity='warn') }}
select ride_id, started_at, ended_at
from {{ ref('stg_trips') }}
where ended_at < started_at