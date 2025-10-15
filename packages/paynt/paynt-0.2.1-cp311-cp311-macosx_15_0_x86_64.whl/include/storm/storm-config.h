/*
 * Storm - Build Options
 *
 * This file is parsed by CMake during Makefile generation
 * It contains build and configuration information
 */

#pragma once


// Directories
// ###########
// The directory of the sources from which Storm was built.
#define STORM_SOURCE_DIR "/Users/runner/work/synthesis/synthesis/build/cp311-cp311-macosx_15_0_x86_64/_deps/storm-src"
// The directory in which Storm was built.
#define STORM_BUILD_DIR "/Users/runner/work/synthesis/synthesis/build/cp311-cp311-macosx_15_0_x86_64/_deps/storm-build"
// The directory of the test resources used in the tests (model files, ...).
#define STORM_TEST_RESOURCES_DIR "/Users/runner/work/synthesis/synthesis/build/cp311-cp311-macosx_15_0_x86_64/_deps/storm-src/resources/examples/testfiles"
// Carl include directory used during compilation.
#define STORM_CARL_INCLUDE_DIR "/Users/runner/work/synthesis/synthesis/build/cp311-cp311-macosx_15_0_x86_64/_deps/carl-src/src"


// Storm configuration options
// ###########################
// Whether benchmarks from QVBS can be used as input
/* #undef STORM_HAVE_QVBS */
// The root directory of QVBS
/* #undef STORM_QVBS_ROOT */
// Logging configuration
/* #undef STORM_LOGGING_FRAMEWORK */
#define STORM_LOG_DISABLE_DEBUG


// Carl configuration
// ###################
// Whether carl is available and to be used
#define STORM_HAVE_CARL
// Whether carl has headers for forward declarations
#define STORM_CARL_SUPPORTS_FWD_DECL
// Version of CARL used by Storm.
#define STORM_CARL_VERSION_MAJOR 14
#define STORM_CARL_VERSION_MINOR 33
#define STORM_CARL_VERSION 14.33


// GMP
// ###
// Whether GMP is available  (it is always available nowadays)
#define STORM_HAVE_GMP
// Include directory for GMP headers
#define GMP_INCLUDE_DIR "/usr/local/include"
#define GMPXX_INCLUDE_DIR "/usr/local/include"


// CLN
// ###
// Whether CLN is available and to be used
#define STORM_HAVE_CLN
// Whether Storm uses CLN for rationals and rational functions
/* #undef STORM_USE_CLN_EA */
#define STORM_USE_CLN_RF


// Z3 configuration
// ################
// Whether Z3 is available and to be used
#define STORM_HAVE_Z3
// Whether the optimization feature of Z3 is available and to be used
#define STORM_HAVE_Z3_OPTIMIZE
// Whether Z3 uses standard integers
#define STORM_Z3_API_USES_STANDARD_INTEGERS
// Version of Z3 used by Storm.
#define STORM_Z3_VERSION 4.15.3


// Dependencies
// ############
// Whether the libraries are available and to be used
#define STORM_HAVE_GMM
#define STORM_HAVE_GLPK
/* #undef STORM_HAVE_GUROBI */
/* #undef STORM_HAVE_MATHSAT */
/* #undef STORM_HAVE_SOPLEX */
#define STORM_HAVE_SPOT
#define STORM_HAVE_XERCES
#define STORM_HAVE_LP_SOLVER
// Whether LTL model checking shall be enabled
#ifdef STORM_HAVE_SPOT
   #define STORM_HAVE_LTL_MODELCHECKING_SUPPORT
#endif // STORM_HAVE_SPOT
