'''
This is a module containing utilities for handling cftimes, and particularly
generating cftimes from iso8061 strings, and assiting in creating cftime_ranges
appropriate for model chunking.

Various functions here are borrowed, and in cases adapated from xarray, which
itself inherits from pandas (where noted below).
'''

import cftime
import re
from datetime import timedelta
from typing import Tuple

# Possibly replacable with xarray.coding.to_cftime_datetime, but that does not have start/end logic.
def parse_time(time_str: str, cftime_calendar:cftime.datetime, date_type: str = 'start') -> cftime.datetime:
    """
    Parse a time string in iso8601 format and return a cftime date-time object
    for the specified calendar type and date_type.

    Args:
        time_str (str): The time string to parse (iso8601_).
        cftime_calendar (cftime.Datetime): cftime calendar object (e.g. cftime.DatetimeNoleap)
        date_type (str): Specifies if the date is a 'start' or 'end' date (default is 'start').
    Returns:
        (cftime.datetime): The parsed date-time object for the specified calendar.

    If `date_type=start`, any date parameters not specified get set to the beginning
    of the period. If `date_type=end`, any date parameters not specified get set to
    the end of the period.

    Examples:
        parse_time('2016-01', cftime_calendar=cftime.DatetimeNoLeap, date_type='start)
            cftime.DatetimeNoLeap(2016, 1, 1, 0, 0, 0, 0, has_year_zero=True)

        parse_time('2016-01', cftime_calendar=cftime.DatetimeNoLeap, date_type='end)
            cftime.DatetimeNoLeap(2016, 1, 31, 23, 59, 59, 999999, has_year_zero=True)

        parse_time('2016-01-15 16:00', cftime_calendar=cftime.DatetimeNoLeap)
            cftime.DatetimeNoLeap(2016, 1, 15, 16, 0, 0, 0, has_year_zero=True)
    """
    if not time_str:
        raise ValueError("Time string must be provided")
    parsed, resolution = _parse_iso8601_with_reso(cftime_calendar, time_str)
    start, end = _parsed_string_to_bounds(cftime_calendar, resolution, parsed)
    dates = {'start': start, 'end': end}
    try:
        return dates[date_type]
    except KeyError:
        raise ValueError(f'date_type must be one of "start" or "end". Received: {date_type}')


# Part of the hack below
def parse_frequency(freq) -> Tuple[int, str]:
    '''split a frequency string into the multiplier and the
    base frequency (e.g. P12MS n=12, base_freq=MS)
    '''
    #below, matches strings like P1MS, P1Y, PT6H
    #T is optional
    #capture group 1: P or PT; group 2: integer; group 3: time unit
    match = re.match(r"P(T?)(\d+)?(\D+)", freq)
    if not match:
        raise ValueError(f"Frequency '{freq}' is not supported.")

    multiplier = int(match.group(2))
    base_freq = match.group(1) + match.group(3)
    return multiplier, base_freq


