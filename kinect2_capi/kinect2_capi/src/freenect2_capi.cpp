#include <iostream>
#include <signal.h>

#include <libfreenect2/opengl.h>

#include <opencv2/opencv.hpp>

#include <libfreenect2/libfreenect2.hpp>
#include <libfreenect2/frame_listener_impl.h>
#include <libfreenect2/threading.h>

#ifndef _WIN32
#include <errno.h>
#endif

#define BUILDING_LF2SDK 1

#include "freenect2_capi.h"

struct lf2_opaque_device
{
  libfreenect2::Freenect2 *_global_libptr;
  libfreenect2::Freenect2Device *_dev;
  libfreenect2::SyncMultiFrameListener _listener;
  pthread_t _waiting_thread;
  pthread_mutex_t _frame_mutex;

  lf2_opaque_device() :
    _listener(libfreenect2::Frame::Depth)
  {
  }
};

static libfreenect2::Freenect2Device * safe_cast(lf2_device *sdkDevice)
{
  if (sdkDevice == NULL)
  {
    fprintf(stderr, "error: attempted to cast a NULL lf2_defvice\n");
    return NULL;
  }
  return sdkDevice->_dev;
  // return reinterpret_cast< libfreenect2::Freenect2Device * >(sdkDevice);
}

// #define ENTER_FUNC fprintf(stdout, "Entering function %s\n", __FUNCTION__)
#define ENTER_FUNC

int lf2_open(lf2_device **pSdkDevice)
{
  ENTER_FUNC;
  // glfwInit(); // NB: This causes subsequent permissions or an errno problem when called with python

  libfreenect2::Freenect2 *freenect2 = new libfreenect2::Freenect2();
  libfreenect2::Freenect2Device *dev = freenect2->openDefaultDevice();

  if (dev == NULL)
  {
    std::cout << "no device connected or failure opening the default one!" << std::endl;
    *pSdkDevice = NULL;
    return -1;
  }

  std::cout << "device serial: " << dev->getSerialNumber() << std::endl;
  std::cout << "device firmware: " << dev->getFirmwareVersion() << std::endl;

  lf2_opaque_device *sdkDevice = new lf2_opaque_device();
  sdkDevice->_global_libptr = freenect2;
  sdkDevice->_dev = dev;

  *pSdkDevice = sdkDevice;
  printf("Returning a device\n");

#ifndef _WIN32
  errno = 0; // HACK: Something is setting errno
#endif

  return 0;
}

int lf2_close(lf2_device *sdkDevice)
{
  ENTER_FUNC;
  libfreenect2::Freenect2Device *dev = safe_cast(sdkDevice);
  if (dev != NULL)
  {
    dev->close();
    delete dev;
  }

  return 0;
}

#if 0
static void * waiting_thread_func(void *thread_params)
{
  lf2_opaque_device * sdkDevice = reinterpret_cast<lf2_opaque_device *>(thread_params);

  libfreenect2::Freenect2Device *dev = safe_cast(sdkDevice);
  libfreenect2::SyncMultiFrameListener *listener = &sdkDevice->_listener;

  libfreenect2::FrameMap frames;
  libfreenect2::FrameMap *frames_prev;

  while (true)
  {
    listener->waitForNewFrame(frames);

    pthread_mutex_lock(&sdkDevice->_frame_mutex);
    sdkDevice->_frames = frames;
    pthread_mutex_unlock(&sdkDevice->_frame_mutex);

    listener->release(*frames_prev);
  }
}
#endif

int lf2_start_streaming(lf2_device *sdkDevice)
{
  ENTER_FUNC;
  libfreenect2::Freenect2Device *dev = safe_cast(sdkDevice);

  dev->setColorFrameListener(&sdkDevice->_listener);
  dev->setIrAndDepthFrameListener(&sdkDevice->_listener);
  dev->start();

//  pthread_create(&sdkDevice->_waiting_thread, waiting_thread_func);
//  pthread_mutex_init(&sdkDevice->_frame_mutex, NULL);

  return 0;
}

int lf2_stop_streaming(lf2_device *sdkDevice)
{
  ENTER_FUNC;
  libfreenect2::Freenect2Device *dev = safe_cast(sdkDevice);

  // TODO: restarting ir stream doesn't work!
  // TODO: bad things will happen, if frame listeners are freed before dev->stop() :(
  dev->stop();
  return 0;
}

//
// TODO: This can be a buffer of shorts instead of floats!
//
int lf2_get_depth_frame(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
  ENTER_FUNC;
  libfreenect2::Freenect2Device *dev = safe_cast(sdkDevice);
  libfreenect2::SyncMultiFrameListener *listener = &sdkDevice->_listener;

  libfreenect2::FrameMap frames;
  listener->waitForNewFrame(frames);
  libfreenect2::Frame *depth = frames[libfreenect2::Frame::Depth];
  const size_t src_float_count = depth->height * depth->width;
  const bool dst_buffer_is_valid = dst_count >= src_float_count;
  if (dst_buffer_is_valid)
  {
    const size_t src_byte_count = src_float_count * sizeof(float);
    memcpy(dst, depth->data, src_byte_count);
  }
  listener->release(frames);
  return dst_buffer_is_valid ? 0 : 1;
}


