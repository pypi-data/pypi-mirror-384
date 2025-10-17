#!/usr/bin/env python3
import argparse
import datetime
import logging
import time

from tstring import render

import tstring_logger

def expensive_function(x):
    time.sleep(1)
    return 2 * x

def main():
    logging.basicConfig()
    lg = logging.getLogger("demo")
    hour = datetime.datetime.now().hour
    print(1)
    lg.debug(test := t"The thing happened with {expensive_function:!fn} {7} at hour {hour}")
    print(2)
    lg.setLevel(logging.DEBUG)
    lg.debug(test)
    print(3)



if __name__ == "__main__":
    main()

