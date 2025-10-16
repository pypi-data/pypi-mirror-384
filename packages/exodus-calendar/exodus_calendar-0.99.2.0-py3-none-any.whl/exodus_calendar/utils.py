import time
from math import modf, ceil, floor, cos, sin, radians
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

###############################################################################
############################# SUMMARY INFORMATION ##########$##################
###############################################################################
###### |--------Calendar structure before and after epoch year----------| #####
###### |----------------------------------------------------------------| #####
###### |---------------------------Epoch Year---------------------------| #####
###### |-------negative timestamps-----||-----positive timestamps-------| #####
###### |-2^64 ................... -1.0 || 1.0 .................... 2^64 | #####
###### |-------------------------------||-------------------------------| #####
###### |-------negative cycle order----||----positive cycle order-------| #####
###### | 01 02 03 04 ..... 19 20 21 22 || 01 02 03 04 ..... 19 20 21 22 | #####
###### |-------------------------------||-------------------------------| #####
###### |------negative years order-----||-----positive years order------| #####
###### |-10 -9 -8 -7 -6 -5 -4 -3 -2 -1 || +1 +2 +3 +4 +5 +6 +7 +8 +9 +10| #####
###### |-------------------------------||-------------------------------| #####
###### |---negative year month order---||---positive year month order---| #####
###### |[Jan-------Dec] [Jan-------Dec]||[Jan-------Dec] [Jan-------Dec]| #####
###### |-------------------------------||-------------------------------| #####
###### |------negative year dates------||-------positive year dates-----| #####
###### | 01 02 03 04 ..... 51 52 53 54 || 01 02 03 04 ..... 53 54 55 56 | #####
###### |-------------------------------||-------------------------------| #####
###############################################################################

###############################################################################
################################## CONSTANTS ##################################
###############################################################################

# Start year, preliminary designation, can be changed
EPOCH = "1955-04-11 19:21:51+00:00"

EARTH_TIMEZONE = ZoneInfo("UTC")

# Martian sol length in milliseconds:
# 24:39:35.244 seconds
SOL_LENGTH = 88775244

# Terrestrial day length in milliseconds
DAY_LENGTH = 86400000

# The northward equinox year length in sols
# Note that this value is not constant and slowly increases
# Needs to be replaced with better expression
MARS_YEAR_LENGTH = 668.5907
MARS_MONTH_LENGTH = 56 # except December
MARS_SECOND_LENGTH = 1027.49125

# Gregorian year in days
EARTH_YEAR_LENGTH = 365.2425

# Julian year in days
JULIAN_YEAR_LENGTH = 365.25

# 22-year cycle: 
# * 10 668-sol years
# * 11 669-sol years, 
# * 1 670 sol year marks end of cycle (leap year)
YEAR_CYCLE = [ 
    669, 668, 669, 668, 669, 668, 669, 668, 669, 668, 669,
    668, 669, 668, 669, 668, 669, 668, 669, 668, 669, 670
]

MS_PER_CYCLE = sum(YEAR_CYCLE)*SOL_LENGTH
MS_PER_MARS_YEAR = (sum(YEAR_CYCLE)*SOL_LENGTH)/len(YEAR_CYCLE)

# Martian months and duration - 11 months x 56 days, 1 month variable duration
MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
]

# MONTHS: 01  02  03  04  05  06  07  08  09  10  11  12
MONTH_LENGTH = {
    668: [56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 52],
    669: [56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 53],
    670: [56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 54],
}

