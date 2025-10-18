#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "HEaaN::HEaaN" for configuration "Release"
set_property(TARGET HEaaN::HEaaN APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(HEaaN::HEaaN PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libHEaaN.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libHEaaN.dylib"
  )

list(APPEND _cmake_import_check_targets HEaaN::HEaaN )
list(APPEND _cmake_import_check_files_for_HEaaN::HEaaN "${_IMPORT_PREFIX}/lib/libHEaaN.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
