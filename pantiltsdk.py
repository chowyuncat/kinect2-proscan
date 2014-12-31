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

from lf2 import *


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


class DepthWithAngle(object):
    def __init__(self, depth_frame, angle, raw_angle):
        self.depth_frame = depth_frame
        self.angle = angle
        self.raw_angle = raw_angle

class PointsWithAngle(object):
    def __init__(self, points, filt_angle, raw_angle, filt_time, raw_time, stepper_count):
        self.points = points
        self.filt_angle = filt_angle
        self.raw_angle = raw_angle
        self.filt_time = filt_time
        self.raw_time = raw_time
        self.stepper_count = stepper_count

def write_points(points, angle, an_xyz_file):
    for p in points:
        x = p[1]
        y = p[2]
        z = p[0]
        cos_a = math.cos( - angle * math.pi / 180.0)
        sin_a = math.sin( - angle * math.pi / 180.0)
        xp = x * cos_a  - y * sin_a
        yp = y * cos_a  + x * sin_a
        # an_xyz_file.write("%.4f, %.4f, %.4f\n" % (xp, yp, z))
        an_xyz_file.write("%f, %f, %f\n" % (xp, yp, z))

def write_colored_points(points, 
    pan_angle, tilt_angle,
    raw_pan_angle,
    filt_time,
    raw_time,
    stepper_count,
    an_xyz_file):
    tilt_angle_norm = tilt_angle - 180.0

    cos_a = math.cos( - pan_angle * math.pi / 180.0)
    sin_a = math.sin( - pan_angle * math.pi / 180.0)

    cos_b = math.cos( - tilt_angle_norm * math.pi / 180.0)
    sin_b = math.sin( - tilt_angle_norm * math.pi / 180.0)
    
    for p in points:
        x = p[2]
        y = p[0]
        z = p[1] # correct

        r = p[3]
        g = p[4]
        b = p[5]
        
        xp = x * cos_a  - y * sin_a
        yp = y * cos_a  + x * sin_a
        # an_xyz_file.write("%f, %f, %f, %f, %f, %f\n" % (xp, yp, z, r, g, b))
        
        x = xp
        y = yp
        z = z
        
        xt = x * cos_b  - z * sin_b
        zt = z * cos_b  + x * sin_b
        yt = y
        #an_xyz_file.write("%f, %f, %f, %f, %f, %f\n" % (xt, yt, zt, r, g, b))
        write_args = (xt, yt, zt, r, g, b, pan_angle, raw_pan_angle, filt_time, raw_time, stepper_count)
        an_xyz_file.write("%f %f %f %d %d %d %f %f %lf %lf %d\n" % write_args)


def write_func(queue):
    DEG_PER_STEP = 0.0102272727272727
    try:
        while True:
            leading_sentinel = queue.get()
            if type(leading_sentinel) is not str:
                print "Type of sentinel is %s" % str(leading_sentinel)
                raise Exception("Leading entry in write_queue must be a filename string")
            print "write_func creating new file '%s'" % leading_sentinel
            fxyz = open(leading_sentinel, "w")
            fxyz_raw = open(leading_sentinel + ".raw.xyz", "w")
            fxyz_relative = open(leading_sentinel + ".stepper.xyz", "w")
            while True:
                entry = queue.get()
                if entry is None:
                    break
                if type(entry) is DepthWithAngle:
                    points = get_xyz_from_depth_frame(entry.depth_frame, True)
                    write_points(points, entry.filt_angle, fxyz)
                    write_points(points, entry.raw_angle, fxyz_raw)
                elif type(entry) is PointsWithAngle:
                    points = entry.points
                    tilt_angle = 180
                    relative_angle = entry.stepper_count * DEG_PER_STEP
                    write_colored_points(points, entry.filt_angle, tilt_angle, entry.raw_angle, entry.filt_time, entry.raw_time, entry.stepper_count, fxyz)
                    write_colored_points(points, entry.raw_angle,  tilt_angle, entry.raw_angle, entry.filt_time, entry.raw_time, entry.stepper_count, fxyz_raw)
                    write_colored_points(points, relative_angle,  tilt_angle, entry.raw_angle, entry.filt_time, entry.raw_time, entry.stepper_count, fxyz_relative)
                else:
                    raise Exception("write_queue popped wrong type")
            fxyz.close()
            fxyz_raw.close()
    except:
        print "Caught exception in write_func:"
        print sys.exc_info()[0]
        print traceback.format_exc()
        os._exit(-1)
    finally:
        print "Exiting write_func"

