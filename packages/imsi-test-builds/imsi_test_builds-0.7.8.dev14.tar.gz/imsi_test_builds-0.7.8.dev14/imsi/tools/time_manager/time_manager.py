import cftime
from imsi.tools.time_manager import cftime_utils
from dataclasses import dataclass, field
from typing import List, Tuple, Type
from datetime import timedelta
import isodate
import re
import warnings

############################################################
# Durations allowed by IMSI
# PnY    or    PnYS     : duration in years
# PnM    or    PnMS     : duration in months
# PnD    or    PnDS     : duration in days
# PTnH   or    PTnHS    : duration in hours
# PTnM   or    PTnMS    : duration in minutes
# PTnS   or    PTnSS    : duration in seconds   RD: we probably don't need SS, maybe?
# Placing and "S" after the unit forces time segments
# to fall on clean boundaries (start and end of months, e.g.),
# only after the FIRST segment.
# For example, if run_segment_start_date = 6000-01-15 and
# model_chunk_size = P1MS, the first segment will run
# from Jan 15 to Jan 31, the second from Feb 1 to Feb 28/29,
# the third from Mar 1 to Mar 31, etc. With P1M, however,
# each segment will start on the 15th of the month.
# Not all sequencers have this behavior enabled at present.
# The above should be added to IMSI documentation and schema.

@dataclass
class SimDateTime:
    """
    Base class for representing an individual time point.

    Attributes:
        time_string (str): The time string in ISO 8601 format.
        calendar (str): The calendar type.
        time (cftime.datetime): Parsed cftime datetime object.
        cftime_calendar (Type[cftime.datetime]): cftime calendar class.
    """
    time_string: str
    calendar: str = 'noleap'
    time: cftime.datetime = field(init=False)
    cftime_calendar: Type[cftime.datetime] = field(init=False)

    def __post_init__(self):
        self.cftime_calendar = cftime_utils.get_date_type(self.calendar)

@dataclass
class SimStartDateTime(SimDateTime):
    """Class for handling the start time of a simulation."""

    def __post_init__(self):
        super().__post_init__()
        self.time = cftime_utils.parse_time(self.time_string, self.cftime_calendar, date_type='start')

@dataclass
class SimStopDateTime(SimDateTime):
    """Class for handling the stop time of a simulation."""

    def __post_init__(self):
        super().__post_init__()
        self.time = cftime_utils.parse_time(self.time_string, self.cftime_calendar, date_type='end')


class SimDuration:
    def __init__(self, user_string: str):
        self.str = user_string

        #matches P or PT, integer, unit, and optional "S"
        #returns a string without "S" if found
        #the result will conform to iso8601 format
        str_match = re.match(r"(P)(T?)(\d+)(\D)(S?)$", self.str)

        if str_match:
            iso_format = f'{str_match.group(1)}{str_match.group(2)}{str_match.group(3)}{str_match.group(4)}'
        else:
            raise ValueError(f'Improper duration specified: {self.str}')

        self.duration = isodate.parse_duration(iso_format)
        self.unit = f'{str_match.group(4)}{str_match.group(5)}'

        if str_match.group(5):
            #if there is the trailing "S" denoting start of duration units
            self.adjust_start = True
        else:
            self.adjust_start = False


