import sys
import os
import traceback
import subprocess
import itertools
import argparse
import math
import threading
import time
import timeit
import signal
import Queue
import multiprocessing
import random
import struct
import uuid


def get_platform_specific_path():
    package_path_prefix_win= "D:/devel/blueview/svn/blueview/Dev4.0-gitsvn/"
    package_path_prefix_osx = "/Users/catz/devel/blueview/Dev4.0-gitsvn/"
    package_path_prefix_linux = "/work/catz_OSX/devel/blueview/Dev4.0-gitsvn/"
    if "win32" in sys.platform:
        return package_path_prefix_win
    elif "darwin" in sys.platform:
       return package_path_prefix_osx
    else:
        return package_path_prefix_linux

def prepare_all_bvt_packages():
    package_path_prefix = get_platform_specific_path()
    subpaths = ["sdk/external/include/",
                "pantiltsdk/external/include"]
    for subpath in subpaths:
        package_path = package_path_prefix + "/" + subpath
        print "Inserting '%s' into sys.path" % package_path
        sys.path.insert(0, package_path)

def prepare_bvt_package(subpath):
    package_path_prefix = get_platform_specific_path()
    package_path = package_path_prefix + "/" + subpath
    print "Inserting '%s' into sys.path" % package_path
    sys.path.insert(0, package_path)

prepare_bvt_package("sdk/external/include/")
from bvt_python import *
# prepare_all_bvt_packages()

s = Sonar()
filename = r"F:\Temp\GAVIA Plane\file_2014-12-19_10_35_56.723.son"

f = open(filename, 'r', 0)
f.close()


# filename = r"D:\Sonar Output\Pipeline Downward Pointing\file_2014-03-22_21_25_59.595 Sandy Bottom.son"
# filename = r"Z:\Engineering\Projects\Current\OEM\XXXX_Gavia_MB2250-W-DL\Test Data\Boat Test\Blueview\141219_Blueview_Run\files\file_2014-12-19_10_35_56.723.son"
s.open("FILE", filename)

h = s.get_head(0)

last_unique_timestamp = None
pings_with_unique_timestamps = []

def benchmark_entire_son_file(function):
    print "Benchmarking with function: %s" % repr(function)
    begin = timeit.default_timer()
    index_win = -1
    begin_win = begin
    ping_count = h.ping_count

    for index in xrange(ping_count):
        # p = h.get_ping_metadata(index)
        p = function(h, index)
        # if p.nav_data_copy.nav_time != last_unique_timestamp:
        #     last_unique_timestamp = p.nav_data_copy.nav_time
        #     pings_with_unique_timestamps.append((index, last_unique_timestamp))
        #     print "Ping %d has unique timestamp %f" % (index, last_unique_timestamp)
        if (index % 1000) == 0:
            now = timeit.default_timer()
            print "index %d / %d " % (index, ping_count)
            pps = (index + 1)  / (now - begin) 
            pps_win = (index - index_win) / (now - begin_win) 
            print "pings / sec all: %.3f" % pps
            print "pings / sec win: %.3f" % pps_win
            index_win = index
            begin_win = now
            print "lat: %f" % p.nav_data_copy.latitude


def benchmark_entire_son_file2(get_object, get_function, count):
    print "Benchmarking with function: %s" % repr(get_function)
    begin = timeit.default_timer()
    index_win = -1
    begin_win = begin

    for index in xrange(count):
        p = get_function(get_object, index)
        # if p.nav_data_copy.nav_time != last_unique_timestamp:
        #     last_unique_timestamp = p.nav_data_copy.nav_time
        #     pings_with_unique_timestamps.append((index, last_unique_timestamp))
        #     print "Ping %d has unique timestamp %f" % (index, last_unique_timestamp)
        if (index % 1000) == 0:
            now = timeit.default_timer()
            print "index %d / %d " % (index, count)
            pps = (index + 1)  / (now - begin) 
            pps_win = (index - index_win) / (now - begin_win) 
            print "pings / sec all: %.3f" % pps
            print "pings / sec win: %.3f" % pps_win
            index_win = index
            begin_win = now
            print "lat: %f" % p.nav_data_copy.latitude


# benchmark_entire_son_file(Head.get_ping)
# benchmark_entire_son_file(Head.get_ping_metadata_only)
benchmark_entire_son_file2(s, Sonar.get_nav_data_copy, s.nav_data_count)
