set(ZINDEX_FOUND TRUE)

# Include directories
set(ZINDEX_INCLUDE_DIRS "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/include")
if (NOT IS_DIRECTORY "${ZINDEX_INCLUDE_DIRS}")
    set(ZINDEX_FOUND FALSE)
endif ()
#message(STATUS "ZINDEX_INCLUDE_DIRS: " ${ZINDEX_INCLUDE_DIRS})
get_filename_component(ZINDEX_ROOT_DIR ${ZINDEX_INCLUDE_DIRS}/.. ABSOLUTE)
#message(STATUS "ZINDEX_ROOT_DIR: " ${ZINDEX_ROOT_DIR})
set(ZINDEX_LIBRARY_PATH "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/lib")
link_directories(${ZINDEX_LIBRARY_PATH})
set(ZINDEX_LIBRARIES zindex)
set(ZINDEX_DEFINITIONS "")
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(zindex
            REQUIRED_VARS ZINDEX_FOUND ZINDEX_INCLUDE_DIRS ZINDEX_LIBRARIES)
