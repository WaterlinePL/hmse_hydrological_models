import csv
import logging
from collections import defaultdict
from typing import Optional

from .. import julian_calendar_manager
from ..hydrus import hydrus_utils
from ..hydrus.file_processing.selector_in_processor import SelectorInProcessor


def read_weather_csv(filepath: str, parsed_start_date: Optional[str] = None, record_count: Optional[int] = None):
    """
    Reads the data from a SWAT weather data .csv file. Returns the data as a dict.

    :param filepath: the path to the file we want to read from
    :return: a dictionary of {str: list}, a mapping of column names to lists of values in said columns
    """

    data = defaultdict(list)
    file = open(filepath)
    reader = csv.DictReader(file)
    jul_day_iter = -1

    found_start_date = parsed_start_date is None
    # start_date_parts = parsed_start_date.split('-')
    # start_date_str = '/'.join((start_date_parts[1], start_date_parts[2], start_date_parts[0]))

    for line in reader:
        data_read = False
        for column, value in line.items():
            # if column == "Date" and value == start_date_str:
            if column == "Date" and value == parsed_start_date:
                found_start_date = True

            if not found_start_date:
                continue

            # a None pops up among the keys for some reason, ignore it
            if column is None:
                continue

            # for everything except date cast the numeric string to a true float
            if column != "Date":
                value = float(value)
            else:
                if jul_day_iter <= 0:
                    jul_day_iter = julian_calendar_manager.date_to_julian(value)
                value = jul_day_iter
                jul_day_iter += 1

            data_read = True
            data[column].append(value)

        if data_read and record_count is not None:
            record_count -= 1
            if record_count <= 0:
                break

    return data


# TODO: enum on the units?
def adapt_data(data: dict, hydrus_dist_unit: str, start_date=None):
    """
    Adapts the raw weather file data for use with hydrus - changes wind speed from m/s to km/day,
    humidity from fractions to percentages (0-100) and scales daily rainfall to the appropriate unit

    :param data: the data we want to adapt
    :param hydrus_dist_unit: the unit of distance used in the hydrus model we'll be modifying - "m", "cm" or "mm"
    :return: the modified data
    """
    #                   to  min  hr   day  km
    data["Wind"] = [speed * 60 * 60 * 24 / 1000 for speed in data["Wind"]]

    data["Relative Humidity"] = [value * 100 for value in data["Relative Humidity"]]

    if hydrus_dist_unit == "m":
        data["Precipitation"] = [value / 1000 for value in data["Precipitation"]]
    elif hydrus_dist_unit == "cm":
        data["Precipitation"] = [value / 10 for value in data["Precipitation"]]
    elif hydrus_dist_unit == "mm":
        pass

    return data


DATE = "Date"
LATITUDE = 'Latitude'
ELEVATION = 'Elevation'
RAD = 'Solar'
T_MAX = 'Max Temperature'
T_MIN = 'Min Temperature'
RH_MEAN = 'Relative Humidity'
WIND = 'Wind'
PRECIPITATION = 'Precipitation'


def add_weather_to_hydrus_model(model_path: str, data: dict):
    """
    Enriches the target hydrus model with weather file data.

    :param model_path: the path of the model to modify
    :param data: a dictionary with the loaded weather data
    :return: success - boolean, true if model was updated successfully, false otherwise
    """

    # modify meteo file if it exists, return if encountered issues
    meteo_path = hydrus_utils.find_hydrus_file_path(model_path, file_name="meteo.in")
    if meteo_path:
        meteo_file_modified = __modify_meteo_file(meteo_path, data)
        if not meteo_file_modified:
            return False

    # modify atmosph file is it exists
    replace_rain = PRECIPITATION in data.keys()
    atmosph_path = hydrus_utils.find_hydrus_file_path(model_path, file_name="atmosph.in")
    if replace_rain and atmosph_path:
        atmosph_file_modified = __modify_atmosph_file(atmosph_path, data)
        if not atmosph_file_modified:
            return False

    selector_path = hydrus_utils.find_hydrus_file_path(model_path, file_name="selector.in")
    if selector_path:
        with open(selector_path, 'r+', encoding='utf-8') as fp:
            SelectorInProcessor(fp).update_initial_and_final_step(data[DATE][0], data[DATE][-1])

    return True


