import datetime as dt
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas
import pandas as pd
import psr.factory

HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
HOURS_PER_WEEK = HOURS_PER_DAY * DAYS_PER_WEEK  # 168 hours
WEEKS_PER_YEAR = 52
AR_STAGE_SAMPLES = 6

_number_of_days_per_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

_g_week_start_date_by_year: Dict[int, List[dt.datetime]] = {}

_week_max_hours = 7 * 24


def get_sddp_stages_by_year(year: int) -> List[dt.datetime]:
    global _g_week_start_date_by_year
    if year not in _g_week_start_date_by_year:
        _g_week_start_date_by_year[year] = [
            dt.datetime(year, 1, 1),
            dt.datetime(year, 1, 8),
            dt.datetime(year, 1, 15),
            dt.datetime(year, 1, 22),
            dt.datetime(year, 1, 29),
            dt.datetime(year, 2, 5),
            dt.datetime(year, 2, 12),
            dt.datetime(year, 2, 19),
            dt.datetime(year, 2, 26),
            dt.datetime(year, 3, 5),
            dt.datetime(year, 3, 12),
            dt.datetime(year, 3, 19),
            dt.datetime(year, 3, 26),
            dt.datetime(year, 4, 2),
            dt.datetime(year, 4, 9),
            dt.datetime(year, 4, 16),
            dt.datetime(year, 4, 23),
            dt.datetime(year, 4, 30),
            dt.datetime(year, 5, 7),
            dt.datetime(year, 5, 14),
            dt.datetime(year, 5, 21),
            dt.datetime(year, 5, 28),
            dt.datetime(year, 6, 4),
            dt.datetime(year, 6, 11),
            dt.datetime(year, 6, 18),
            dt.datetime(year, 6, 25),
            dt.datetime(year, 7, 2),
            dt.datetime(year, 7, 9),
            dt.datetime(year, 7, 16),
            dt.datetime(year, 7, 23),
            dt.datetime(year, 7, 30),
            dt.datetime(year, 8, 6),
            dt.datetime(year, 8, 13),
            dt.datetime(year, 8, 20),
            dt.datetime(year, 8, 27),
            dt.datetime(year, 9, 3),
            dt.datetime(year, 9, 10),
            dt.datetime(year, 9, 17),
            dt.datetime(year, 9, 24),
            dt.datetime(year, 10, 1),
            dt.datetime(year, 10, 8),
            dt.datetime(year, 10, 15),
            dt.datetime(year, 10, 22),
            dt.datetime(year, 10, 29),
            dt.datetime(year, 11, 5),
            dt.datetime(year, 11, 12),
            dt.datetime(year, 11, 19),
            dt.datetime(year, 11, 26),
            dt.datetime(year, 12, 3),
            dt.datetime(year, 12, 10),
            dt.datetime(year, 12, 17),
            dt.datetime(year, 12, 24)
        ]
    return _g_week_start_date_by_year[year]


def get_closest_sddp_stage_date(y: int, m: int, d: int, previous_date: bool = True) -> Optional[dt.datetime]:
    """Get the closest SDDP stage date for a given year, month, and day."""
    dates = get_sddp_stages_by_year(y)
    sdat = dt.datetime(y, m, d)
    offset = 0 if previous_date else + 1
    last_date = dates[-1]
    if previous_date and sdat >= last_date:
        return last_date
    elif not previous_date and sdat >= last_date:
        dates = get_sddp_stages_by_year(y + 1)
        return dates[0]
    else:
        for index in range(len(dates)-1):
            if dates[index] <= sdat < dates[index+1]:
                return dates[index + offset]
    return None


def get_sddp_week(y: int, m: int, d: int) -> int:
    dates = get_sddp_stages_by_year(y)
    sdat = dt.datetime(y, m, d)
    if dates[-1] <= sdat <= dt.datetime(y, 12, 31):
        return WEEKS_PER_YEAR
    else:
        for index in range(len(dates)-1):
            if dates[index] <= sdat < dates[index+1]:
                return index + 1
    return -1


def get_sddp_start_date_and_stage(year, month, day) -> Tuple[dt.datetime, int]:
    sddp_date = get_closest_sddp_stage_date(year, month, day, previous_date=True)
    sddp_week = get_sddp_week(sddp_date.year, sddp_date.month, sddp_date.day)
    return sddp_date, sddp_week


