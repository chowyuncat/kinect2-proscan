import sys
import os
import traceback
import subprocess
import itertools
import argparse
import math
import time
import timeit
import signal
import random
import struct


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
prepare_bvt_package("pantiltsdk/external/include/bvt_python")
from pantilt import *


def go_home(pt, speed):
    """
    Slowly move both axes of the PanTilt device to
    the home position of 180 degrees
    """
    pt.set_speed(AXIS_PAN,  speed)
    pt.set_speed(AXIS_TILT, speed)

    print "Moving pan home"
    pt.move_to_angle(AXIS_PAN, 180)
    pt.wait_for_async_command()

    print "Moving tilt home"
    pt.move_to_angle(AXIS_TILT, 180)
    pt.wait_for_async_command()

    print "Exiting"

if __name__ == '__main__':
    # prepare_bvt_package("pantiltsdk/external/include/")
    # from bvt_python import *


    AXIS_PAN  = PanTilt.AXIS_PAN
    AXIS_TILT = PanTilt.AXIS_TILT
    CLOCKWISE        = PanTilt.CLOCKWISE
    COUNTERCLOCKWISE = PanTilt.COUNTERCLOCKWISE

    pt = PanTilt()
    def get_platform_specific_serial_port_name():
        if "win32" in sys.platform:
            return "COM8"
        elif "darwin" in sys.platform:
            return "/dev/cu.usbserial-FTE0AKCX"
        else:
            return "/dev/ttyUSB0"
    device_id = get_platform_specific_serial_port_name()

    line_delay = 5
    pt.line_delay_milliseconds = line_delay 

    # note: setting delay to pan 125, tilt 125
    # then setting back to pan 0, tilt 0
    # always seems to fail on setting the second delay (tilt) to zero

    Logger.target = 'stdout'
    Logger.level2 = 4

    if False:
        device_id = None
        for device_id in serial_win.enumerate_serial_ports():
            pt = PanTilt()
            pt.line_delay_milliseconds = line_delay
            print "Trying serial device '%s'..." % device_id
            try:
                pt.open_fast(device_id)
                print "Found PanTilt device"
                print "Actual comm delay %d" % pt.get_comm_delay_milliseconds(AXIS_PAN)
                break
            except Exception:
                continue
        if device_id is None:
            os._exit(-1)
    else:
        # pt.open_fast(device_id)
        print "Trying serial device '%s'..." % device_id
        pt.open(device_id)



    if True:
        print "Going home quickly"
        go_home(pt, 10.0)
        print "Going home slowly"
        go_home(pt, 0.5)
        time.sleep(2)


    t_process = timeit.default_timer()


    # stops = [2, 45, 90, 135, 180] # 225, 270, 315]
    stops_readonly = [2, 358] # 225, 270, 315]

    # stops = [ 2.0 + i / 2.0 for i in xrange(0, 356 * 2) ]
    speed_index = 0
    # speeds = [10, 5, 2]
    speeds = [0.5, 1, 2, 5]
    speeds.reverse()
    
    num_frames_read = 0

    initial_angle = pt.get_angle(AXIS_PAN)

    depth_frames = []

    num_scans = -1

    try:

        while True:

            while True:
                pt.set_speed(AXIS_PAN, 10)
                relative_degrees = 5.0
                for i in xrange(2):
                    print "Moving to relative angle"
                    pt.move_to_relative_angle(AXIS_PAN, relative_degrees)
                    time.sleep(relative_degrees / pt.get_speed(AXIS_PAN)*.9)
                    print '\a'
                    time.sleep(2)

                print "Going home quickly"
                go_home(pt, 10.0)
                print "Going home slowly"
                go_home(pt, 0.5)
                time.sleep(2)


            num_scans += 1

            stops = list(stops_readonly)
            if abs(initial_angle - stops[0]) > abs(initial_angle - stops[-1]):
                stops.reverse()

            pt.set_speed(AXIS_PAN, 15)
            pt.move_to_angle(AXIS_PAN, stops[0])
            print "waiting for pan to reach initial angle of %.3f" % stops[0]
            pt.wait_for_async_command()
            print "Beginning scan %d..." % num_scans

            moving_forward = True if stops[0] >= initial_angle else False

            speed = speeds[speed_index]
            speed_index = (speed_index + 1) % len(speeds)
            pt.set_speed(AXIS_PAN, speed)

            

            for stop_angle in stops:
                print "Moving to %.3f" % stop_angle

                pt.move_to_angle(AXIS_PAN, stop_angle)

                t0 = timeit.default_timer()
                num_samples = 0

                while True:
                    # angle = pt.get_angle(AXIS_PAN)
                    # raw_angle = pt.get_unfiltered_angle(AXIS_PAN)

                    filt_angle = c_float()
                    filt_time = c_double()
                    raw_angle = c_float()
                    raw_time = c_double()
                    stepper_count = c_int()
                    """ TODO: Can reach this point before the bvtpantilt 'moveto' thread resets the stepper count
                    resulting in a large stepper_count value
                    """
                    pt.get_angle_ex(AXIS_PAN, filt_angle, filt_time, raw_angle, raw_time, stepper_count)
                    filt_angle = filt_angle.value
                    filt_time = filt_time.value
                    raw_angle = raw_angle.value
                    raw_time = raw_time.value
                    stepper_count = stepper_count.value

                    num_samples += 1
                    # print "Elapsed: %4.1f" % (timeit.default_timer() - t_process)
                    sample_rate = num_samples / (timeit.default_timer() - t0)
                    print "Angle %4.2f, Sample Rate: %.3f" % (filt_angle, sample_rate)

                    if math.isnan(filt_angle):
                        raise Exception("Angle was Nan!!")


                    # is_at_end_point = (angle <= stop_angle and dir == COUNTERCLOCKWISE) or (angle >= stop_angle and dir == CLOCKWISE)
                    if not pt.is_async_command_in_progress:
                        print "Current angle is %.3f, but moving to %.3f so waiting for async..." % (filt_angle, stop_angle)
                        pt.wait_for_async_command(); # should return immediately
                        # pt.stop(AXIS_PAN)
                        break
            print "Adding terminal sentinel to write queue"
            write_queue.put(None)
    except:
        print "Caught Exception!"
        e = sys.exc_info()[0]
        print e
        print traceback.format_exc()

        print "Attempting to stop PanTilt..."
        try:
            pt.stop(AXIS_PAN)
            print "Stopped PanTilt"
        except Exception as e:
            print "Stop failed!"
            print e
        print "os.exit..."
        os._exit(-1)

    pt.stop(AXIS_PAN)
