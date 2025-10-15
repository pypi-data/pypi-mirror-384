#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "zindex" for configuration "Release"
set_property(TARGET zindex APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex PROPERTIES
  IMPORTED_LOCATION_RELEASE "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/bin/zindex"
  )

list(APPEND _IMPORT_CHECK_TARGETS zindex )
list(APPEND _IMPORT_CHECK_FILES_FOR_zindex "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/bin/zindex" )

# Import target "zindex_core" for configuration "Release"
set_property(TARGET zindex_core APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex_core PROPERTIES
  IMPORTED_LOCATION_RELEASE "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/lib/libzindex_core.so"
  IMPORTED_SONAME_RELEASE "libzindex_core.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS zindex_core )
list(APPEND _IMPORT_CHECK_FILES_FOR_zindex_core "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/lib/libzindex_core.so" )

# Import target "zindex_py" for configuration "Release"
set_property(TARGET zindex_py APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex_py PROPERTIES
  IMPORTED_COMMON_LANGUAGE_RUNTIME_RELEASE ""
  IMPORTED_LOCATION_RELEASE "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/lib/zindex_py.cpython-39-x86_64-linux-gnu.so"
  IMPORTED_NO_SONAME_RELEASE "TRUE"
  )

list(APPEND _IMPORT_CHECK_TARGETS zindex_py )
list(APPEND _IMPORT_CHECK_FILES_FOR_zindex_py "/usr/WS2/haridev/zindex/build/lib.linux-x86_64-cpython-39/zindex_py/lib/zindex_py.cpython-39-x86_64-linux-gnu.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