def get_hour_block_map_from_study(study: psr.factory.Study) -> pandas.DataFrame:
    """
    Extract the HourBlockMap from the study and return as a DataFrame.
    """
    # FixedDurationOfBlocks(block)
    stage_type = study.get("StageType")
    hour_block_map_df = study.get_df("HourBlockMap")

    if hour_block_map_df.empty:
        initial_year = study.get("InitialYear")
        end_year = initial_year + 10
        total_blocks = study.get("NumberOfBlocks")
        block_duration = {}
        total_duration = 0
        for block in range(1, total_blocks + 1):
            # block duration is a percentage of total hours in a stage
            block_duration[block] = study.get(f"FixedDurationOfBlocks({block})")
            total_duration += block_duration[block]

        if total_duration > 99.9:
            # Group stage hours on blocks based on their relative durations to the total number of hours (total_duration)
            if stage_type == 1:
                total_duration = _week_max_hours
                # weekly stages, fixed stage duration
                mapping_data = []
                for year in range(initial_year, end_year):
                    start_date = pandas.Timestamp(f"{year}-01-01")
                    for week in range(1, 53):
                        accumulated_hours = total_duration
                        for block in range(total_blocks, 0, -1):
                            current_duration = int(block_duration[block] * total_duration // 100)
                            if block != 1:
                                current_hours = accumulated_hours - current_duration
                            else:
                                current_hours = 0
                            for hour in range(current_hours, accumulated_hours):
                                datetime_point = start_date + pandas.Timedelta(weeks=week - 1, hours=hour)
                                formatted_datetime = f"{datetime_point.year}/{week:02d} {hour + 1}h"
                                mapping_data.append({
                                    'datetime': formatted_datetime,
                                    'year': datetime_point.year,
                                    'sddp_stage': week,
                                    'sddp_block': block,
                                    'stage_hour': hour + 1
                                })
                            accumulated_hours -= current_duration
                hour_block_map_df = pandas.DataFrame(mapping_data).set_index('datetime')
                # sort dataframe by year, sddp_stage, sddp_block, stage_hour
                hour_block_map_df.sort_values(by=['year', 'sddp_stage', 'sddp_block', 'stage_hour'], inplace=True)
            elif stage_type == 2:
                # monthly stages, variable stage duration
                mapping_data = []
                for year in range(initial_year, end_year):
                    for month in range(1, 13):
                        start_date = pandas.Timestamp(f"{year}-{month:02d}-01")
                        days_in_month = _number_of_days_per_month[month]
                        total_duration = days_in_month * HOURS_PER_DAY
                        accumulated_hours = total_duration
                        for block in range(total_blocks, 0, -1):
                            current_duration = int(block_duration[block] * total_duration // 100)
                            if block != 1:
                                current_hours = accumulated_hours - current_duration
                            else:
                                current_hours = 0
                            for hour in range(current_hours, accumulated_hours):
                                datetime_point = start_date + pandas.Timedelta(hours=hour)
                                formatted_datetime = f"{datetime_point.year}/{datetime_point.month:02d} {hour + 1}h"
                                mapping_data.append({
                                    'datetime': formatted_datetime,
                                    'year': datetime_point.year,
                                    'sddp_stage': month,
                                    'sddp_block': block,
                                    'stage_hour': hour + 1
                                })
                            accumulated_hours -= current_duration
                hour_block_map_df = pandas.DataFrame(mapping_data).set_index('datetime')
                # sort dataframe by year, sddp_stage, sddp_block, stage_hour
                hour_block_map_df.sort_values(by=['year', 'sddp_stage', 'sddp_block', 'stage_hour'], inplace=True)

        else:
            raise ValueError("Total duration of blocks must be 100% or more.")
    else:
        # format HourBlockMap dataframe to have year, sddp_week, sddp_block columns
        # its index datetime column is in the following format: 'YYYY/WW HHHh', where WW is the week number (1-52) and HHH is the hour of the week (1-168)
        # for weekly cases. for monthly cases, it is 'YYYY/MM HHHh', where MM is the month number (1-12) and HHH is the hour of the month (1-744).
        hour_block_map_df = hour_block_map_df.reset_index()
        hour_block_map_df['year'] = hour_block_map_df['datetime'].str.slice(0, 4).astype(int)
        hour_block_map_df['sddp_stage'] = hour_block_map_df['datetime'].str.slice(5, 7).astype(int)
        hour_block_map_df['stage_hour'] = hour_block_map_df['datetime'].str.slice(8, -1).astype(int)
        hour_block_map_df['sddp_block'] = ((hour_block_map_df['hour_of_week'] - 1) // 6) + 1
        hour_block_map_df = hour_block_map_df.set_index('datetime')[['year', 'sddp_week', 'sddp_block']]
    return hour_block_map_df


def remap_hourly_to_stage(hourly_df: pd.DataFrame, hour_block_map_df: pd.DataFrame, stage_type: int,
                          aggregation_method: str = 'mean') -> pd.DataFrame:
    """
    Strategy to Map hourly data into weekly/monthly data:
    - Merge the hourly data dataframe with the Study's hour block map dataframe
    - Aggregate by stage and/or by block using avg, sum, max, etc
    """
    # create indices before merging
    if stage_type == 1:
        # weekly stages
        hourly_df = hourly_df.copy()

        hourly_df['year'] = hourly_df.index.year
        hourly_df['sddp_stage'] = 0
        hourly_df['stage_hour'] = 0
        for irow, (index, row) in enumerate(hourly_df.iterrows()):
            stage_start_date = get_closest_sddp_stage_date(index.year, index.month, index.day, previous_date=True)
            week = get_sddp_week(index.year, index.month, index.day)
            hour_of_week = ((index - stage_start_date).days * 24) + index.hour + 1
            hourly_df.at[row.name, 'sddp_stage'] = week
            hourly_df.at[row.name, 'stage_hour'] = hour_of_week
    elif stage_type == 2:
        # monthly stages
        hourly_df = hourly_df.copy()
        hourly_df['year'] = hourly_df.index.year
        hourly_df['sddp_stage'] = hourly_df.index.month
        hourly_df['stage_hour'] = ((hourly_df.index.day - 1) * 24) + hourly_df.index.hour + 1
    else:
        raise ValueError("Unsupported stage type. Only weekly (1) and monthly (2) are supported.")
    hourly_df = hourly_df.set_index('year,sddp_stage,stage_hour'.split(','))
    hour_block_map_df = hour_block_map_df.set_index('year,sddp_stage,stage_hour'.split(','))
    merged_df = pd.merge(hourly_df, hour_block_map_df, left_index=True, right_index=True, how='inner')

    numeric_cols = hourly_df.select_dtypes(include=[np.number]).columns.tolist()
    result = merged_df.groupby(['year', 'sddp_stage'])[numeric_cols].agg(aggregation_method).reset_index()
    result.sort_values(by=['year', 'sddp_stage'], inplace=True)
    result.set_index(['year', 'sddp_stage'], inplace=True)
    return result


def remap_hourly_to_blocks(hourly_df: pd.DataFrame, hour_block_map_df: pd.DataFrame, stage_type: int,
                          aggregation_method: str = 'mean') -> pd.DataFrame:
    """
    Strategy to Map hourly data into weekly/by block data:
    - Merge the hourly data dataframe with the Study's hour block map dataframe
    - Aggregate by stage and/or by block using avg, sum, max, etc
    """
    # create indices before merging
    if stage_type == 1:
        # weekly stages
        hourly_df = hourly_df.copy()

        hourly_df['year'] = hourly_df.index.year
        hourly_df['sddp_stage'] = 0
        hourly_df['stage_hour'] = 0
        for irow, (index, row) in enumerate(hourly_df.iterrows()):
            stage_start_date = get_closest_sddp_stage_date(index.year, index.month, index.day, previous_date=True)
            week = get_sddp_week(index.year, index.month, index.day)
            hour_of_week = ((index - stage_start_date).days * 24) + index.hour + 1
            hourly_df.at[row.name, 'sddp_stage'] = week
            hourly_df.at[row.name, 'stage_hour'] = hour_of_week
    elif stage_type == 2:
        # monthly stages
        hourly_df = hourly_df.copy()
        hourly_df['year'] = hourly_df.index.year
        hourly_df['sddp_stage'] = hourly_df.index.month
        hourly_df['stage_hour'] = ((hourly_df.index.day - 1) * 24) + hourly_df.index.hour + 1
    else:
        raise ValueError("Unsupported stage type. Only weekly (1) and monthly (2) are supported.")
    hourly_df = hourly_df.set_index('year,sddp_stage,stage_hour'.split(','))
    hour_block_map_df = hour_block_map_df.set_index('year,sddp_stage,stage_hour'.split(','))
    merged_df = pd.merge(hourly_df, hour_block_map_df, left_index=True, right_index=True, how='inner')

    numeric_cols = hourly_df.select_dtypes(include=[np.number]).columns.tolist()
    result = merged_df.groupby(['year', 'sddp_stage', 'sddp_block'])[numeric_cols].agg(aggregation_method).reset_index()
    result.sort_values(by=['year', 'sddp_stage', 'sddp_block'], inplace=True)
    result.set_index(['year', 'sddp_stage', 'sddp_block'], inplace=True)
    return result
