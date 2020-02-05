#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" get_stats.py

    This parses apache logfiles for number of visits / seconds spent watching / data transferred
    logfiles are in the form (use split.sh):
        Jan_Year.log
        Feb_Year.log
        March_Year.log
        ...

    Where the LogFormat is:
        LogFormat "%v %h %l %u %t \"%r\" %>s %b %O \"%{Referer}i\""

    Usage:
        ./get_stats.py <day | month | all> <selectors> <ignored_ips>
        ./get_stats.py day <year> <month> <day> <ignored_ips>
        ./get_stats.py month <year> <month> <ignored_ips>
        ./get_stats.py all <year> <ignored_ips>
        eg.: ./get_stats.py day 2016 06 06 127.0.0.1,6.6.6.6

    Outputs:
        visits:
            - a visit is a hit from an ip on a .mp4 file at a specific time
            - if another hit is seen from the same ip within 5400 seconds of the first encounter
            it is considered to be a part of the same visit
            - if a hit from the same ip is seen later than 5400 seconds from the last visit,
            it is considered to be a new visit

        seconds:
            - in the absence of better data we count the time spent watching as:
            seconds = time of last hit during a given visit - time of first hit during a given visit

        data:
            - no need to account for data for a given visit, it is enough to gather %O for the whole day

        ignored_visits:
            - is a basically the same as visits, just from IPs that were specified as ignored at runtime
            - this is to account for anomalies in the data that are caused by extensive crawling from search engines

        ignored_seconds:
            - when an search engine crawls the site, it can happen that the total amount of seconds spent on the streams
              is almost one full day, which skews the statistics significantly. The ignored_ips option was added
              to account for this fact

    gnd, 2017 - 2019
