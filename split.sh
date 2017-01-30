#!/bin/bash
#
# splits Apache logfile into monthly parts
##########################################
if [[ -z "$1" ]]; then
	print "Usage: $0 <year>"
	exit
fi

YEAR=$1
rm $YEAR"_access_log"
MON=("Jan" "Feb" "Mar" "Apr" "May" "Jun" "Jul" "Aug" "Sep" "Oct" "Nov" "Dec");
for m in ${MON[@]}
do
	cat ../apache_access_log|grep $m"/"$YEAR | tee -a $YEAR"_access_log" > $m"_"$YEAR".log"
done
