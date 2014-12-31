from ctypes import *
import math
import sys

dll_name = None
if "win32" in sys.platform:
    dll_name = "C:/Users/Cat/Documents/DepthBasics-D2D/Release/kinect2_capi.dll"
    dll_name = r"""D:\devel\blueview\svn\blueview\python-bindings\kinect2_capi\kinect2_capi\Release\kinect2_capi.dll"""
elif "darwin" in sys.platform:
    dll_name = "/Users/catz/devel/third-party/libfreenect2-wiedemeyer/examples/protonect/lib/liblf2_capi.dylib"


_DEPTH_WIDTH  = 512
_DEPTH_HEIGHT = 424
_MAX_VALID_DEPTH = 4500

def _check_func(retval):
    if retval != 0:
        raise Exception("LF2_CAPI returned error %d" % retval)

class Kinect():
    def __init__(self):
        self._handle = c_void_p()

    def lf2_open(self):
        _check_func( dll.lf2_open(self._handle) )

    def lf2_close(self):
        _check_func( dll.lf2_close(self._handle) )

    def lf2_start_streaming(self):
        _check_func( dll.lf2_start_streaming(self._handle) )

    def lf2_stop_streaming(self):
        _check_func( dll.lf2_stop_streaming(self._handle) )

    def lf2_get_depth_frame(self):
        num_floats = int(_DEPTH_WIDTH*_DEPTH_HEIGHT)
        c_float_buffer_t = c_float * num_floats
        float_buffer = c_float_buffer_t()
        _check_func( dll.lf2_get_depth_frame(self._handle, float_buffer, num_floats) )
        return [float_buffer[i] for i in range(num_floats)]

    def lf2_get_points(self):
        num_floats = int(_DEPTH_WIDTH*_DEPTH_HEIGHT*6)
        c_float_buffer_t = c_float * num_floats
        float_buffer = c_float_buffer_t()
        _check_func( dll.lf2_get_points(self._handle, float_buffer, num_floats) )
        # return [float_buffer[i] for i in range(num_floats)]
        points = []
        for i in range(0, num_floats, 6):
            if (float_buffer[i+0] == 0.0 and 
                float_buffer[i+1] == 0.0 and
                float_buffer[i+2] == 0.0):
               continue
            points.append((
                float_buffer[i+0],
                float_buffer[i+1],
                float_buffer[i+2],
                float_buffer[i+3],
                float_buffer[i+4],
                float_buffer[i+5]))
        return points

    def lf2_get_time_smoothed_points(self):
        num_floats = int(_DEPTH_WIDTH*_DEPTH_HEIGHT*6)
        c_float_buffer_t = c_float * num_floats
        float_buffer = c_float_buffer_t()
        _check_func( dll.lf2_get_time_smoothed_points(self._handle, float_buffer, num_floats) )
        # return [float_buffer[i] for i in range(num_floats)]
        points = []
        for i in range(0, num_floats, 6):
            if (float_buffer[i+0] == 0.0 and 
                float_buffer[i+1] == 0.0 and
                float_buffer[i+2] == 0.0):
               continue
            points.append((
                float_buffer[i+0],
                float_buffer[i+1],
                float_buffer[i+2],
                float_buffer[i+3],
                float_buffer[i+4],
                float_buffer[i+5]))
        return points

    def lf2_get_points_center_column(self):
        num_floats = int(_DEPTH_WIDTH*_DEPTH_HEIGHT*6)
        c_float_buffer_t = c_float * num_floats
        float_buffer = c_float_buffer_t()
        _check_func( dll.lf2_get_points_center_column(self._handle, float_buffer, num_floats) )
        # return [float_buffer[i] for i in range(num_floats)]
        points = []

        w = _DEPTH_WIDTH
        h = _DEPTH_HEIGHT

        for y in xrange(0, h):
            for x in xrange(0, w):
                if x < 212 or x > 212:
                    continue
                i = int(y * w + x) * int(6)
                if (float_buffer[i+0] == 0.0 and 
                    float_buffer[i+1] == 0.0 and
                    float_buffer[i+2] == 0.0):
                   continue
                points.append((
                    float_buffer[i+0],
                    float_buffer[i+1],
                    float_buffer[i+2],
                    float_buffer[i+3],
                    float_buffer[i+4],
                    float_buffer[i+5]))
        return points

