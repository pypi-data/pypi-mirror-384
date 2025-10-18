#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "deb::deb" for configuration "Release"
set_property(TARGET deb::deb APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(deb::deb PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libdeb.a"
  )

list(APPEND _cmake_import_check_targets deb::deb )
list(APPEND _cmake_import_check_files_for_deb::deb "${_IMPORT_PREFIX}/lib/libdeb.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