class SimStartStop:
    """
    Class for start and stop data for the run and run segment.
    Does not contain chunk information, as it is used in different
    contexts.
    """
    def __init__(self, calendar: str, run_start: str, run_stop: str,
                 run_segment_start: str, run_segment_stop):

        self.calendar = cftime_utils.get_date_type(calendar)
        self.run_start_time = SimStartDateTime(run_start, calendar).time
        self.run_stop_time = SimStopDateTime(run_stop, calendar).time
        self.run_segment_start_time = SimStartDateTime(run_segment_start, calendar).time
        self.run_segment_stop_time = SimStopDateTime(run_segment_stop, calendar).time

    @classmethod
    def from_kwargs(cls, **kwargs):
        '''
        Instantiate SimStartStop instance from KW args
        '''
        calendar = kwargs.get('calendar', 'noleap')

        run_start_time = kwargs.get('run_start_time')
        run_stop_time = kwargs.get('run_stop_time')
        run_segment_start_time = kwargs.get('run_segment_start_time')
        run_segment_stop_time = kwargs.get('run_segment_stop_time')

        return cls(calendar, run_start_time, run_stop_time, run_segment_start_time, run_segment_stop_time)

    def shell_formatted_time_vars(self):
        """
        Create a dict of formatted time/chunk vars to meet the current canesm scripting interface
        """
        dates2process = {
            "run_start": self.run_start_time,
            "run_stop": self.run_stop_time,
            "run_segment_start": self.run_segment_start_time,
            "run_segment_stop": self.run_segment_stop_time,
        }

        return format_time_vars(dates2process)


class SimTimer:
    """
    A generic class for holding chunk info
    """

    def __init__(
        self,
        name: str,
        calendar: str,
        start: SimStartDateTime,
        stop: SimStopDateTime,
        chunk_duration: str,
        date_prefix: str,
        chunk_prefix: str,
    ):
        self.name = name
        self.calendar = calendar
        self.start = start
        self.stop = stop
        self.date_prefix = date_prefix
        self.chunk_prefix = chunk_prefix
        self.chunk_size_str = chunk_duration
        self.ChunkDuration = SimDuration(chunk_duration)
        (self.ChunkIndexStart, self.ChunkIndexStop) = (
            self._generate_job_start_end_date_lists(
                self.start, self.stop, self.ChunkDuration
            )
        )
        self.NumChunks = len(self.ChunkIndexStart)

    @classmethod
    def from_iso(
        cls,
        name,
        start,
        stop,
        ChunkDuration,
        date_prefix,
        chunk_prefix,
        calendar="noleap",
    ):
        """
        Instantiate a SimulationTime instance from iso8601 strings

        Parse times into CFTIMES, using start/end logic
        """
        StartTime = SimStartDateTime(start, calendar).time
        StopTime = SimStopDateTime(stop, calendar).time
        return cls(
            name,
            calendar,
            StartTime,
            StopTime,
            ChunkDuration,
            date_prefix,
            chunk_prefix,
        )

    def get_chunk_by_index(self, index):
        return (self.ChunkIndexStart[index], self.ChunkIndexStop[index])

    def _generate_job_start_end_date_lists(
        self,
        start: cftime.datetime,
        end: cftime.datetime,
        duration: SimDuration,
        periods=None,
        adjust_start=True,
    ):
        start_times = [start]

        if duration.adjust_start:
            adjusted_start = cftime_utils.adjust_start_date(start, duration)
        else:
            adjusted_start = start

        stop_times = [adjusted_start + duration.duration - timedelta(seconds=1)]

        time_gen = time_interval_generator(adjusted_start, duration.duration)

        if (
            periods is not None
        ):  # RD: I think this can be safely removed, if we are requiring users to enter an iso8601 duration
            # Generate exactly 'periods' number of times
            for _ in range(periods):
                start_times.append(next(time_gen))
        elif end is not None:
            # Generate times until the end_time is reached
            for current_time, prev_stop_time in time_gen:
                if current_time > end:
                    break
                start_times.append(current_time)
                stop_times.append(prev_stop_time)
        else:
            raise ValueError("Either 'end_time' or 'periods' must be specified.")

        if stop_times[-1] > end:
            stop_times[-1] = end

        return start_times, stop_times

    def shell_formatted_time_vars(self):
        """
        Create a dict of formatted time/chunk vars to meet the current canesm scripting interface
        """
        formatted_time_vars = {f"number_of_{self.chunk_prefix}s": self.NumChunks}

        # Need to assess where this is needed and if there's another way
        # The variables created here are only used in the archive_run_files task
        # There is the assumption that the model will create history/restarts
        # labeled by month. This will fail if using units smaller than 1 month
        try:
            multiplier = int(self.ChunkDuration.duration.months)
            if int(self.ChunkDuration.duration.years):
                multiplier += int(self.ChunkDuration.duration.years * 12)
        # TODO: Dangerous to catch all exceptions, should remove this.
        except:
            multiplier = 1
            warnings.warn(
                f"\033[93mSelected chunk duration < 1 month. Some environment variables will default to 1 month size and model/postproc tasks which rely on those variables may not be functional.\033[0m",
                UserWarning
            )   
        if multiplier == 0:
            raise ValueError(f"Number of months for {self.chunk_prefix} = 0")
        formatted_time_vars[f"{self.chunk_prefix}_size_months".upper()] = multiplier
        # Should probably replace this^^ with some parsing and calculation of the
        # string variable below VV

        # Add chunk size string to environment
        # This is needed to compute correct date from a loop index (e.g. in Maestro)
        formatted_time_vars[f"{self.chunk_prefix}_size"] = self.chunk_size_str

        return formatted_time_vars


