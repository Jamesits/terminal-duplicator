#!/usr/bin/env bash
DEST=/tmp/terminal-rec

echo "James' Terminal Duplicator"

if [ "$ONRECORD" = "true" ]; then
    echo "You can't record in another recording process."
    exit 1
fi

echo "Preparing files..."
touch $DEST

echo "Connecting..."
python3 ./rec.py --lines `tput lines` --cols `tput cols` --env "`env | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\&/g'`" --pid-file "/tmp/terminal-dup.pid" $@ &

echo "Starting recording..."

ONRECORD="true" script -qF $DEST
if [ $? -ne 0 ]; then
	# somehow script doesn't support "F" options
	ONRECORD="true" script -q -f $DEST
fi

echo "[Exited]" >>$DEST

sleep 2
echo "Record stopped. Quitting..."
kill -2 `cat /tmp/terminal-dup.pid`
rm $DEST
