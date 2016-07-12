# Terminal Duplicator

An easy way for sharing your terminal content in real time through a web page.
终端内容网页实时直播，弹幕交互 + 视频。

![Demo](https://cloud.githubusercontent.com/assets/1297257/14592671/d9c9ac38-0553-11e6-8678-f964d7da793f.gif)

This is a demo project winning 1st award on "2016 龙驰杯浙江高校 hackathon 大赛".

## Usage

Dependency: 
 * Python 3 (can be invoked with `python3`, otherwise edit `record.sh`)
 * requests (`pip3 install requests`)

Clone `master` branch and run `record.sh`. This will start a new shell with its content broadcasted to web. 

URL can be displayed by sending USR1 to record process (```kill -USR1 `cat /tmp/terminal-dup.pid` ```). To be more user-friendly, `source rc.sh` in the end of your shell's rc script.

We use Wilddog to deliver data. Online clients are limited to 50 for free account so you can register one yourself and change API URL (in web service and use `record.sh -u https://example.wilddogio.com/` to start service). 

## Author
 * Jamesits
 * Joway
 * WPH95

## License

This software, except all extern library used by this software, is licensed under CC BY-NC-SA 4.0 International.
