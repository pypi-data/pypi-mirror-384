#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "zindex" for configuration "Release"
set_property(TARGET zindex APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/bin/zindex"
  )

list(APPEND _cmake_import_check_targets zindex )
list(APPEND _cmake_import_check_files_for_zindex "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/bin/zindex" )

# Import target "zindex_core" for configuration "Release"
set_property(TARGET zindex_core APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex_core PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/lib/libzindex_core.so"
  IMPORTED_SONAME_RELEASE "libzindex_core.so"
  )

list(APPEND _cmake_import_check_targets zindex_core )
list(APPEND _cmake_import_check_files_for_zindex_core "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/lib/libzindex_core.so" )

# Import target "zindex_py" for configuration "Release"
set_property(TARGET zindex_py APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(zindex_py PROPERTIES
  IMPORTED_COMMON_LANGUAGE_RUNTIME_RELEASE ""
  IMPORTED_LOCATION_RELEASE "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/lib/zindex_py.cpython-310-x86_64-linux-gnu.so"
  IMPORTED_NO_SONAME_RELEASE "TRUE"
  )

list(APPEND _cmake_import_check_targets zindex_py )
list(APPEND _cmake_import_check_files_for_zindex_py "/home/runner/work/zindex/zindex/build/lib.linux-x86_64-cpython-310/zindex_py/lib/zindex_py.cpython-310-x86_64-linux-gnu.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