def take_snapshots():
    # full_snapshot_stops = [2, 45, 90, 135, 180, 225, 270, 315, 358]

    full_snapshot_tilt_stops = [180]
    full_snapshot_pan_stops = [2, 70, 140, 210, 280]

    pt.set_speed(AXIS_TILT, 2.0)
    pt.set_speed(AXIS_PAN, 15)

    snapshot_xyz = open("lf_snapshots.xyz", "w")
    smooth_snapshot_xyz = open("lf_smooth_snapshots.xyz", "w")


    for tilt_stop in full_snapshot_tilt_stops:
        pt.move_to_angle(AXIS_TILT, tilt_stop)
        pt.wait_for_async_command()
        tilt_angle = pt.get_angle(AXIS_TILT)

        pan_stops = list(full_snapshot_pan_stops)
        if abs(initial_angle - pan_stops[0]) > abs(initial_angle - pan_stops[-1]):
            pan_stops.reverse()
        for pan_stop in pan_stops:
            pt.move_to_angle(AXIS_PAN, pan_stop)
            print "waiting for pan to reach full snapshot angle of %.3f" % pan_stop
            pt.wait_for_async_command()
            pan_angle = pt.get_angle(AXIS_PAN)
            if False:
                depth_frame = kinect.lf2_get_depth_frame()
                points = get_xyz_from_depth_frame(depth_frame, None)
                write_points(points, angle, snapshot_xyz)
            else:
                # points = kinect.lf2_get_points()
                points = kinect.lf2_get_points()
                write_colored_points(points, pan_angle, tilt_angle, 0, 0, 0, 0, snapshot_xyz)

                points = kinect.lf2_get_time_smoothed_points()
                write_colored_points(points, pan_angle, tilt_angle, 0, 0, 0, 0, smooth_snapshot_xyz)
    snapshot_xyz.close()
    smooth_snapshot_xyz.close()

def go_home(pt):
    """
    Slowly move both axes of the PanTilt device to
    the home position of 180 degrees
    """
    pt.set_speed(AXIS_PAN,  0.5)
    pt.set_speed(AXIS_TILT, 0.5)

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

    kinect = None
    if False:
        kinect = KinectMock()
    else:
        kinect = Kinect()
    kinect.lf2_open()
    kinect.lf2_start_streaming()
    depth_frame = kinect.lf2_get_depth_frame()

    orient = Orientation()

    AXIS_PAN  = PanTilt.AXIS_PAN
    AXIS_TILT = PanTilt.AXIS_TILT
    CLOCKWISE        = PanTilt.CLOCKWISE
    COUNTERCLOCKWISE = PanTilt.COUNTERCLOCKWISE

    pt = PanTilt()
    def get_platform_specific_serial_port_name():
        if "win32" in sys.platform:
            return "COM4"
        elif "darwin" in sys.platform:
            return "/dev/cu.usbserial-FTE0AKCX"
        else:
            return  "/dev/ttyUSB0"
    device_id = get_platform_specific_path()

    line_delay = 0
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
        device_id = "COM8"
        # pt.open_fast(device_id) 
        pt.open(device_id)
        pt.hardware_comm_delay_milliseconds = 0



    if False:
        go_home(pt)


    write_queue = multiprocessing.JoinableQueue(16)
    writer = multiprocessing.Process(target=write_func, args=(write_queue,))
    writer.start()

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

        take_snapshots()
        # os._exit(-1)

        while True:
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

            xyz_filename = "lf2_speed_%3.2f_%04d.xyz" % (speed, num_scans)
            write_queue.put(xyz_filename)

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

                    if True:
                        num_frames_read += 1
                        t0_depth_grab = timeit.default_timer()
                        # depth_frame = kinect.lf2_get_depth_frame()
                        points = kinect.lf2_get_points_center_column()
                        t1_depth_grab = timeit.default_timer()
                        depth_grab_ms = int((t1_depth_grab - t0_depth_grab) * 1000)
                        #### print "Acquired depth frame in %d ms." % depth_grab_ms

                        # degrees_per_step 0.0102272727272727
                        if moving_forward:
                            stepper_count = -stepper_count

                        # entry = DepthWithAngle(depth_frame, angle, raw_angle)
                        entry = PointsWithAngle(points, filt_angle, raw_angle, filt_time, raw_time, stepper_count)
                        queue_timeout_sec = 2
                        write_queue.put(entry, True, queue_timeout_sec)

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

        print "Terminating writer"
        writer.terminate()

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

    kinect.lf2_stop_streaming()
    kinect.lf2_close()