def __modify_meteo_file(meteo_file_path, data):
    meteo_file = open(meteo_file_path, "r+")

    old_file_lines = meteo_file.readlines()
    # remove trailing empty lines from end of file
    while old_file_lines[len(old_file_lines) - 1].strip() == "":
        old_file_lines.pop()
    new_file_lines = []

    # update latitude and altitude
    i = 0
    while True:
        curr_line = old_file_lines[i]
        new_file_lines.append(curr_line)
        i += 1
        if "Latitude" in curr_line:
            # write the updated values and break
            new_file_lines.append(f"   {data[LATITUDE][0]}   {data[ELEVATION][0]}\n")
            i += 1
            break

    # check which fields we have data about
    replace_rad = RAD in data.keys()
    replace_tmax = T_MAX in data.keys()
    replace_tmin = T_MIN in data.keys()
    replace_rhmean = RH_MEAN in data.keys()
    replace_wind = WIND in data.keys()

    # navigate to table start
    while True:
        curr_line = old_file_lines[i]
        new_file_lines.append(curr_line)
        i += 1
        if "Daily values" in curr_line:
            new_file_lines.append(old_file_lines[i])  # skip field descriptions line
            i += 1
            new_file_lines.append(old_file_lines[i])  # skip units line
            i += 1
            break

    # verify if weather file length is at least the same as data;
    # i+1 for 0-indexing, +1 for the sum to be correct, then -1 for the EOF line
    data_lines = len(old_file_lines) - (i + 1)
    if len(data[LATITUDE]) < data_lines:
        logging.log(logging.WARN,
                    f"Insufficient weather file size"
                    f" - expected at least {data_lines} records,"
                    f" got {len(data[LATITUDE])}")
        return False

    # write new table values, only change columns for which we have data
    data_row = 0
    while True:

        # break if reached end of file
        curr_line = old_file_lines[i]
        if "end" in curr_line:
            new_file_lines.append(curr_line)
            break

        curr_row = old_file_lines[i].split()
        curr_row[0] = data[DATE][data_row]
        if replace_rad:
            curr_row[1] = data[RAD][data_row]
        if replace_tmax:
            curr_row[2] = data[T_MAX][data_row]
        if replace_tmin:
            curr_row[3] = data[T_MIN][data_row]
        if replace_rhmean:
            curr_row[4] = data[RH_MEAN][data_row]
        if replace_wind:
            curr_row[5] = data[WIND][data_row]

        new_file_lines.append(__build_line(curr_row))

        i += 1
        data_row += 1

    # overwrite file
    meteo_file.seek(0)
    meteo_file.writelines(new_file_lines)
    meteo_file.truncate()
    meteo_file.close()

    return True


def __modify_atmosph_file(atmosph_file_path, data):
    atmosph_file = open(atmosph_file_path, "r+")

    old_file_lines = atmosph_file.readlines()
    # remove trailing empty lines from end of file
    while old_file_lines[len(old_file_lines) - 1].strip() == "":
        old_file_lines.pop()
    new_file_lines = []

    i = 0

    # navigate to table start
    while True:
        curr_line = old_file_lines[i]
        new_file_lines.append(curr_line)
        i += 1
        if "Prec" in curr_line:
            break

    # verify if weather file length is at least the same as data;
    # i+1 for 0-indexing, +1 for the sum to be correct, then -1 for the EOF line
    data_lines = len(old_file_lines) - (i + 1)
    if len(data[LATITUDE]) < data_lines:
        logging.log(logging.WARN,
                    f"Insufficient weather file size"
                    f" - expected at least {data_lines} records,"
                    f" got {len(data[LATITUDE])}")
        return False

    # modify table
    data_row = 0
    while True:

        # break if reached end of file
        curr_line = old_file_lines[i]
        if "end" in curr_line:
            new_file_lines.append(curr_line)
            break

        curr_row = old_file_lines[i].split()
        curr_row[0] = data[DATE][data_row]
        curr_row[1] = data[PRECIPITATION][data_row]
        new_file_lines.append(__build_line(curr_row))

        i += 1
        data_row += 1

    # overwrite file
    atmosph_file.seek(0)
    atmosph_file.writelines(new_file_lines)
    atmosph_file.truncate()
    atmosph_file.close()

    return True


def __build_line(items: list):
    line = "   "
    for item in items:
        line += f"{item}    "
    line += "\n"
    return line
