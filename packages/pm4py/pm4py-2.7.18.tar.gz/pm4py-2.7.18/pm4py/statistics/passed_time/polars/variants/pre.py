'''
    PM4Py â€“ A Process Mining Library for Python
Copyright (C) 2024 Process Intelligence Solutions UG (haftungsbeschrÃ¤nkt)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see this software project's root or
visit <https://www.gnu.org/licenses/>.

Website: https://processintelligence.solutions
Contact: info@processintelligence.solutions
'''
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TIMESTAMP_KEY
from pm4py.util.constants import CASE_CONCEPT_NAME
from pm4py.util import exec_utils
from pm4py.util import constants
from enum import Enum
from typing import Optional, Dict, Any
import polars as pl


class Parameters(Enum):
    ATTRIBUTE_KEY = constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    MAX_NO_POINTS_SAMPLE = "max_no_of_points_to_sample"
    KEEP_ONCE_PER_CASE = "keep_once_per_case"
    BUSINESS_HOURS = "business_hours"
    BUSINESS_HOUR_SLOTS = "business_hour_slots"
    WORKCALENDAR = "workcalendar"


def apply(
    lf: pl.LazyFrame,
    activity: str,
    parameters: Optional[Dict[Any, Any]] = None,
) -> Dict[str, Any]:
    """
    Gets the time passed from each preceding activity

    Parameters
    -------------
    lf
        LazyFrame
    activity
        Activity that we are considering
    parameters
        Possible parameters of the algorithm

    Returns
    -------------
    dictio
        Dictionary containing a 'pre' key with the
        list of aggregates times from each preceding activity to the given activity
    """
    if parameters is None:
        parameters = {}

    case_id_glue = exec_utils.get_param_value(
        Parameters.CASE_ID_KEY, parameters, CASE_CONCEPT_NAME
    )
    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, parameters, DEFAULT_NAME_KEY
    )
    timestamp_key = exec_utils.get_param_value(
        Parameters.TIMESTAMP_KEY, parameters, DEFAULT_TIMESTAMP_KEY
    )
    start_timestamp_key = exec_utils.get_param_value(
        Parameters.START_TIMESTAMP_KEY, parameters, None
    )

    business_hours = exec_utils.get_param_value(
        Parameters.BUSINESS_HOURS, parameters, False
    )
    business_hours_slots = exec_utils.get_param_value(
        Parameters.BUSINESS_HOUR_SLOTS,
        parameters,
        constants.DEFAULT_BUSINESS_HOUR_SLOTS,
    )
    workcalendar = exec_utils.get_param_value(
        Parameters.WORKCALENDAR,
        parameters,
        constants.DEFAULT_BUSINESS_HOURS_WORKCALENDAR,
    )

    # Basic DFG computation for preceding activities
    # This is a simplified version - full implementation would need more complex DFG logic
    if start_timestamp_key is None:
        start_timestamp_key = timestamp_key
    
    # Sort by case and timestamp
    sorted_lf = lf.sort([case_id_glue, timestamp_key])
    
    # Create pairs of consecutive activities
    with_next = sorted_lf.with_columns([
        pl.col(activity_key).shift(-1).over(case_id_glue).alias(activity_key + "_next"),
        pl.col(timestamp_key).shift(-1).over(case_id_glue).alias(timestamp_key + "_next"),
    ])
    
    # Filter for target activity as next activity
    target_flows = with_next.filter(
        pl.col(activity_key + "_next") == activity
    )
    
    # Calculate time differences
    if business_hours:
        # For business hours, we need to collect and apply the function
        # This is a simplified version
        flows_df = target_flows.collect()
        # Would need actual business hours calculation here
        flows_df = flows_df.with_columns(
            (pl.col(timestamp_key + "_next") - pl.col(timestamp_key)).dt.total_seconds().alias("flow_time")
        )
    else:
        flows_df = target_flows.with_columns(
            (pl.col(timestamp_key + "_next") - pl.col(timestamp_key)).dt.total_seconds().alias("flow_time")
        ).collect()
    
    # Group by preceding activity and compute statistics
    stats = flows_df.group_by(activity_key).agg([
        pl.col("flow_time").mean().alias("avg_time"),
        pl.col("flow_time").count().alias("frequency")
    ])
    
    pre = []
    sum_perf_pre = 0.0
    sum_acti_pre = 0.0
    
    for row in stats.iter_rows():
        pre_activity = row[0]
        avg_time = row[1]
        frequency = row[2]
        
        pre.append([pre_activity, float(avg_time), int(frequency)])
        sum_perf_pre += float(avg_time) * int(frequency)
        sum_acti_pre += int(frequency)

    if sum_acti_pre > 0:
        sum_perf_pre = sum_perf_pre / sum_acti_pre

    return {"pre": pre, "pre_avg_perf": sum_perf_pre, "pre_total_acti": sum_acti_pre}