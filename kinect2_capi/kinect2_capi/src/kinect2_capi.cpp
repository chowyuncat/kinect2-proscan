#define _WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <comdef.h>
#include <kinect.h>

#include <iostream>

#define BUILDING_LF2SDK 1
#include "freenect2_capi.h"

#ifdef SUCCEEDED
#undef SUCCEEDED
#define SUCCEEDED(hr) (((HRESULT)(hr)) >= 0)
#endif

// #define ENTER_FUNC fprintf(stdout, "Entering function %s\n", __FUNCTION__)
#define ENTER_FUNC
#define EXIT_FUNC


// Safe release for interfaces
template<class Interface>
inline void SafeRelease(Interface *& pInterfaceToRelease)
{
    if (pInterfaceToRelease != NULL)
    {
        pInterfaceToRelease->Release();
        pInterfaceToRelease = NULL;
    }
}

struct lf2_opaque_device
{
    IKinectSensor*     _KinectSensor;
    IDepthFrameReader* _DepthFrameReader;
    IColorFrameReader* _ColorFrameReader;
    IInfraredFrameReader *_InfraredFrameReader;
    ICoordinateMapper* _CoordinateMapper;

    RGBQUAD *_ColorBuffer;
};

static IKinectSensor * safe_cast(lf2_opaque_device *sdkDevice)
{
    if (sdkDevice == NULL)
    {
        fprintf(stderr, "error: attempted to cast a NULL lf2_defvice\n");
        return NULL;
    }
    return sdkDevice->_KinectSensor;
}
 
#define API_FUNC(name) lf2_##name

int API_FUNC(open)(lf2_device **pSdkDevice)
{
    ENTER_FUNC;

    printf("LF2_CAPI compiled at "__TIMESTAMP__"\n");

    *pSdkDevice = NULL;

    HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
    if (hr != S_OK) // S_FALSE also okay??
    {
        std::cout << "Failed to initialize COM!" << std::endl;
        return hr;
    }

    IKinectSensor * kinect = NULL;
    hr = GetDefaultKinectSensor(&kinect);
    if (FAILED(hr))
    {
        std::cout << "no device connected or failure opening the default one!" << std::endl;
        return hr;
    }

    IDepthFrameSource* pDepthFrameSource = NULL;
    hr = kinect->Open();
    if (SUCCEEDED(hr))
    {
        hr = kinect->get_DepthFrameSource(&pDepthFrameSource);
    }
    IDepthFrameReader *depthFrameReader = NULL;
    if (SUCCEEDED(hr))
    {
        hr = pDepthFrameSource->OpenReader(&depthFrameReader);
    }
    else
    {
        std::cout << "Could not open depth frame reader!" << std::endl;
    }
    SafeRelease(pDepthFrameSource);

    IColorFrameSource* pColorFrameSource = NULL;
    if (SUCCEEDED(hr))
    {
        hr = kinect->get_ColorFrameSource(&pColorFrameSource);
    }
    IColorFrameReader *colorFrameReader = NULL;
    if (SUCCEEDED(hr))
    {
        hr = pColorFrameSource->OpenReader(&colorFrameReader);
    }
    else
    {
        std::cout << "Could not open depth frame reader!" << std::endl;
    }
    SafeRelease(pColorFrameSource);

    IInfraredFrameSource *pInfraredFrameSource = NULL;
    if (SUCCEEDED(hr))
    {
        hr = kinect->get_InfraredFrameSource(&pInfraredFrameSource);
    }
    IInfraredFrameReader *infraredFrameReader = NULL;
    if (SUCCEEDED(hr))
    {
        hr = pInfraredFrameSource->OpenReader(&infraredFrameReader);
    }
    else
    {
        std::cout << "Could not open infrared frame reader!" << std::endl;
    }
    SafeRelease(pInfraredFrameSource);

    ICoordinateMapper* coordinateMapper = NULL;
    hr = kinect->get_CoordinateMapper(&coordinateMapper);
    if (SUCCEEDED(hr)){

    }

    lf2_opaque_device * sdkDevice = new lf2_opaque_device();
    sdkDevice->_KinectSensor = kinect;
    sdkDevice->_DepthFrameReader = depthFrameReader;
    sdkDevice->_ColorFrameReader = colorFrameReader;
    sdkDevice->_InfraredFrameReader = infraredFrameReader;
    sdkDevice->_CoordinateMapper = coordinateMapper;
    sdkDevice->_ColorBuffer = NULL;

    std::cout << "Found a Kinect Sensor" << std::endl;

    *pSdkDevice = sdkDevice;
    return 0;
}

