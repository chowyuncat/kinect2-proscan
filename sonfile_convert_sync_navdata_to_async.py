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

import serial_win

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
    subpaths = ["sdk/external/include/" ]
                # "pantiltsdk/external/include"]
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
# prepare_bvt_package("pantiltsdk/external/include/bvt_python")
# from pantilt import *

filename = r"F:\Temp\GAVIA Plane\file_2014-12-19_10_35_56.723.son"
s = Sonar()
s.open("FILE", filename)

out_filename = r"F:\Temp\GAVIA Plane\asyncnav-file_2014-12-19_10_35_56.723.son"
if os.path.isfile(out_filename):
    os.remove(out_filename)

s_out = Sonar()
s_out.create_file(out_filename, s, "")

head_index = 0

h = s.get_head(head_index)
h_out = s_out.get_head(head_index)

last_unique_timestamp = None
pings_with_unique_timestamps = []

ping_count = h.ping_count
for index in xrange(ping_count):
    p = h.get_ping_metadata_only(index)
    n = p.nav_data_copy
    if n.nav_time != last_unique_timestamp:
        last_unique_timestamp = n.nav_time
        h_out.put_ping(p)
        s_out.put_nav_data(n)
    
    if (index % 1000) == 0:
        print "index %d / %d " % (index, ping_count)

