#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "hem::hem_client" for configuration "Release"
set_property(TARGET hem::hem_client APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hem::hem_client PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhem_client.a"
  )

list(APPEND _cmake_import_check_targets hem::hem_client )
list(APPEND _cmake_import_check_files_for_hem::hem_client "${_IMPORT_PREFIX}/lib/libhem_client.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