class KinectMock():
    def __init__(self):
        self._handle = c_void_p()

    def lf2_open(self):
        self._opened = True

    def lf2_close(self):
        self._opened = False

    def lf2_start_streaming(self):
        pass

    def lf2_stop_streaming(self):
            pass

    def lf2_get_depth_frame(self):
        return [float(i) for i in xrange(_DEPTH_WIDTH * _DEPTH_HEIGHT)]

if True:
    dll = CDLL(dll_name) # , DEFAULT_MODE, None, True, False)
    dll.lf2_open.restype = c_int
    dll.lf2_open.argtypes = (POINTER(c_void_p), )

    dll.lf2_close.restype = c_int
    dll.lf2_close.argtypes = (c_void_p, )

    dll.lf2_start_streaming.restype = c_int
    dll.lf2_start_streaming.argtypes = (c_void_p, )

    dll.lf2_stop_streaming.restype = c_int
    dll.lf2_stop_streaming.argtypes = (c_void_p, )

    dll.lf2_get_depth_frame.restype = c_int
    dll.lf2_get_depth_frame.argtypes = (c_void_p, POINTER(c_float), c_int, )

    dll.lf2_get_points.restype = c_int
    dll.lf2_get_points.argtypes = (c_void_p, POINTER(c_float), c_int, )

    dll.lf2_get_time_smoothed_points.restype = c_int
    dll.lf2_get_time_smoothed_points.argtypes = (c_void_p, POINTER(c_float), c_int, )

    dll.lf2_get_points_center_column.restype = c_int
    dll.lf2_get_points_center_column.argtypes = (c_void_p, POINTER(c_float), c_int, )


def _depth_at_xy(d, x, y):
    # if x < 0 || x >= _DEPTH_WIDTH ||
    #    y < 0 || y >= _DEPTH_HEIGHT:
    #    return None:
    return d[_DEPTH_WIDTH * y + x]

def filter_kernel(depths, d, i, j):
    thresh = 30
    num_failed = 0

    # if (abs(_depth_at_xy(depths, i-1, j-1) - d) > thresh and
    #     abs(_depth_at_xy(depths, i,   j-1) - d) > thresh and
    #     abs(_depth_at_xy(depths, i+1, j-1) - d) > thresh and
    #
    #     abs(_depth_at_xy(depths, i-1, j) - d) > thresh and
    #     abs(_depth_at_xy(depths, i+1, j) - d) > thresh and
    #
    #     abs(_depth_at_xy(depths, i-1, j+1) - d) > thresh and
    #     abs(_depth_at_xy(depths, i,   j+1) - d) > thresh and
    #     abs(_depth_at_xy(depths, i+1, j+1) - d) > thresh):
    #     return True

    if abs(_depth_at_xy(depths, i-1, j-1) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i,   j-1) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i+1, j-1) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i-1, j) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i+1, j) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i-1, j+1) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i,   j+1) - d) > thresh:
        num_failed += 1
    if abs(_depth_at_xy(depths, i+1, j+1) - d) > thresh:
        num_failed += 1

    return num_failed > 7

def get_xyz_from_depth_frame(depths, only_center):
    depthWidth = _DEPTH_WIDTH
    depthHeight = _DEPTH_HEIGHT
    depthWidthHalf = depthWidth / 2.0
    depthHeightHalf = depthHeight / 2.0
    # depthHFOV = 57.0 # Kinect1
    # depthVFOV = 43.0 # Kinect1
    depthHFOV = 70.0
    depthVFOV = 60.0
    depthH = math.tan ( (depthHFOV / 2.0) * ( math.pi / 180.0 ) );
    depthV = math.tan ( (depthVFOV / 2.0) * ( math.pi / 180.0 ) );

    points = []

    w = _DEPTH_WIDTH
    h = _DEPTH_HEIGHT


    for j in xrange(0, h):
        for i in xrange(0, w):
            depth = depths[j * w + i]

            # if i < 211 or i > 212:
            if only_center is not None and i != 212:
                continue

            if (i > 0 and i < _DEPTH_WIDTH  - 1 and
                j > 0 and j < _DEPTH_HEIGHT - 1 and
                filter_kernel(depths, depth, i, j)):
                continue

            if depth > _MAX_VALID_DEPTH:
                continue

            depth /= 1000.0
            x = depth * depthH * ((h/2 - j) / depthWidthHalf);
            y = depth * depthV * ((w/2 - i) / depthHeightHalf);
            z = depth;

            points.append((x,y,z))

    return points