def sim_time_factory(run_dates: dict, timer_name: str):
    """
    Special function for generating specific well-known run timers
    Overlays SimTimer and selects the correct run_dates based on argument

    Parameters:
        run_dates (dict): dictionary of run start/stop times and chunk sizes
        timer_name (str): for now, only "model_submission_job",
                                        "model_inner_loop",
                                        "postproc_submission_job"
    """

    # maps timer_name to variable prefixes in run_dates
    timer_map = {
        "model_submission_job": {
            "date_prefix": "run_segment",
            "chunk_prefix": "model_chunk",
        },
        "model_inner_loop": {
            "date_prefix": "run_segment",
            "chunk_prefix": "model_internal_chunk",
        },
        "postproc_submission_job": {
            "date_prefix": "run_segment",
            "chunk_prefix": "postproc_chunk",
        },
    }

    date_prefix = timer_map[timer_name]["date_prefix"]
    chunk_prefix = timer_map[timer_name]["chunk_prefix"]

    return SimTimer.from_iso(
        timer_name,
        run_dates[f"{date_prefix}_start_time"],
        run_dates[f"{date_prefix}_stop_time"],
        run_dates[f"{chunk_prefix}_size"],
        date_prefix,
        chunk_prefix,
    )


def time_interval_generator(start_time, duration):
    """
    Generator that yields cftime objects, starting from `start_time`, and
    increments by `duration` each time it's called.

    Warning: this is an infinite generator (will run until stopped
    externally with "break", eg.). See _generate_job_start_end_date_lists
    for example usage.

    :param start_time: A cftime object representing the starting time
    :param duration: isodate duration object
    """
    # TODO: refactor this so it contains its own break condition
    current_time = start_time

    while True:
        # Add the duration to the current time
        current_time = current_time + duration

        prev_stop_time = current_time + duration - timedelta(seconds=1)

        # Yield the current time
        yield current_time, prev_stop_time


# Likely be useful for downstream
def format_time_vars(time_dict: dict) -> dict:
    """
    Break a dicts of specified cftime's into component elements (date, year, month, day, hour, minute, second)
    and return a dict of these.

    The keys in the input dict are used to label the elements returned in the output dict

    Example:
        format_time_vars({'run_start' : cftime.DatetimeNoLeap(2016,1,4)} )
             {'run_start_year' : '2016'
              'run_start_month' : '1'...
             }
    """
    formatted_time_vars = {}
    for prefix, this_cftime in time_dict.items():
        formatted_time_vars[prefix + "_date"] = this_cftime.isoformat(
            timespec="seconds"
        )  # iso8601 format, truncated at seconds
        for freq in ["year", "month", "day", "hour", "minute", "second"]:
            formatted_time_vars[prefix + "_" + freq] = getattr(this_cftime, freq)
    return formatted_time_vars
