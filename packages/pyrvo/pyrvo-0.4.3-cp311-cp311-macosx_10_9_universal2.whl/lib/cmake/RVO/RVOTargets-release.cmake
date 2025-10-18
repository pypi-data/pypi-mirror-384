#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "RVO::RVO" for configuration "Release"
set_property(TARGET RVO::RVO APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(RVO::RVO PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libRVO.2.0.3.dylib"
  IMPORTED_SONAME_RELEASE "@loader_path/.dylibs/libRVO.0.dylib"
  )

list(APPEND _cmake_import_check_targets RVO::RVO )
list(APPEND _cmake_import_check_files_for_RVO::RVO "${_IMPORT_PREFIX}/lib/libRVO.2.0.3.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
