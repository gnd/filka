#!/bin/bash
#
# splits Nginx logfile into monthly parts
##########################################
USE_EXCLUDE=0

if [[ -z "$1" ]]; then
	print "Usage: $0 <year> [exclude_ips_file]"
	exit
else
	YEAR=$1
	STATDIR="stats_"$YEAR
fi

if [[ ! -z "$2" ]]; then
	EXCLUDE_FILE=$2
	USE_EXCLUDE=1
	echo "Using IP exclude list from $EXCLUDE_FILE"
fi

## clean old data (if any)
if [[ -d $STATDIR ]]; then
	rm -rf $STATDIR/*
else
	mkdir $STATDIR
fi

MON=("Jan" "Feb" "Mar" "Apr" "May" "Jun" "Jul" "Aug" "Sep" "Oct" "Nov" "Dec");
for m in ${MON[@]}
do
	if [[ $USE_EXCLUDE == "1" ]]; then
		cat ../nginx_access_log|grep -a $m"/"$YEAR | grep -vf $EXCLUDE_FILE | tee -a $STATDIR/$YEAR"_access_log" > $STATDIR/$m"_"$YEAR".log"
	else
		cat ../nginx_access_log|grep -a $m"/"$YEAR | tee -a $STATDIR/$YEAR"_access_log" > $STATDIR/$m"_"$YEAR".log"
	fi
done