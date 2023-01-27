#!/bin/bash
#
# splits Apache logfile into monthly parts
##########################################

if [[ -z "$1" ]]; then
	print "Usage: $0 <year>"
	exit
else
	YEAR=$1
	STATDIR="stats_"$YEAR
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
	cat ../apache_access_log|grep -a $m"/"$YEAR | tee -a $STATDIR/$YEAR"_access_log" > $STATDIR/$m"_"$YEAR".log"
done
