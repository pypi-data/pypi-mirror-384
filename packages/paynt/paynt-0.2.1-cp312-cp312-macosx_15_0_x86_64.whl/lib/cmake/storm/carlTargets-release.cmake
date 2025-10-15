#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "lib_carl" for configuration "Release"
set_property(TARGET lib_carl APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(lib_carl PROPERTIES
  IMPORTED_LOCATION_RELEASE "/var/folders/5k/fq5ptf2906bgfn1krb78bmj00000gn/T/tmpj71pd8ad/wheel/platlib/lib/storm/resources/libcarl.14.33.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libcarl.14.33.dylib"
  )

list(APPEND _cmake_import_check_targets lib_carl )
list(APPEND _cmake_import_check_files_for_lib_carl "/var/folders/5k/fq5ptf2906bgfn1krb78bmj00000gn/T/tmpj71pd8ad/wheel/platlib/lib/storm/resources/libcarl.14.33.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
