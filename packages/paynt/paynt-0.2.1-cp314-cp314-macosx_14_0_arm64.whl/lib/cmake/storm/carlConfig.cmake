
set(carl_VERSION 14.33)


set( carl_VERSION_MAJOR 14)
set( carl_VERSION_MINOR 33)
set( carl_VERSION_PATCH )
set( carl_MINORYEARVERSION 14)
set( carl_MINORMONTHVERSION 33)
set( carl_MAINTENANCEVERSION )


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was carlConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################


get_filename_component(carl_CMAKE_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)



if(NOT TARGET CLN_SHARED)
	add_library(CLN_SHARED SHARED IMPORTED)
	set_target_properties(CLN_SHARED PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libcln.dylib")
	set_target_properties(CLN_SHARED PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
endif()

if(NOT TARGET CLN_STATIC)
	add_library(CLN_STATIC STATIC IMPORTED)
	set_target_properties(CLN_STATIC PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libcln.a")
	set_target_properties(CLN_STATIC PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
	set_target_properties(CLN_STATIC PROPERTIES IMPORTED_LINK_INTERFACE_LIBRARIES "GMP_STATIC")
	set_target_properties(CLN_STATIC PROPERTIES IMPORTED_LINK_INTERFACE_LIBRARIES "GMP_STATIC")
endif()

if(NOT TARGET GINAC_SHARED)
	add_library(GINAC_SHARED SHARED IMPORTED)
	set_target_properties(GINAC_SHARED PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libginac.dylib")
	set_target_properties(GINAC_SHARED PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
	set_target_properties(GINAC_SHARED PROPERTIES IMPORTED_LINK_INTERFACE_LIBRARIES "CLN_SHARED")
endif()

if(NOT TARGET GMP_SHARED)
	add_library(GMP_SHARED SHARED IMPORTED)
	set_target_properties(GMP_SHARED PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libgmp.dylib")
	set_target_properties(GMP_SHARED PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
endif()

if(NOT TARGET GMP_STATIC)
	add_library(GMP_STATIC STATIC IMPORTED)
	set_target_properties(GMP_STATIC PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libgmp.a")
	set_target_properties(GMP_STATIC PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
endif()

if(NOT TARGET GMPXX_SHARED)
	add_library(GMPXX_SHARED SHARED IMPORTED)
	set_target_properties(GMPXX_SHARED PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libgmpxx.dylib")
	set_target_properties(GMPXX_SHARED PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
endif()

if(NOT TARGET GMPXX_STATIC)
	add_library(GMPXX_STATIC STATIC IMPORTED)
	set_target_properties(GMPXX_STATIC PROPERTIES IMPORTED_LOCATION "/opt/homebrew/lib/libgmpxx.a")
	set_target_properties(GMPXX_STATIC PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
	set_target_properties(GMPXX_STATIC PROPERTIES IMPORTED_LINK_INTERFACE_LIBRARIES "GMP_STATIC")
endif()

if(NOT TARGET Boost::headers)
	add_library(Boost::headers INTERFACE IMPORTED)
	set_target_properties(Boost::headers PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/opt/homebrew/include")
endif()


set(CARL_STORM_USE_CLN_EA "OFF")
set(CARL_STORM_USE_CLN_RF "ON")
set(CARL_STORM_BUILD_TESTS "ON")
set(CARL_STORM_BUILD_EXECUTABLES "OFF")
set(CARL_STORM_3RDPARTY_BINARY_DIR "/Users/runner/work/synthesis/synthesis/build/cp314-cp314-macosx_14_0_arm64/_deps/storm-build/resources/3rdparty")
set(CARL_CARL_LOGGING "OFF")
set(CARL_TIMING "OFF")
set(CARL_FORCE_SHIPPED_RESOURCES "OFF")
set(CARL_FORCE_SHIPPED_GMP "OFF")
set(CARL_USE_GINAC "TRUE")
set(CARL_USE_CLN_NUMBERS "TRUE")
set(CARL_USE_COCOA "OFF")
set(CARL_USE_BLISS "OFF")
set(CARL_USE_MPFR_FLOAT "OFF")
set(CARL_PORTABLE "OFF")
set(CARL_BUILD_STATIC "OFF")
set(CARL_BUILD_DOXYGEN "OFF")
set(CARL_THREAD_SAFE "ON")
set(CARL_EXCLUDE_TESTS_FROM_ALL "ON")
set(CARL_HAVE_CLN "TRUE")
set(CARL_HAVE_GINAC "TRUE")
 
# Our library dependencies (contains definitions for IMPORTED targets)
if(NOT TARGET lib_carl)
  include("${CMAKE_CURRENT_LIST_DIR}/carlTargets.cmake")
endif()
if(NOT TARGET lib_carl)
    message(FATAL_ERROR "Including ${CMAKE_CURRENT_LIST_DIR}/carlTargets.cmake did not define target lib_carl.")
endif()

   
set(carl_INCLUDE_DIR "${CMAKE_INSTALL_DIR}//var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib/include/storm/resources")

set(carl_LIBRARIES lib_carl)
check_required_components(carl)
