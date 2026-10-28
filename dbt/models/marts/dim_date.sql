with bounds as (

    select
        min(started_date) as min_date,
        max(started_date) as max_date
    from {{ ref('fct_trips') }}

)

select
    d as date_day,
    extract(year from d) as year,
    extract(month from d) as month,
    format_date('%B', d) as month_name,
    extract(dayofweek from d) as day_of_week_number,
    format_date('%A', d) as day_name,
    extract(dayofweek from d) in (1, 7) as is_weekend
from bounds,
    unnest(generate_date_array(min_date, max_date)) as d