# This is a hack, and better replaced with xarray logic
# just have to figure out which functions
def adjust_start_date(start, duration) -> cftime.datetime:
    '''Given a start date with a specified resolution (precision)
       and a frequency (perhaps better duration), adjust the start
       so that it corresponds to the beginning of the "resolution"
       specified in frequency.

       Args:
            start (cftime) : a cftime instance
            duration (str) : the time duration/frequency

       Examples:
       cftime_utils.adjust_start_date(cftime.DatetimeNoLeap(2016,1,14), '12MS')
        cftime.DatetimeNoLeap(2016, 1, 1, 0, 0, 0, 0, has_year_zero=True)

        -> notice the resulting cftime starts on Jan 1, whereas the input time
           started on Jan 14.

        cftime_utils.adjust_start_date(cftime.DatetimeNoLeap(2016,1,14,16,00), '12MS')
            cftime.DatetimeNoLeap(2016, 1, 1, 0, 0, 0, 0, has_year_zero=True)

        cftime_utils.adjust_start_date(cftime.DatetimeNoLeap(2016,1,14,16,00), '1D')
            cftime.DatetimeNoLeap(2016, 1, 14, 0, 0, 0, 0, has_year_zero=True)
    '''

    base_freq = duration.unit

    #some of the units follow xarray conventions, and some also are deprecated in xarray
    date_attrs = {
        'MS': {'day': 1, 'hour': 0, 'minute': 0, 'second': 0},
        'YS': {'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0},
        'DS': {'hour': 0, 'minute': 0, 'second': 0},
        'THS': {'minute': 0, 'second': 0},
        'TMS': {'second': 0},
        'TSS': {},
    }

    try:
        return start.replace(**date_attrs[base_freq])
    except KeyError:
        raise ValueError(f"Frequency '{base_freq}' is not supported.")

# Function below are borrowed from xarray, specifically
# xarray.coding.cftime_range, cftimeindex, times
# In some cases functions were slightly modified for sensible usage here

# For reference, this is the license that appears in xarray/pandas source:
# (c) 2011-2012, Lambda Foundry, Inc. and PyData Development Team
# All rights reserved.

# Copyright (c) 2008-2011 AQR Capital Management, LLC
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

#     * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.

#     * Neither the name of the copyright holder nor the names of any
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# standard calendars recognized by cftime
_STANDARD_CALENDARS = {"standard", "gregorian", "proleptic_gregorian"}
def _is_standard_calendar(calendar: str) -> bool:
    return calendar.lower() in _STANDARD_CALENDARS

def get_date_type(calendar, use_cftime=True):
    """Return the cftime date type for a given calendar name."""
    # NCS - not applicable here
    #if cftime is None:
    #    raise ImportError("cftime is required for dates with non-standard calendars")
    #else:
    #    if _is_standard_calendar(calendar) and not use_cftime:
    #        return _nanosecond_precision_timestamp

    calendars = {
        "noleap": cftime.DatetimeNoLeap,
        "360_day": cftime.Datetime360Day,
        "365_day": cftime.DatetimeNoLeap,
        "366_day": cftime.DatetimeAllLeap,
        "gregorian": cftime.DatetimeGregorian,
        "proleptic_gregorian": cftime.DatetimeProlepticGregorian,
        "julian": cftime.DatetimeJulian,
        "all_leap": cftime.DatetimeAllLeap,
        "standard": cftime.DatetimeGregorian,
    }
    # NCS modified for better error handling
    try:
        return calendars[calendar.lower()]
    except KeyError:
        raise ValueError(f"Unsupported calendar type: {calendar}")


def named(name, pattern):
    return "(?P<" + name + ">" + pattern + ")"

def optional(x):
    return "(?:" + x + ")?"

def trailing_optional(xs):
    if not xs:
        return ""
    return xs[0] + optional(trailing_optional(xs[1:]))

def build_pattern(date_sep=r"\-", datetime_sep=r"T", time_sep=r"\:"):
    pieces = [
        (None, "year", r"\d{4}"),
        (date_sep, "month", r"\d{2}"),
        (date_sep, "day", r"\d{2}"),
        (datetime_sep, "hour", r"\d{2}"),
        (time_sep, "minute", r"\d{2}"),
        (time_sep, "second", r"\d{2}"),
    ]
    pattern_list = []
    for sep, name, sub_pattern in pieces:
        pattern_list.append((sep if sep else "") + named(name, sub_pattern))
        # TODO: allow timezone offsets?
    return "^" + trailing_optional(pattern_list) + "$"


_BASIC_PATTERN = build_pattern(date_sep="", time_sep="")
_EXTENDED_PATTERN = build_pattern()
_CFTIME_PATTERN = build_pattern(datetime_sep=" ")
_PATTERNS = [_BASIC_PATTERN, _EXTENDED_PATTERN, _CFTIME_PATTERN]

def parse_iso8601_like(datetime_string):
    '''
    Given a time string, return a dict, with keys of
    year, month, day, hour, minute, second, and the values
    being the integer date value, or None if it was not
    specified in the input string
    (NCS inference, undocumented in xarray).
    '''
    for pattern in _PATTERNS:
        match = re.match(pattern, datetime_string)
        if match:
            return match.groupdict()
    raise ValueError(
        f"no ISO-8601 or cftime-string-like match for string: {datetime_string}"
    )

def _parse_iso8601_with_reso(date_type, timestr):
    '''
    Parses an iso8061 datestring, and returns a cftime instance
    (of date_type) and a specification of the resolution of
    the date string (i.e. specified down to year, month, day...)

    NCS inference - xarray version undocumented.
    '''
    if cftime is None:
        raise ModuleNotFoundError("No module named 'cftime'")

    default = date_type(1, 1, 1)
    result = parse_iso8601_like(timestr)
    replace = {}

    for attr in ["year", "month", "day", "hour", "minute", "second"]:
        value = result.get(attr, None)
        if value is not None:
            # Note ISO8601 conventions allow for fractional seconds.
            # TODO: Consider adding support for sub-second resolution?
            replace[attr] = int(value)
            resolution = attr
    return default.replace(**replace), resolution

# From xarray
def _parsed_string_to_bounds(date_type, resolution, parsed):
    """Generalization of
    pandas.tseries.index.DatetimeIndex._parsed_string_to_bounds
    for use with non-standard calendars and cftime.datetime
    objects.
    """
    if resolution == "year":
        return (
            date_type(parsed.year, 1, 1),
            date_type(parsed.year + 1, 1, 1) - timedelta(seconds=1),
        )
    elif resolution == "month":
        if parsed.month == 12:
            end = date_type(parsed.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end = date_type(parsed.year, parsed.month + 1, 1) - timedelta(
                seconds=1
            )
        return date_type(parsed.year, parsed.month, 1), end
    elif resolution == "day":
        start = date_type(parsed.year, parsed.month, parsed.day)
        return start, start + timedelta(days=1, seconds=-1)
    elif resolution == "hour":
        start = date_type(parsed.year, parsed.month, parsed.day, parsed.hour)
        return start, start + timedelta(hours=1, seconds=-1)
    elif resolution == "minute":
        start = date_type(
            parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute
        )
        return start, start + timedelta(minutes=1, seconds=-1)
    elif resolution == "second":
        start = date_type(
            parsed.year,
            parsed.month,
            parsed.day,
            parsed.hour,
            parsed.minute,
            parsed.second,
        )
        #currently we don't support sub-second units, so start = end when specifying down to the second
        return start, start
    else:
        raise KeyError

