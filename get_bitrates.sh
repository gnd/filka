#!/bin/bash
#
# create a list of all current videos and their bitrates
#
# This is not used as of 2018 
#
########################################################

if [[ -z $1 ]]; then
	echo "Usage $0 <logfile> <rootdir>"
	exit
fi
if [[ -z $2 ]]; then
	echo "Usage $0 <logfile> <rootdir>"
	exit
fi

LOG_FILE=$1
ROOT_DIR=$2
rm video_bitrates.txt

for FILE in `cat $LOG_FILE |grep mp4 |grep -v dl.php|awk {'print $7;'}|sort|uniq`
do
	if [ -f $vid ]; then
		VIDEO=$ROOT_DIR$FILE
		TYPE=`file $VIDEO|awk {'print $4;'}`
		if [[ $TYPE == "MP4" ]]; then
			BITRATE=`avprobe $VIDEO 2>&1 |grep bitrate|awk {'print $6;'}`
			BITS=$(($BITRATE * 1024))
			echo "$FILE $BITS" >> video_bitrates.txt
		fi
	fi
done