int API_FUNC(close)(lf2_device *sdkDevice)
{
    ENTER_FUNC;
    IKinectSensor *sensor = safe_cast(sdkDevice);
    if (sensor != NULL)
    {
        std::cout << "Closing Kinect sensor!" << std::endl;
        sensor->Close();
        SafeRelease(sdkDevice->_CoordinateMapper);
        SafeRelease(sdkDevice->_ColorFrameReader);
        SafeRelease(sdkDevice->_DepthFrameReader);
        SafeRelease(sensor);
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

int API_FUNC(start_streaming)(lf2_device *sdkDevice)
{
    ENTER_FUNC;
    IKinectSensor *dev = safe_cast(sdkDevice);

    //  pthread_create(&sdkDevice->_waiting_thread, waiting_thread_func);
    //  pthread_mutex_init(&sdkDevice->_frame_mutex, NULL);

    return 0;
}

int API_FUNC(stop_streaming)(lf2_device *sdkDevice)
{
    ENTER_FUNC;
    IKinectSensor *dev = safe_cast(sdkDevice);

    return 0;
}

static HRESULT GetDepthFrame(IDepthFrameReader *depthFrameReader, float *float_buffer)
{
    IDepthFrame* pDepthFrame = NULL;

    HRESULT hr = depthFrameReader->AcquireLatestFrame(&pDepthFrame);

    if (SUCCEEDED(hr))
    {
        INT64 nTime = 0;
        IFrameDescription* pFrameDescription = NULL;
        int nWidth = 0;
        int nHeight = 0;
        USHORT nDepthMinReliableDistance = 0;
        USHORT nDepthMaxReliableDistance = 0;
        UINT nBufferSize = 0;
        UINT16 *pBuffer = NULL;

        hr = pDepthFrame->get_RelativeTime(&nTime);

        if (SUCCEEDED(hr))
        {
            hr = pDepthFrame->get_FrameDescription(&pFrameDescription);
        }
        else
        {
            std::cout << "Could not get frame description!" << std::endl;
        }

        if (SUCCEEDED(hr))
        {
            hr = pFrameDescription->get_Width(&nWidth);
        }

        if (SUCCEEDED(hr))
        {
            hr = pFrameDescription->get_Height(&nHeight);
        }

        if (SUCCEEDED(hr))
        {
            hr = pDepthFrame->get_DepthMinReliableDistance(&nDepthMinReliableDistance);
        }

        if (SUCCEEDED(hr))
        {
            hr = pDepthFrame->get_DepthMaxReliableDistance(&nDepthMaxReliableDistance);
        }

        if (SUCCEEDED(hr))
        {
            hr = pDepthFrame->AccessUnderlyingBuffer(&nBufferSize, &pBuffer);
        }
        else
        {
            std::cout << "Could not access underlying buffer!" << std::endl;
        }

        if (SUCCEEDED(hr))
        {
            const int numSourceElements = nWidth * nHeight;
            // ProcessDepth(nTime, pBuffer, nWidth, nHeight, nDepthMinReliableDistance, nDepthMaxReliableDistance);
            for (int i = 0; i < numSourceElements; ++i)
            {
                float_buffer[i] = pBuffer[i];
            }
        }

        SafeRelease(pFrameDescription);
    }

    SafeRelease(pDepthFrame);

    return hr;
}

//
// TODO: This can be a buffer of shorts instead of floats!
//
int API_FUNC(get_depth_frame)(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    ENTER_FUNC;

    IKinectSensor *sensor = safe_cast(sdkDevice);

    BOOLEAN isOpen = 0;
    sensor->get_IsOpen(&isOpen);
    if (!isOpen)
    {
        std::cout << "Kinect not open when calling get depth frame!" << std::endl;
        return -1;
    }



    if (sensor == NULL)
    {
        return -1;
    }


#if 0
    const size_t src_float_count = depth->height * depth->width;
    const bool dst_buffer_is_valid = dst_count >= src_float_count;
    if (dst_buffer_is_valid)
    {
        const size_t src_byte_count = src_float_count * sizeof(float);
        memcpy(dst, depth->data, src_byte_count);
    }
    return dst_buffer_is_valid ? 0 : 1;
#endif
    IDepthFrameReader *reader = sdkDevice->_DepthFrameReader;
    // HRESULT hr = GetDepthFrame(sdkDevice->_DepthFrameReader, dst);
    int tries = 0;
    HRESULT hr;
    while ((hr = GetDepthFrame(reader, dst)) != S_OK)
    {
        if ((tries++ % 10000000) == 0)
        {
            std::cout << "Could not acquire latest frame after " << tries << " tries" << std::endl;
            const _com_error err(hr);
            std::wcout << hr << ": " << err.ErrorMessage() << std::endl;
            // printf("%d: %ls\n", hr, err.ErrorMessage());
        }

    }
    if (tries > 0)
        std::cout << "Frame acquisition took " << tries << " tries " << std::endl;
    /*if (SUCCEEDED(hr))
    {
    */
    return 0;
    //  }
    // return hr;
}

static inline UINT16 compute_average_depth(int dx, int dy, int depthWidth, double *accum_buffer, int *pass_count_buffer)
{
    const double accum_depth = accum_buffer[dy * depthWidth + dx];
    const int pass_count_for_pixel = pass_count_buffer[dy * depthWidth + dx];

    const UINT16 depth = pass_count_for_pixel > 0 ?
        static_cast<UINT16>(accum_depth / pass_count_for_pixel) :
        0;

    return depth;
}

static inline UINT16 compute_average_depth(int dx, int dy, int depthWidth, size_t pass_count, UINT16 **depth_buffer_slices)
{
    const size_t index = dy * depthWidth + dx;
    double accum_depth = 0;
    int pass_count_for_pixel = 0;
    UINT16 min_depth = UINT16_MAX;
    UINT16 max_depth = 1;
    for (size_t slice = 0; slice < pass_count; ++slice)
    {
        const UINT16 d = depth_buffer_slices[slice][index];
        if (d > 0)
            ++pass_count_for_pixel;
        if (d < min_depth)
            min_depth = d;
        if (d > max_depth)
            max_depth = d;
        accum_depth += d;
    }
    
    if (max_depth - min_depth > 100)
    {
        return 0;
    }

    const UINT16 depth = pass_count_for_pixel > 0 ?
        static_cast<UINT16>(accum_depth / pass_count_for_pixel) :
        0;

    return depth;
}

static int _get_time_smoothed_points(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    if (sdkDevice == NULL)
        return 1;
    if (dst == NULL)
        return 1;
    if (dst_count < 1)
        return 1;

    IKinectSensor *sensor = safe_cast(sdkDevice);
    IDepthFrameReader *depthFrameReader = sdkDevice->_DepthFrameReader;
    IDepthFrame* pDepthFrame = NULL;
    HRESULT hr;
    do {
        hr = depthFrameReader->AcquireLatestFrame(&pDepthFrame);
    } while (!SUCCEEDED(hr));
    std::cout << "Acquired depth" << std::endl;

    IFrameDescription* pFrameDescription = NULL;
    hr = pDepthFrame->get_FrameDescription(&pFrameDescription);
    int depthWidth = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Width(&depthWidth);
    }
    int depthHeight = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Height(&depthHeight);
    }
    SafeRelease(pFrameDescription);

    USHORT depthMinReliable = 0;
    pDepthFrame->get_DepthMinReliableDistance(&depthMinReliable);
    USHORT depthMaxReliable = 0;
    pDepthFrame->get_DepthMaxReliableDistance(&depthMaxReliable);

    if (dst_count != depthWidth * depthHeight * 6)
    {
        std::cerr << "client allocated buffer not the right size" << std::endl;
        return -1;
    }

    const size_t accum_buffer_count = depthWidth * depthHeight;

    //// TODO: delete me
    //double *const accum_buffer = new double[accum_buffer_count];
    //std::fill(accum_buffer, accum_buffer + accum_buffer_count, 0.0);

    //// TODO: delete me
    //int *const pass_count_buffer = new int[accum_buffer_count];
    //std::fill(pass_count_buffer, pass_count_buffer + accum_buffer_count, 0);

    const size_t num_passes = 100;
    UINT16 **depth_buffer_slices = new UINT16*[num_passes];
    for (size_t pass = 0; pass < num_passes; ++pass)
    {
        UINT16 *const this_depth_buffer = new UINT16[accum_buffer_count];
        std::fill(this_depth_buffer, this_depth_buffer + accum_buffer_count, 0);

        uint16_t *depthBuffer = NULL;
        size_t depthBufferSize = 0;
        hr = pDepthFrame->AccessUnderlyingBuffer(&depthBufferSize, &depthBuffer);
        for (size_t i = 0; i < depthBufferSize; ++i)
        {
            const UINT16 d = depthBuffer[i];
            // if (d > depthMinReliable && d < depthMaxReliable)
            {
                // accum_buffer[i] += d;
                // ++pass_count_buffer[i];
                this_depth_buffer[i] = d;
            }
        }
        depth_buffer_slices[pass] = this_depth_buffer;

        if (pass + 1 < num_passes)
        {
            SafeRelease(pDepthFrame);
            HRESULT hr;
            do {
                hr = depthFrameReader->AcquireLatestFrame(&pDepthFrame);
            } while (!SUCCEEDED(hr));
            std::cout << "Acquired depth for pass " << pass << std::endl;
        }
    }

    IColorFrameReader *colorFrameReader = sdkDevice->_ColorFrameReader;
    IColorFrame* pColorFrame = NULL;
    do {
        hr = colorFrameReader->AcquireLatestFrame(&pColorFrame);
    } while (!SUCCEEDED(hr));
    std::cout << "Acquired color" << std::endl;

    pFrameDescription = NULL;
    hr = pColorFrame->get_FrameDescription(&pFrameDescription);
    int colorWidth = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Width(&colorWidth);
    }
    int colorHeight = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Height(&colorHeight);
    }
    SafeRelease(pFrameDescription);
    size_t colorBufferSize = colorWidth *colorHeight;

    pFrameDescription = NULL;
    // hr = pIRFrame->get_FrameDescription(&pFrameDescription);
    int infraWidth = 0;
    if (SUCCEEDED(hr))
    {
        //    hr = pFrameDescription->get_Width(&infraWidth);
    }
    else
    {
        std::cerr << "Failed to get InfraredFrame Description" << std::endl;
    }
    int infraHeight = 0;
    if (SUCCEEDED(hr))
    {
        //    hr = pFrameDescription->get_Height(&infraHeight);
    }
    SafeRelease(pFrameDescription);


    if (sdkDevice->_ColorBuffer == NULL)
    {
        printf("Frame Allocation:\n");
        printf(" IR   : %4d x %4d\n", infraWidth, infraHeight);
        printf(" Depth: %4d x %4d\n", depthWidth, depthHeight);
        printf(" Color: %4d x %4d\n", colorWidth, colorHeight);
        sdkDevice->_ColorBuffer = new RGBQUAD[colorWidth * colorHeight];
    }
    RGBQUAD *colorBuffer = sdkDevice->_ColorBuffer;
    hr = pColorFrame->CopyConvertedFrameDataToArray(colorBufferSize * sizeof(RGBQUAD), reinterpret_cast<BYTE*>(&colorBuffer[0]), ColorImageFormat::ColorImageFormat_Bgra);
    SafeRelease(pColorFrame);

    ICoordinateMapper *coordinateMapper = sdkDevice->_CoordinateMapper;
    size_t dst_i = 0;
    for (int dy = 0; dy < depthHeight; ++dy)
    {
        for (int dx = 0; dx < depthWidth; ++dx)
        {
            float x, y, z;
            float r, g, b;
            x = 0;
            y = 0;
            z = 0;
            r = g = b = 0;

            const DepthSpacePoint depthSpacePoint = { static_cast<float>(dx), static_cast<float>(dy) };

            // const UINT16 depth = compute_average_depth(dx, dy, depthWidth, accum_buffer, pass_count_buffer);
            const UINT16 depth = compute_average_depth(dx, dy, depthWidth, num_passes, depth_buffer_slices);

            // Coordinate Mapping Depth to Color Space, and Setting PointCloud RGB
            ColorSpacePoint colorSpacePoint = { 0.0f, 0.0f };
            coordinateMapper->MapDepthPointToColorSpace(depthSpacePoint, depth, &colorSpacePoint);
            int colorX = static_cast<int>(std::floor(colorSpacePoint.X + 0.5f));
            int colorY = static_cast<int>(std::floor(colorSpacePoint.Y + 0.5f));
            if ((0 <= colorX) && (colorX < colorWidth) && (0 <= colorY) && (colorY < colorHeight)){
                RGBQUAD color = colorBuffer[colorY * colorWidth + colorX];
                b = color.rgbBlue; // / 255.0f;
                g = color.rgbGreen; // / 255.0f;
                r = color.rgbRed; // / 255.0f;
            }

            // Coordinate Mapping Depth to Camera Space, and Setting PointCloud XYZ
            CameraSpacePoint cameraSpacePoint = { 0.0f, 0.0f, 0.0f };
            coordinateMapper->MapDepthPointToCameraSpace(depthSpacePoint, depth, &cameraSpacePoint);
            if ((0 <= colorX) && (colorX < colorWidth) && (0 <= colorY) && (colorY < colorHeight))
            {
                x = cameraSpacePoint.X;
                y = cameraSpacePoint.Y;
                z = cameraSpacePoint.Z;
            }

            dst[dst_i + 0] = x;
            dst[dst_i + 1] = y;
            dst[dst_i + 2] = z;

            dst[dst_i + 3] = r;
            dst[dst_i + 4] = g;
            dst[dst_i + 5] = b;
            dst_i += 6;
        }
    }

    for (size_t i = 0; i < num_passes; ++i)
    {
        delete [] (depth_buffer_slices[i]);
    }
    delete [] depth_buffer_slices;

    SafeRelease(pDepthFrame);

    return 0;
}

