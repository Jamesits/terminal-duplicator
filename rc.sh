# Terminal recorder
# Add to your *sh.rc
# https://github.com/Jamesits/terminal-duplicator
if [[ $ONRECORD == 'true' ]]; then
	echo "\x1b[31m[⬤ Recording]\x1b[m"
	kill -USR1 `cat /tmp/terminal-dup.pid`
fi
