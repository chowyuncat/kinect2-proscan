#ifdef _WIN32
#	ifdef BUILDING_LF2SDK
#		define LF2SDK_EXPORT __declspec(dllexport)
#	else
#		define LF2SDK_EXPORT __declspec(dllimport)
#	endif
#	if !defined(LF2SDK_NO_DEPRECATE) && _MSC_VER >= 1310
#		define LF2SDK_EXPORT_OBSOLETE LF2SDK_EXPORT __declspec(deprecated("This will be removed in a future version of the API"))
#	else
#		define LF2SDK_EXPORT_OBSOLETE LF2SDK_EXPORT
#	endif
#else
#	if __GNUC__ >= 4
#		define LF2SDK_EXPORT __attribute__ ((visibility ("default")))
#	else
#		define LF2SDK_EXPORT
#	endif
#	if !defined(LF2SDK_NO_DEPRECATE) && ((__GNUC__ > 3 || (__GNUC__ == 3 && __GNUC_MINOR__ >= 1)))
#		define LF2SDK_EXPORT_OBSOLETE LF2_EXPORT __attribute__((__deprecated__("This will be removed in a future version of the API")))
#	else
#		define LF2SDK_EXPORT_OBSOLETE LF2SDK_EXPORT
#	endif
#endif

#ifdef BUILDING_LF2SDK
typedef struct lf2_opaque_device lf2_device;
#else
typedef struct lf2_opaque_really_device lf2_device;
#endif


#ifdef __cplusplus
extern "C" {
#endif

LF2SDK_EXPORT int lf2_open(lf2_device **sdkDevice);
LF2SDK_EXPORT int lf2_close(lf2_device *sdkDevice);
LF2SDK_EXPORT int lf2_start_streaming(lf2_device *sdkDevice);
LF2SDK_EXPORT int lf2_stop_streaming(lf2_device *sdkDevice);
LF2SDK_EXPORT int lf2_get_depth_frame(lf2_device *sdkDevice, float *dst, size_t dst_count);
LF2SDK_EXPORT int lf2_get_points(lf2_device *sdkDevice, float *dst, size_t dst_count);
LF2SDK_EXPORT int lf2_get_points_center_column(lf2_device *sdkDevice, float *dst, size_t dst_count);
LF2SDK_EXPORT int lf2_get_time_smoothed_points(lf2_device *sdkDevice, float *dst, size_t dst_count);

#ifdef __cplusplus
}
#endif