static int _get_points(bool center_only, lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    if (sdkDevice == NULL)
        return 1;
    if (dst == NULL)
        return 1;
    if (dst_count < 1)
        return 1;

    IKinectSensor *sensor = safe_cast(sdkDevice);
    IDepthFrameReader *depthFrameReader = sdkDevice->_DepthFrameReader;
    IDepthFrame* pDepthFrame = NULL;
    HRESULT hr;
    do {
        hr = depthFrameReader->AcquireLatestFrame(&pDepthFrame);
    } while (!SUCCEEDED(hr));
    std::cout << "Acquired depth" << std::endl;

    IColorFrameReader *colorFrameReader = sdkDevice->_ColorFrameReader;
    IColorFrame* pColorFrame = NULL;
    do {
        hr = colorFrameReader->AcquireLatestFrame(&pColorFrame);
    } while (!SUCCEEDED(hr));
    std::cout << "Acquired color" << std::endl;

    IFrameDescription* pFrameDescription = NULL;
    hr = pDepthFrame->get_FrameDescription(&pFrameDescription);
    int depthWidth = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Width(&depthWidth);
    }
    int depthHeight = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Height(&depthHeight);
    }
    SafeRelease(pFrameDescription);

    if (dst_count != depthWidth * depthHeight * 6)
    {
        std::cerr << "client allocated buffer not the right size" << std::endl;
        return -1;
    }

    pFrameDescription = NULL;
    hr = pColorFrame->get_FrameDescription(&pFrameDescription);
    int colorWidth = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Width(&colorWidth);
    }
    int colorHeight = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Height(&colorHeight);
    }
    SafeRelease(pFrameDescription);
    size_t colorBufferSize = colorWidth *colorHeight;

    pFrameDescription = NULL;
    IInfraredFrameReader *infraredFrameReader = sdkDevice->_InfraredFrameReader;
    IInfraredFrame *pIRFrame = NULL;
    do {
        hr = infraredFrameReader->AcquireLatestFrame(&pIRFrame);
    } while (!SUCCEEDED(hr));
    std::cout << "Acquired color" << std::endl;
    hr = pIRFrame->get_FrameDescription(&pFrameDescription);
    int infraWidth = 0;
    if (SUCCEEDED(hr))
    {
       hr = pFrameDescription->get_Width(&infraWidth);
    }
    else
    {
        std::cerr << "Failed to get InfraredFrame Description" << std::endl;
    }
    int infraHeight = 0;
    if (SUCCEEDED(hr))
    {
        hr = pFrameDescription->get_Height(&infraHeight);
    }
    SafeRelease(pFrameDescription);


    uint16_t *depthBuffer = NULL;
    size_t depthBufferSize = 0;
    hr = pDepthFrame->AccessUnderlyingBuffer(&depthBufferSize, &depthBuffer);

    if (sdkDevice->_ColorBuffer == NULL)
    {
        printf("Frame Allocation:\n");
        printf(" IR   : %4d x %4d\n", infraWidth, infraHeight);
        printf(" Depth: %4d x %4d\n", depthWidth, depthHeight);
        printf(" Color: %4d x %4d\n", colorWidth, colorHeight);
        sdkDevice->_ColorBuffer = new RGBQUAD[colorWidth * colorHeight];
    }
    RGBQUAD *colorBuffer = sdkDevice->_ColorBuffer;
    hr = pColorFrame->CopyConvertedFrameDataToArray(colorBufferSize * sizeof(RGBQUAD), reinterpret_cast<BYTE*>(&colorBuffer[0]), ColorImageFormat::ColorImageFormat_Bgra);
    SafeRelease(pColorFrame);

    UINT16 *irBuffer = NULL;
    size_t irBufferSize = 0;
    pIRFrame->AccessUnderlyingBuffer(&irBufferSize, &irBuffer);

    ICoordinateMapper *coordinateMapper = sdkDevice->_CoordinateMapper;
    size_t dst_i = 0;
    for (int dy = 0; dy < depthHeight; ++dy)
    {
        for (int dx = 0; dx < depthWidth; ++dx)
        {
            float x, y, z;
            float r, g, b;
            x = 0;
            y = 0;
            z = 0;
            r = g = b = 0;
            if (!center_only || (dx >= 212 && dx <= 212))
            {
                DepthSpacePoint depthSpacePoint = { static_cast<float>(dx), static_cast<float>(dy) };
                UINT16 depth = depthBuffer[dy * depthWidth + dx];

                // Coordinate Mapping Depth to Color Space, and Setting PointCloud RGB
                
                ColorSpacePoint colorSpacePoint = { 0.0f, 0.0f };
                coordinateMapper->MapDepthPointToColorSpace(depthSpacePoint, depth, &colorSpacePoint);
                const int colorX = static_cast<int>(std::floor(colorSpacePoint.X + 0.5f));
                const int colorY = static_cast<int>(std::floor(colorSpacePoint.Y + 0.5f));
                const bool colorMapped = (colorX >= 0) && (colorX < colorWidth) && (colorY >= 0) && (colorY < colorHeight);
#if 0
                if (colorMapped){
                    RGBQUAD color = colorBuffer[colorY * colorWidth + colorX];
                    b = color.rgbBlue; // / 255.0f;
                    g = color.rgbGreen; // / 255.0f;
                    r = color.rgbRed; // / 255.0f;
                }
#else
                // const float heat = (irBuffer[dy * depthWidth + dx] / 4096.0f) * 255.0f;
                const float heat = powf(irBuffer[dy * depthWidth + dx] / 65535.0f, 0.32f) * 255.0f;
                r = heat;
                g = heat;
                b = heat;
#endif
                // Coordinate Mapping Depth to Camera Space, and Setting PointCloud XYZ
                CameraSpacePoint cameraSpacePoint = { 0.0f, 0.0f, 0.0f };
                coordinateMapper->MapDepthPointToCameraSpace(depthSpacePoint, depth, &cameraSpacePoint);
                if (colorMapped)
                {
                    x = cameraSpacePoint.X;
                    y = cameraSpacePoint.Y;
                    z = cameraSpacePoint.Z;
                }
                else
                {
                     // TODO: what happens if the point couldn't be mapped?
                }
            }
            dst[dst_i + 0] = x;
            dst[dst_i + 1] = y;
            dst[dst_i + 2] = z;

            dst[dst_i + 3] = r;
            dst[dst_i + 4] = g;
            dst[dst_i + 5] = b;
            dst_i += 6;
        }
    }

    SafeRelease(pDepthFrame);
    SafeRelease(pIRFrame);

    return 0;
}

int API_FUNC(get_points_center_column)(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    ENTER_FUNC;

    return _get_points(true, sdkDevice, dst, dst_count);
}

int API_FUNC(get_points)(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    ENTER_FUNC;

    return _get_points(false, sdkDevice, dst, dst_count);
}

int API_FUNC(get_time_smoothed_points)(lf2_device *sdkDevice, float *dst, size_t dst_count)
{
    ENTER_FUNC;

    return _get_time_smoothed_points(sdkDevice, dst, dst_count);
}
