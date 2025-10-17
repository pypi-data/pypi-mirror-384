#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "eiquadprog::eiquadprog" for configuration "Release"
set_property(TARGET eiquadprog::eiquadprog APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(eiquadprog::eiquadprog PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libeiquadprog.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libeiquadprog.dylib"
  )

list(APPEND _cmake_import_check_targets eiquadprog::eiquadprog )
list(APPEND _cmake_import_check_files_for_eiquadprog::eiquadprog "${_IMPORT_PREFIX}/lib/libeiquadprog.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