"""

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
        if (day in line) and ("mp4" in line) and not ('HTTP/1.1" 404' in line) and (len(line.split()) == 12):
            daylines.append(line)
    return daylines


#
# gets a list of unique ips for a given day
#
def get_day_ips(day_loglines):
    ips = []
    for line in day_loglines:
        if (line.split()[0] not in ips and (len(line.split()) == 12)):
            ips.append(line.split()[0])
    return ips

#
# gets video bitrates, not used as of 2018
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
# gets count ips / seconds for a given day
#
def get_day_visits(ips, loglines, is_day, ignore_ips):
    visits = 0
    seconds = 0
    # Remove ignored ips from the list
    if len(ignore_ips) > 0:
        for ip in ignore_ips:
            if ip in ips:
                ips.remove(ip)
    # Process all IPs without the ignored ones
    if is_day:
        print "IP first last seconds"
    for ip in ips:
        last = 0
        first = 0
        for line in loglines:
            iptime = time.mktime(datetime.datetime.strptime(line.split()[3].replace("[",""), "%d/%b/%Y:%H:%M:%S").timetuple())
            # this searches for the length of a given visit - if no last, its the moment when the IP shows up
            if (ip in line) and (last == 0):
                visits += 1
                first = iptime
                last = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")
            # we still see the IP, its not the first time and its part of the same visit
            if (ip in line) and (iptime - last <= 5400) and (iptime - last > 0):
                last = iptime
                last_str = line.split()[3].replace("[","")
            # in case we see ip after 5400 seconds, make it a new visit and finish & account for the old one
            if (ip in line) and (iptime - last > 5400) and (last != 0):
                seconds += (last - first)
                visits+=1
                first = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")
                last = iptime
        # otherwise no more hits from IP, account for the visit
        seconds += (last - first)
        if is_day:
            print "%s %s %s %d" % (ip, first_str, last_str, (last - first))
    # Now do the same for ignored IPs
    visits_ignore = 0
    seconds_ignore = 0
    if is_day:
        print "Ignored_IP first last seconds"
    for ip in ignore_ips:
        last = 0
        first = 0
        for line in loglines:
            iptime = time.mktime(datetime.datetime.strptime(line.split()[3].replace("[",""), "%d/%b/%Y:%H:%M:%S").timetuple())
            # this searches for the length of a given visit - if no last, its the moment when the IP shows up
            if (ip in line) and (last == 0):
                visits_ignore += 1
                first = iptime
                last = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")
            # we still see the IP, its not the first time and its part of the same visit
            if (ip in line) and (iptime - last <= 5400) and (iptime - last > 0):
                last = iptime
                last_str = line.split()[3].replace("[","")
            # in case we see ip after 5400 seconds, make it a new visit and finish & account for the old one
            if (ip in line) and (iptime - last > 5400) and (last != 0):
                seconds_ignore += (last - first)
                visits_ignore+=1
                first = iptime
                first_str = line.split()[3].replace("[","")
                last_str = line.split()[3].replace("[","")
                last = iptime
        # otherwise no more hits from IP, account for the visit
        seconds_ignore += (last - first)
        if is_day:
            print "%s %s %s %d" % (ip, first_str, last_str, (last - first))
    # return total values
    return (visits, seconds, visits_ignore, seconds_ignore)

#
# gets data sent for a given day
#
def get_day_data(loglines, is_day):
    data = 0
    for line in loglines:
        bytes_out = int(line.split()[10])
        data += bytes_out
    if is_day:
        print "Transferred: %d" % (data)
    return (data)

#
# main()
#
if len(sys.argv) > 1:
    scope = sys.argv[1]
else:
    print "Usage: %s <day | month | all> <selectors>" % (sys.argv[0])
    print "%s day <year> <month> <day> <ignored_ips>" % (sys.argv[0])
    print "%s month <year> <month> <ignored_ips>" % (sys.argv[0])
    print "%s all <year> <ignored_ips>" % (sys.argv[0])
    print "eg.: %s day 2016 06 06 ignored.ips" % (sys.argv[0])
    sys.exit()


if scope == 'day':
    year = sys.argv[2]
    month = int(sys.argv[3])-1
    daynum = sys.argv[4]
    ignored_ips = []
    if len(sys.argv) > 5:
        print "Reading ignored IPS file"
        ignored_ips_file = sys.argv[5]
        f = file(ignored_ips_file, 'r')
        tmp = f.readlines()
        f.close()
        for ip in tmp:
            ignored_ips.append(ip.strip())
    logfile = "%s_%s.log" % (months[month], year)
    monthlines = get_month_loglines(logfile)
    day = "%02d/%s" % (int(daynum), months[month])
    daylines = get_day_loglines(day, monthlines)
    ips = get_day_ips(daylines)
    (visits, seconds, ignored_visits, ignored_seconds) = get_day_visits(ips, daylines, True, ignored_ips)
    data = get_day_data(daylines, True)
    print "Visits Seconds Data Ignored_visits Ignored_seconds"
    print "%d %d %d %d %d" % (visits, seconds, data, ignored_visits, ignored_seconds)

elif scope == 'month':
    year = sys.argv[2]
    month = int(sys.argv[3])-1
    ignored_ips = []
    if len(sys.argv) > 4:
        print "Reading ignored IPS file"
        ignored_ips_file = sys.argv[4]
        f = file(ignored_ips_file, 'r')
        tmp = f.readlines()
        f.close()
        for ip in tmp:
            ignored_ips.append(ip.strip())
    logfile = "%s_%s.log" % (months[month], year)
    monthlines = get_month_loglines(logfile)
    total_visits = 0
    total_seconds = 0
    total_ignored_visits = 0
    total_ignored_seconds = 0
    total_data = 0
    print "Day Visits Seconds Data Ignored_visits Ignored_seconds"
    for daynum in range(1, days[months[month]]):
        day = "%02d/%s" % (daynum, months[month])
        daylines = get_day_loglines(day, monthlines)
        ips = get_day_ips(daylines)
        (visits, seconds, ignored_visits, ignored_seconds) = get_day_visits(ips, daylines, False, ignored_ips)
        data = get_day_data(daylines, False)
        total_visits += visits
        total_seconds += seconds
        total_ignored_visits += ignored_visits
        total_ignored_seconds += ignored_seconds
        total_data += data
        print "%d %d %d %d %d %d" % (daynum, visits, seconds, data, ignored_visits, ignored_seconds)
    print "%s %d %d %d %d %d" % ("Total", total_visits, total_seconds, total_data, total_ignored_visits, total_ignored_seconds)

elif scope == 'all':
    year = sys.argv[2]
    ignored_ips = []
    if len(sys.argv) > 3:
        print "Reading ignored IPS file"
        ignored_ips_file = sys.argv[3]
        f = file(ignored_ips_file, 'r')
        tmp = f.readlines()
        f.close()
        for ip in tmp:
            ignored_ips.append(ip.strip())
    total_visits = 0
    total_seconds = 0
    total_ignored_visits = 0
    total_ignored_seconds = 0
    total_data = 0
    print "Month Visits Seconds Data Ignored_visits Ignored_seconds"
    for month in months:
        logfile = "%s_%s.log" % (month, year)
        monthlines = get_month_loglines(logfile)
        month_visits = 0
        month_seconds = 0
        month_ignored_visits = 0
        month_ignored_seconds = 0
        month_data = 0
        for daynum in range(1, days[month]):
            day = "%02d/%s" % (daynum, month)
            daylines = get_day_loglines(day, monthlines)
            ips = get_day_ips(daylines)
            (visits, seconds, ignored_visits, ignored_seconds) = get_day_visits(ips, daylines, False, ignored_ips)
            data = get_day_data(daylines, False)
            month_visits += visits
            month_seconds += seconds
            month_ignored_visits += ignored_visits
            month_ignored_seconds += ignored_seconds
            month_data += data
        print "%s %d %d %d %d %d" % (month, month_visits, month_seconds, month_data, month_ignored_visits, month_ignored_seconds)
        total_visits += month_visits
        total_seconds += month_seconds
        total_ignored_visits += month_ignored_visits
        total_ignored_seconds += month_ignored_seconds
        total_data += month_data
    print "%s %d %d %d %d %d" % ("Total", total_visits, total_seconds, total_data, total_ignored_visits, total_ignored_seconds)

else:
    print "Usage: %s <day | month | all> <selectors> <ignored_ips>" % (sys.argv[0])
    print "%s day <year> <month> <day> <ignored_ips>" % (sys.argv[0])
    print "%s month <year> <month> <ignored_ips>" % (sys.argv[0])
    print "%s all <year> <ignored_ips>" % (sys.argv[0])
    print "eg.: %s day 2016 06 06 ignored.ips" % (sys.argv[0])
