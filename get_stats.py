#!/usr/bin/python
#
# ## get_stats.py
#
# parses apache logfiles for number of visits / seconds spent watching / data transferred
# logfiles are in the form (use split.sh):
#     Jan_Year.log
#     Feb_Year.log
#     March_Year.log
#     ...
# 
# where the LogFormat is:
#     LogFormat "%v %h %l %u %t \"%r\" %>s %b \"%{Referer}i\""
#
#
# ## Usage
#
# ./get_stats.py <day | month | all> <selectors>
# ./get_stats.py day <year> <month> <day>
# ./get_stats.py month <year> <month>
# ./get_stats.py all <year>
# eg.: ./get_stats.py day 2016 06 06
#
#
# ## Outputs
#
# visits:
#   - a visit is a hit from an ip on a .mp4 file at a specific time
#   - if another hit is seen from the same ip within 5400 seconds of the first encounter
#     it is considered to be a part of the same visit
#   - if a hit from the same ip is seen later than 5400 seconds from the last visit,
#     it is considered to be a new visit
#
# seconds:
#   - in the absence of better data we count the time spent watching as:
#     seconds = time of last hit during a given visit - time of first hit during a given visit
#
# data:
#   - likewise since apache with LogFormat %b shows usually the whole filesize as transferred
#     (even when the transfer was interrupted) we count the data transmitted as:
#     duration of visit * bitrate of the watched video
#   - this is always a lower bound of data transmitted as various browsers employ various 
#     caching strategies, and might actually download much more data
#   - a better step in determining the data transferred is using %O of mod_logio (next year)
#   - the bitrates are stored in the file video_bitrates.txt which is generated using avprobe
#
##############################################################################################

import sys
import time
import datetime
from os.path import basename

days = {'Jan': 31, 'Feb': 28, 'Mar': 31, 'Apr': 30, 'May': 31, 'Jun': 30, 'Jul': 30, 'Aug': 31, 'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31} 
months = ['Jan', 'Feb','Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

#
# gets loglines for a given month
#
def get_month_loglines(logfile):
    f = file(logfile, 'r')
    lines = f.readlines()
    f.close()
    return lines

#
# gets loglines for a given day
#
def get_day_loglines(day, month_loglines):
    daylines = []
    for line in month_loglines:
        if (day in line) and ("mp4" in line) and not ('HTTP/1.1" 404' in line) and (len(line.split()) == 11):
            daylines.append(line)
    return daylines


#
# gets a list of unique ips for a given day
#
def get_day_ips(day_loglines):
    ips = []
    for line in day_loglines:
        if (line.split()[0] not in ips and (len(line.split()) == 11)):
            ips.append(line.split()[0])
    return ips

#
# gets video bitrates
#
def get_bitrates():
    bitrates = {}
    f = file('video_bitrates.txt','r')
    vlines = f.readlines()
    f.close()
    for line in vlines:
        bitrates[line.strip().split()[0]] = int(line.strip().split()[1])
    return bitrates

#
# gets count ips / seconds / bytes for a given day
#
def get_day_totals(ips, loglines, bitrates, is_day):
    visits = 0;
    seconds = 0
    data = 0
    for ip in ips:
        last = 0
        for line in loglines:
            iptime = time.mktime(datetime.datetime.strptime(line.split()[3].replace("[",""), "%d/%b/%Y:%H:%M:%S").timetuple())
            video = basename(line.split()[6])
            bitrate = 0
            if video in bitrates:
                bitrate = bitrates[video] / 8
            # this searches for the length of a given visit
            if (ip in line) and (last == 0):
                visits += 1
                first = iptime
                last = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")              
            if (ip in line) and (iptime - last <= 5400) and (iptime - last > 0):
                last = iptime
                last_str = line.split()[3].replace("[","")
            if (ip in line) and (iptime - last > 5400) and (last != 0):
                #print "ip: %s first: %s last: %s seconds: %d data: %d" % (ip, first_str, last_str, (last - first), ((last - first) * bitrate))
                data += (last - first) * bitrate
                seconds += (last - first)
                visits+=1
                first = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")
                last = iptime
        seconds += (last - first)
        data += (last - first) * bitrate
        if is_day:
            print "IP: %s first: %s last: %s seconds: %d data: %d" % (ip, first_str, last_str, (last - first), ((last - first) * bitrate))  
    return (visits, seconds, data)


#
# main()
#
if len(sys.argv) > 1:
    scope = sys.argv[1]
else:
    print "Usage: %s <day | month | all> <selectors>" % (sys.argv[0])
    print "%s day <year> <month> <day>" % (sys.argv[0])
    print "%s month <year> <month>" % (sys.argv[0])
    print "%s all <year>" % (sys.argv[0])
    print "eg.: %s day 2016 06 06" % (sys.argv[0])
    sys.exit()


if scope == 'day':
    year = sys.argv[2]
    month = int(sys.argv[3])-1
    daynum = sys.argv[4]

    logfile = "%s_%s.log" % (months[month], year)
    monthlines = get_month_loglines(logfile)
    day = "%02d/%s" % (int(daynum), months[month])
    daylines = get_day_loglines(day, monthlines)
    ips = get_day_ips(daylines)
    bitrates = get_bitrates()

    (visits, seconds, data) = get_day_totals(ips, daylines, bitrates, True)
    print "Visits: %d Seconds: %d Data: %f" % (visits, seconds, data)

elif scope == 'month':
    year = sys.argv[2]
    month = int(sys.argv[3])-1
    
    logfile = "%s_%s.log" % (months[month], year)
    monthlines = get_month_loglines(logfile)
    bitrates = get_bitrates()
    total_visits = 0
    total_seconds = 0
    total_data = 0
    for daynum in range(1, days[months[month]]):
        day = "%02d/%s" % (daynum, months[month])
        daylines = get_day_loglines(day, monthlines)
        ips = get_day_ips(daylines)
        (visits, seconds, data) = get_day_totals(ips, daylines, bitrates, False)
        total_visits += visits
        total_seconds += seconds
        total_data += data
        print "Day %d Visits: %d Seconds: %d Data: %f" % (daynum, visits, seconds, data)
    print "Visits: %d Seconds: %d Data: %f" % (total_visits, total_seconds, total_data)

elif scope == 'all':
    year = sys.argv[2]

    total_visits = 0
    total_seconds = 0
    total_data = 0    
    for month in months:
        logfile = "%s_%s.log" % (month, year)
        monthlines = get_month_loglines(logfile)
        bitrates = get_bitrates()
        month_visits = 0
        month_seconds = 0
        month_data = 0
        for daynum in range(1, days[month]):
            day = "%02d/%s" % (daynum, month)
            daylines = get_day_loglines(day, monthlines)
            ips = get_day_ips(daylines)
            (visits, seconds, data) = get_day_totals(ips, daylines, bitrates, False)
            month_visits += visits
            month_seconds += seconds
            month_data += data
        print "%s Visits: %d Seconds: %d Data: %f" % (month, month_visits, month_seconds, month_data)
        total_visits += month_visits
        total_seconds += month_seconds
        total_data += month_data
    print "%s Visits: %d Seconds: %d Data: %f" % (month, total_visits, total_seconds, total_data)

else:
    print "Usage: %s <day | month | all> <selectors>" % (sys.argv[0])
    print "%s day <year> <month> <day>" % (sys.argv[0])
    print "%s month <year> <month>" % (sys.argv[0])
    print "%s all <year>" % (sys.argv[0])
    print "eg.: %s day 2016 06 06" % (sys.argv[0])