WEEKDAYS = [
    "Monday", "Tuesday","Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

# STRING CONSTANTS
STR_ANNUAL_ERROR = "Annual error for calendar year in seconds"
STR_AVG_YEAR_LENGTH = "Calendar year length"
STR_MARS_YEARS_TO_1SOL_ERROR = "Martian years to pass for 1 sol error"
STR_EARTH_YEARS_TO_1SOL_ERROR = "Earth years to pass for 1 sol error"

###############################################################################
################################ IMPLEMENTATION ###############################
###############################################################################

def get_solar_longitude_angle(p_milliseconds):
    # Planetary perturbation constants
    PX = {
        "A":[0.007, 0.006, 0.004, 0.004, 0.002, 0.002, 0.002], #deg
        "tau":[2.2353, 2.7543, 1.1177, 15.7866, 2.1354, 2.4694, 32.8493], #Jyr
        "phi":[49.409, 168.173, 191.837, 21.736, 15.704, 95.528, 49.095] #deg
    }
    
    # calcuate julian date offset from January, 1st, 2000
    jd_ut = 2440587.5 + p_milliseconds/DAY_LENGTH
    jd_tt = jd_ut + 69.184/86400
    dT_J2000 = jd_tt - 2451545.0
    
    # calculate orbital elements data
    M_rad = radians(19.3870 + 0.52402075*dT_J2000)
    alpha_fms = 270.3863 + 0.52403840*dT_J2000
    
    # calculate orbital perturbations parameter
    PBS = 0.0
    for i in range(0, len(PX), 1):
        angle = radians(0.98562*dT_J2000/PX["tau"][i]+PX["phi"][i])
        PBS = PBS + PX["A"][i]*cos(angle)

    # calculate angle
    Ls = alpha_fms + (10.691 + 3.0e-7*dT_J2000)*sin(M_rad) \
        + 0.623*sin(2*M_rad) + 0.050*sin(3*M_rad) \
        + 0.005*sin(4*M_rad) + 0.0005*sin(5*M_rad) + PBS

    return (Ls % 360)


def format_raw_time(p_milliseconds, mars_second_on=False):
    if mars_second_on:
        second_length = MARS_SECOND_LENGTH
    else:
        second_length = 1000
    hours_int = (p_milliseconds // (3600*second_length))
    p_milliseconds = p_milliseconds - hours_int*3600*second_length
    minutes_int = p_milliseconds//(60*second_length)
    p_milliseconds = p_milliseconds - minutes_int*60*second_length
    seconds = p_milliseconds / second_length
    sec_frac, sec_int = modf(seconds)
    ms = round(sec_frac*1000)
    # todo - account for ms>1000 when martian second is used?
    if mars_second_on:
        timestamp = "%02d:%02d:%02d.%03d" % (hours_int, minutes_int, sec_int, ms)
    else:
        timestamp = "%02d:%02d:%02d.%03d" % (hours_int, minutes_int, sec_int, ms)
    return timestamp


def martian_time_to_millisec(timestamp, mars_second_on=False):
    ts_s = [float(x) for x in timestamp.split(':')]
    # ts_s = [hours, minutes, seconds]
    if mars_second_on:
        milliseconds = (ts_s[2]+ts_s[1]*60+ts_s[0]*3600)*MARS_SECOND_LENGTH
    else:
        milliseconds = (ts_s[2]+ts_s[1]*60+ts_s[0]*3600)*1000
    return round(milliseconds)


# need to check the implementation again (suspect!)
def negative_milliseconds_to_date(p_delta_ms, mars_second_on=False):
    absolute_milliseconds = abs(p_delta_ms)
    total_cycles = absolute_milliseconds // MS_PER_CYCLE
    # calculate total cycle years passed
    full_cycle_years = total_cycles*len(YEAR_CYCLE)
    ms_residual = absolute_milliseconds % MS_PER_CYCLE
    years_accumulated = 0
    for i in range(len(YEAR_CYCLE)-1, -1, -1):
        if (ms_residual - YEAR_CYCLE[i]*SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - YEAR_CYCLE[i]*SOL_LENGTH
            years_accumulated = years_accumulated + 1
    # calculate current year duration
    year_len = YEAR_CYCLE[len(YEAR_CYCLE)-years_accumulated-1]
    # calculate months elapsed since start of year
    months_accumulated = 0
    for i in range(len(MONTH_LENGTH[year_len])-1, -1, -1):
        if (ms_residual - MONTH_LENGTH[year_len][i]*SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - MONTH_LENGTH[year_len][i]*SOL_LENGTH
            months_accumulated = months_accumulated + 1

    months_accumulated = len(MONTH_LENGTH[year_len]) - months_accumulated
    # calculate days elapsed
    month_duration = MONTH_LENGTH[year_len][months_accumulated-1]
    days_accumulated = 0
    for i in range(month_duration-1, -1, -1):
        if (ms_residual - SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - SOL_LENGTH
            days_accumulated = days_accumulated + 1
    days_accumulated = month_duration - days_accumulated
    # calculate time
    if round(ms_residual)>0:
        tt = format_raw_time(SOL_LENGTH-ms_residual, mars_second_on)
    else:
        tt = format_raw_time(ms_residual, mars_second_on)
        days_accumulated = days_accumulated + 1
        if days_accumulated>month_duration:
            months_accumulated = months_accumulated + 1
            days_accumulated = 1
        if months_accumulated>len(MONTHS):
            months_accumulated = 1
            years_accumulated = years_accumulated - 1
        
    yyyy = - full_cycle_years - years_accumulated - 1
    mm = months_accumulated

    dd= days_accumulated
    wd = WEEKDAYS[(days_accumulated-1) % 7]
    # never year 'zero'
    if yyyy==0:
        return("%04d-%02d-%02d %s, %s" % (yyyy+1, mm, dd, tt, wd))
    else:
        return("%05d-%02d-%02d %s, %s" % (yyyy, mm, dd, tt, wd))


def positive_milliseconds_to_date(p_delta_ms, p_mars_second_on=False):
    milliseconds_since_epoch = p_delta_ms
    total_cycles = milliseconds_since_epoch // MS_PER_CYCLE
    # calculate total cycle years passed
    full_cycle_years = total_cycles*len(YEAR_CYCLE)
    ms_residual = milliseconds_since_epoch % MS_PER_CYCLE
    years_accumulated = 0
    for i in range(0, len(YEAR_CYCLE), 1):
        if (ms_residual - YEAR_CYCLE[i]*SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - YEAR_CYCLE[i]*SOL_LENGTH
            years_accumulated = years_accumulated + 1
    # calculate current year duration
    year_length = YEAR_CYCLE[years_accumulated]
    # calculate months elapsed since start of year
    months_accumulated = 0
    for i in range(0, len(MONTH_LENGTH[year_length]), 1):
        if (ms_residual - MONTH_LENGTH[year_length][i]*SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - MONTH_LENGTH[year_length][i]*SOL_LENGTH
            months_accumulated = months_accumulated + 1
    # calculate days elapsed
    days_accumulated = 0
    month_duration = MONTH_LENGTH[year_length][months_accumulated]
    for i in range(0, month_duration, 1):
        if (ms_residual - SOL_LENGTH)<0:
            break
        else:
            ms_residual = ms_residual - SOL_LENGTH
            days_accumulated = days_accumulated + 1
    # get time
    tt = format_raw_time(ms_residual, p_mars_second_on)
    # adds ones where necessary
    yyyy = full_cycle_years + years_accumulated + 1
    mm = months_accumulated + 1
    dd = days_accumulated + 1
    wd = WEEKDAYS[days_accumulated % 7]
    return("%04d-%02d-%02d %s, %s" %(yyyy, mm, dd, tt, wd))


def positive_dates_to_milliseconds(input_date, p_mars_second_on=False):
    datetimes = input_date.split()
    date_split = [int(x) for x in datetimes[0].split('-')]
    # calculate milliseconds elapsed
    ms_total = 0
    years_elapsed = date_split[0] - 1 
    total_cycles_passed = years_elapsed // len(YEAR_CYCLE)
    ms_total = ms_total + MS_PER_CYCLE*total_cycles_passed
    # add full years
    year_in_current_cycle = years_elapsed - total_cycles_passed*len(YEAR_CYCLE)
    year_length = YEAR_CYCLE[year_in_current_cycle]
    for i in range(0, year_in_current_cycle, 1):
        ms_total = ms_total + YEAR_CYCLE[i]*SOL_LENGTH
    months_elapsed = date_split[1] - 1 
    for i in range(0, months_elapsed, 1):
        ms_total = ms_total + MONTH_LENGTH[year_length][i]*SOL_LENGTH
    days_elapsed = date_split[2] - 1
    for i in range(0, days_elapsed, 1):
        ms_total = ms_total + SOL_LENGTH
    ms_total = ms_total + martian_time_to_millisec(datetimes[1], p_mars_second_on)
    return ms_total

 
def negative_dates_to_milliseconds(p_input_date, p_mars_second_on=False):
    datetimes = p_input_date.split()
    date_split = [int(x) for x in datetimes[0].split('-')]
    # calculate milliseconds elapsed
    ms_total = 0
    years_elapsed = date_split[0] - 1
    # calculate cycles passed 
    total_cycles_passed = years_elapsed // len(YEAR_CYCLE)
    ms_total = ms_total + MS_PER_CYCLE*total_cycles_passed
    # calculate current year length
    year_in_current_cycle = years_elapsed - total_cycles_passed*len(YEAR_CYCLE)
    year_len = YEAR_CYCLE[len(YEAR_CYCLE) - year_in_current_cycle-1]
    for i in range(0, year_in_current_cycle,1):
        ms_total = ms_total + YEAR_CYCLE[len(YEAR_CYCLE)-i-1]*SOL_LENGTH
    months_elapsed = len(MONTHS) - date_split[1]
    for i in range(0, months_elapsed, 1):
        ms_total = ms_total + MONTH_LENGTH[year_len][len(MONTHS)-i-1]*SOL_LENGTH
    days_elapsed = MONTH_LENGTH[year_len][date_split[1]-1] - date_split[2]
    for i in range(0, days_elapsed, 1):
        ms_total = ms_total + SOL_LENGTH
    time_to_ms = martian_time_to_millisec(datetimes[1],p_mars_second_on)
    ms_total = ms_total + (SOL_LENGTH - time_to_ms)
    return -ms_total


def earth_datetime_to_mars_datetime(input_dt, mars_sec_on=False):
    epoch_date = datetime.fromisoformat(EPOCH)
    diff = input_dt - epoch_date
    ms_since_epoch = diff.total_seconds()*1000.0
    if (epoch_date<=input_dt):
        mars_dt = positive_milliseconds_to_date(ms_since_epoch, mars_sec_on)
    else:
        mars_dt = negative_milliseconds_to_date(ms_since_epoch, mars_sec_on)
    Ls = mars_datetime_to_solar_longitude_angle(mars_dt[:23], mars_sec_on)
    date = mars_dt.split(',')[0].split(' ')[0]
    time = mars_dt.split(',')[0].split(' ')[1]
    weekday = mars_dt.split(',')[1].strip(' ')
    return (date, time, weekday, Ls)


def mars_datetime_to_earth_datetime(input_dt, mars_sec_on=False):
    out_ms = mars_datetime_to_earth_datetime_as_ms(input_dt, mars_sec_on)
    out_dt = datetime.fromisoformat(EPOCH) + timedelta(milliseconds=out_ms)
    return out_dt


def mars_datetime_to_earth_datetime_as_ms(input_dt, mars_sec_on=False):
    if input_dt[0] == '-':
        out_ms = negative_dates_to_milliseconds(input_dt[1:], mars_sec_on)
    else:
        out_ms = positive_dates_to_milliseconds(input_dt, mars_sec_on)
    return out_ms


def mars_datetime_now(format="str", mars_sec_on=False):
    timedate = datetime.now(timezone.utc)
    m_d = earth_datetime_to_mars_datetime(timedate, mars_sec_on)
    if format == "str":
        return m_d
    if format == "ms":
        m_td = f"{m_d[0]} {m_d[1]}"
        return mars_datetime_to_earth_datetime_as_ms(m_td, mars_sec_on)
    else:
        return None

def compute_mars_timedelta(p_date_1, p_date_2, mars_sec_on=False):
    time_ms_a = mars_datetime_to_earth_datetime_as_ms(p_date_1, mars_sec_on)
    time_ms_b = mars_datetime_to_earth_datetime_as_ms(p_date_2, mars_sec_on)
    return (time_ms_b-time_ms_a)


def add_timedelta_to_mars_date(p_date, p_milliseconds, mars_sec_on=False):
    start_ms = mars_datetime_to_earth_datetime_as_ms(p_date, mars_sec_on)
    total_ms = start_ms + p_milliseconds
    if total_ms>=0:
        return positive_milliseconds_to_date(total_ms, mars_sec_on)
    else:
        return negative_milliseconds_to_date(total_ms, mars_sec_on)


def mars_datetime_to_solar_longitude_angle(p_mars_datetime, mars_sec_on=False):
    delta_ms = mars_datetime_to_earth_datetime_as_ms(p_mars_datetime, mars_sec_on)
    start_dt = datetime.fromisoformat(EPOCH) + timedelta(milliseconds=delta_ms)
    Ls = round(get_solar_longitude_angle(start_dt.timestamp()*1000),3)
    return Ls

