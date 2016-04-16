# This code is modefied from http://www.cnblogs.com/bufferfly/p/4878688.html
# to work under Python 3 and fixed various bugs.
#
# https://github.com/Jamesits/netease-music-status
# by James Swineson
# 2016-02-20

import os
import sys
import time


class Tail(object):
    """
    Python-Tail - Unix tail follow implementation in Python.

    python-tail can be used to monitor changes to a file.

    Example:
        import tail

        # Create a tail instance
        t = tail.Tail('file-to-be-followed')

        # Register a callback function to be called when a new line is found in the followed file.
        # If no callback function is registerd, new lines would be printed to standard out.
        t.register_callback(callback_function)

        # Follow the file with 5 seconds as sleep time between iterations.
        # If sleep time is not provided 1 second is used as the default time.
        t.follow(s=5)
    """

    ''' Represents a tail command. '''

    def __init__(self, file, callback=sys.stdout.write, encoding='utf-8'):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed. '''

        self.encoding = encoding
        self.check_file_validity(file)
        self.tailed_file = file
        self.callback = None
        self.register_callback(callback)

        self.try_count = 0

        try:
            self.file_ = open(self.tailed_file, "rb")
            self.size = os.path.getsize(self.tailed_file)

            # Go to the end of file
            self.file_.seek(0, 2)
        except:
            raise

    def reload_tailed_file(self):
        """ Reload tailed file when it be empty be `echo "" > tailed file`, or
            segmentated by logrotate.
        """
        try:
            self.file_ = open(self.tailed_file, "rb")
            self.size = os.path.getsize(self.tailed_file)

            # Go to the head of file
            self.file_.seek(0, 1)

            return True
        except:
            return False

    def follow(self, interval=0.01):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            interval - Number of seconds to wait between each iteration; Defaults to 1. """

        while True:
            _size = os.path.getsize(self.tailed_file)
            if _size < self.size:
                while self.try_count < 10:
                    if not self.reload_tailed_file():
                        self.try_count += 1
                    else:
                        self.try_count = 0
                        self.size = os.path.getsize(self.tailed_file)
                        break
                    time.sleep(0.1)

                if self.try_count == 10:
                    raise Exception("Open %s failed after try 10 times" % self.tailed_file)
            else:
                self.size = _size

            curr_position = self.file_.tell()
            line = self.file_.read().decode(self.encoding)
            # if not line:
            #     self.file_.seek(curr_position)
            # elif not line.endswith("\n"):
            #     self.file_.seek(curr_position)
            # else:
            if len(line) > 0:
                self.callback(line)
            time.sleep(interval)

    def register_callback(self, func):
        """ Overrides default callback function to provided function.

            Arguments:
                func - the callback function
        """
        self.callback = func

    @staticmethod
    def check_file_validity(file):
        """ Check whether the a given file exists, readable and is a file.

            Arguments:
                file - the file path to be checked.
        """
        if not os.access(file, os.F_OK):
            raise TailError("File '%s' does not exist" % (file))
        if not os.access(file, os.R_OK):
            raise TailError("File '%s' not readable" % (file))
        if os.path.isdir(file):
            raise TailError("File '%s' is a directory" % (file))


class TailError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
        t = Tail(file)
        t.register_callback(lambda x: print(x))
        t.follow()
    else:
        print("Please specify file name.")
