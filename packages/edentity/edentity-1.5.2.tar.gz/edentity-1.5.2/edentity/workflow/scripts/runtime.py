import json
from datetime import datetime


def update_start_time(json_path, stage):
    """
    Update the start time of a stage in a JSON file.
        json_path (str): The path to the JSON file to update.
        stage (str): The key for the start time in the format "%d-%m-%Y %H:%M".
    Returns:
        dict: The updated dictionary from the JSON file.
    """
    current_start_datetime = datetime.now().strftime("%d-%m-%Y %H:%M")
    with open(json_path, "r") as table_5:
        metabarcoding_run_dict = json.load(table_5)

    # Check if trimming start/end datetime is already in the JSON file
    previous_start_datetime = metabarcoding_run_dict.get(stage, current_start_datetime)
    # previous_trim_end_datetime = metabarcoding_run_dict.get('trimming_end_datetime', end_time)

    # Only record the earliest start datetime (the first sample to be trimmed)
    if current_start_datetime < previous_start_datetime:
        metabarcoding_run_dict[stage] = current_start_datetime
    else:
        metabarcoding_run_dict[stage] = previous_start_datetime

    return metabarcoding_run_dict


def update_end_time(metabarcoding_run_dict, stage):
    """
    Update the end time for a given stage in the metabarcoding run dictionary.
    Args:
        metabarcoding_run_dict (dict): Dictionary containing the metabarcoding run data.
        stage (str): The stage of the metabarcoding process to update.
    Returns:
        dict: Updated metabarcoding run dictionary with the new end time for the specified stage.
    """

    # record the last sample end datetime
    current_end_datetime = datetime.now().strftime("%d-%m-%Y %H:%M")
    # check if trimming end datetime is already in the json file, if not set it to the current end datetime
    previous_end_datetime = metabarcoding_run_dict.get(stage, current_end_datetime)
    if current_end_datetime > previous_end_datetime:
        metabarcoding_run_dict[stage] = current_end_datetime
    else:
        metabarcoding_run_dict[stage] = previous_end_datetime
    return metabarcoding_run_dict
