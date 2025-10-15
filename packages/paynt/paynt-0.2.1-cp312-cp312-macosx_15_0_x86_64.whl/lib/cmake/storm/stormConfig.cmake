include(CMakeFindDependencyMacro)



####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was stormConfig.cmake.install.in                            ########

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

set(STORM_USE_CLN_EA "OFF")
set(STORM_USE_CLN_RF "ON")
set(STORM_BUILD_TESTS "ON")
set(STORM_BUILD_EXECUTABLES "OFF")
set(STORM_3RDPARTY_BINARY_DIR "/Users/runner/work/synthesis/synthesis/build/cp312-cp312-macosx_15_0_x86_64/_deps/storm-build/resources/3rdparty")
set(STORM_VERSION "1.11.1")
set(STORM_VERSION_DEV "0")
set(STORM_HAVE_GMM "ON")
set(STORM_HAVE_GUROBI "OFF")
set(STORM_HAVE_SPOT "ON")
set(STORM_HAVE_SOPLEX "OFF")
set(STORM_HAVE_XERCES "ON")
set(STORM_HAVE_Z3 "ON")


# Compute the installation prefix relative to this file.
get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_FILE}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
if(_IMPORT_PREFIX STREQUAL "/")
  set(_IMPORT_PREFIX "")
endif()

set(STORM_RESOURCE_INCLUDE_INSTALL_DIR "${_IMPORT_PREFIX}/include/storm/resources")
set(STORM_RESOURCE_LIBRARY_INSTALL_DIR "${_IMPORT_PREFIX}/lib/storm/resources")

include("${CMAKE_CURRENT_LIST_DIR}/carlConfig.cmake")
if(NOT TARGET lib_carl)
    message(FATAL_ERROR "Including ${CMAKE_CURRENT_LIST_DIR}/carlConfig.cmake did not define target lib_carl.")
endif()
set(storm_carl_DIR "${CMAKE_CURRENT_LIST_DIR}")
include("${STORM_RESOURCE_LIBRARY_INSTALL_DIR}/sylvan/cmake/sylvan/sylvan-config.cmake")

set(CMAKE_MODULE_PATH_save "${CMAKE_MODULE_PATH}")
list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_LIST_DIR}/find_modules/")

find_dependency(Boost QUIET NO_MODULE)
if(ON)  # STORM_HAVE_Z3
    if(ON)
        find_dependency(Z3 4.8.7 NO_MODULE)
    else()
        find_dependency(Z3)
        add_library(z3 SHARED IMPORTED)
        set_target_properties(
                z3
                PROPERTIES
                IMPORTED_LOCATION ${Z3_LIBRARIES}
                INTERFACE_INCLUDE_DIRECTORIES ${Z3_INCLUDE_DIR}
        )
    endif()
endif()
find_dependency(Threads)
if(ON)  # STORM_HAVE_GLPK
    find_dependency(GLPK)

    add_library(glpk SHARED IMPORTED)
    set_target_properties(
            glpk
            PROPERTIES
            IMPORTED_LOCATION ${GLPK_LIBRARIES}
            INTERFACE_INCLUDE_DIRECTORIES ${GLPK_INCLUDE_DIR}
    )
endif()

if(ON) # STORM_HAVE_XERCES
    find_dependency(XercesC)
endif()
if(OFF) # STORM_HAVE_SOPLEX
    find_dependency(soplex)
endif()
if(OFF) # STORM_HAVE_GUROBI
    find_dependency(GUROBI)
    add_library(GUROBI UNKNOWN IMPORTED)
    set_target_properties(
            GUROBI
            PROPERTIES
            IMPORTED_LOCATION ${GUROBI_LIBRARY}
            INTERFACE_INCLUDE_DIRECTORIES ${GUROBI_INCLUDE_DIRS}
    )
endif()

add_library(cudd3 STATIC IMPORTED)
set_target_properties(
		cudd3
		PROPERTIES
		IMPORTED_LOCATION ${STORM_RESOURCE_LIBRARY_INSTALL_DIR}/libcudd.a
		INTERFACE_INCLUDE_DIRECTORIES ${STORM_RESOURCE_INCLUDE_INSTALL_DIR}/cudd/
)

if(ON) # STORM_HAVE_SPOT
    if(ON) # STORM_SHIPPED_SPOT
        add_library(Storm::Spot-bddx SHARED IMPORTED)
            set_target_properties(Storm::Spot-bddx PROPERTIES
                    INTERFACE_INCLUDE_DIRECTORIES "${STORM_RESOURCE_INCLUDE_INSTALL_DIR}/spot/"
                    IMPORTED_LOCATION ${STORM_RESOURCE_LIBRARY_INSTALL_DIR}/libbddx.dylib
                    )

        add_library(Storm::Spot SHARED IMPORTED)
        set_target_properties(Storm::Spot PROPERTIES
                INTERFACE_INCLUDE_DIRECTORIES "${STORM_RESOURCE_INCLUDE_INSTALL_DIR}/spot/"
                IMPORTED_LOCATION ${STORM_RESOURCE_LIBRARY_INSTALL_DIR}/libspot.dylib
                INTERFACE_LINK_LIBRARIES Storm::Spot-bddx
        )
    else()
        find_dependency(Spot)
        add_library(Storm::Spot UNKNOWN IMPORTED)
        set_target_properties(
                Storm::Spot
                PROPERTIES
                IMPORTED_LOCATION ${Spot_LIBRARIES}
                INTERFACE_INCLUDE_DIRECTORIES ${Spot_INCLUDE_DIR}
        )

    endif()
endif()


if(OFF)  # STORM_HAVE_MATHSAT
    set(MATHSAT_ROOT "")
    find_dependency(MATHSAT QUIET)
    add_library(mathsat UNKNOWN IMPORTED)
    set_target_properties(
            mathsat
            PROPERTIES
            IMPORTED_LOCATION ${MATHSAT_LIBRARIES}
            INTERFACE_INCLUDE_DIRECTORIES ${MATHSAT_INCLUDE_DIRS}
    )
endif()


set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH_save}")
unset(CMAKE_MODULE_PATH_save)

# Our library dependencies (contains definitions for IMPORTED targets)
if(NOT TARGET storm)
  include("${CMAKE_CURRENT_LIST_DIR}/stormTargets.cmake")
endif()

