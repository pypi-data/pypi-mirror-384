#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "sylvan::sylvan" for configuration "Release"
set_property(TARGET sylvan::sylvan APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sylvan::sylvan PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/storm/resources/sylvan/libsylvan.a"
  )

list(APPEND _cmake_import_check_targets sylvan::sylvan )
list(APPEND _cmake_import_check_files_for_sylvan::sylvan "${_IMPORT_PREFIX}/lib/storm/resources/sylvan/libsylvan.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
