/**
 * @file CMakeOptions.h
 * @author Gereon Kremer <gereon.kremer@cs.rwth-aachen.de>
 */

#pragma once

#include <iostream>

namespace carl {

void printCMakeOptions(std::ostream& os);

namespace cmakeoptions {

	static constexpr auto _ALLOW_STORM_FETCH = "ON";
	static constexpr auto _ALLOW_STORM_SYSTEM = "OFF";
	static constexpr auto _ALLWARNINGS = "OFF";
	static constexpr auto _BUILD_DOXYGEN = "OFF";
	static constexpr auto _BUILD_STATIC = "OFF";
	static constexpr auto _Boost_DIR = "/opt/homebrew/lib/cmake/Boost-1.89.0";
	static constexpr auto _CARL_BIN_INSTALL_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib/bin";
	static constexpr auto _CARL_CMAKE_INSTALL_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib/lib/cmake/storm";
	static constexpr auto _CARL_COMPILE_BENCHMARKS = "OFF";
	static constexpr auto _CARL_INCLUDE_INSTALL_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib/include/storm/resources";
	static constexpr auto _CARL_LIB_INSTALL_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib/lib/storm/resources";
	static constexpr auto _CARL_LOGGING = "OFF";
	static constexpr auto _CARL_WARNING_AS_ERROR = "OFF";
	static constexpr auto _CLANG_SANITIZER = "none";
	static constexpr auto _CMAKE_BUILD_TYPE = "Release";
	static constexpr auto _CMAKE_FIND_ROOT_PATH_MODE_PACKAGE = "BOTH";
	static constexpr auto _CMAKE_INSTALL_PREFIX = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib";
	static constexpr auto _CMAKE_MAKE_PROGRAM = "/opt/homebrew/bin/ninja";
	static constexpr auto _CMAKE_PREFIX_PATH = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp/lib/python3.14/site-packages";
	static constexpr auto _DEVELOPER = "OFF";
	static constexpr auto _EXECUTABLE_OUTPUT_PATH = "/Users/runner/work/synthesis/synthesis/build/cp314-cp314-macosx_14_0_arm64/_deps/carl-build/bin";
	static constexpr auto _FETCHCONTENT_BASE_DIR = "/Users/runner/work/synthesis/synthesis/build/cp314-cp314-macosx_14_0_arm64/_deps";
	static constexpr auto _FETCHCONTENT_FULLY_DISCONNECTED = "OFF";
	static constexpr auto _FETCHCONTENT_QUIET = "OFF";
	static constexpr auto _FETCHCONTENT_SOURCE_DIR_CARL = "";
	static constexpr auto _FETCHCONTENT_SOURCE_DIR_STORM = "";
	static constexpr auto _FETCHCONTENT_UPDATES_DISCONNECTED = "OFF";
	static constexpr auto _FETCHCONTENT_UPDATES_DISCONNECTED_CARL = "OFF";
	static constexpr auto _FETCHCONTENT_UPDATES_DISCONNECTED_STORM = "OFF";
	static constexpr auto _FORCE_SHIPPED_GMP = "OFF";
	static constexpr auto _FORCE_SHIPPED_RESOURCES = "OFF";
	static constexpr auto _LOGGING_DISABLE_INEFFICIENT = "OFF";
	static constexpr auto _PRUNE_MONOMIAL_POOL = "ON";
	static constexpr auto _PYBIND11_PYTHONLIBS_OVERWRITE = "ON";
	static constexpr auto _PYBIND11_PYTHON_VERSION = "";
	static constexpr auto _Python3_EXECUTABLE = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp/bin/python";
	static constexpr auto _Python3_FIND_REGISTRY = "NEVER";
	static constexpr auto _Python3_INCLUDE_DIR = "/Library/Frameworks/Python.framework/Versions/3.14/include/python3.14";
	static constexpr auto _Python3_ROOT_DIR = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp";
	static constexpr auto _Python_EXECUTABLE = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp/bin/python";
	static constexpr auto _Python_FIND_REGISTRY = "NEVER";
	static constexpr auto _Python_INCLUDE_DIR = "/Library/Frameworks/Python.framework/Versions/3.14/include/python3.14";
	static constexpr auto _Python_ROOT_DIR = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp";
	static constexpr auto _SKBUILD = "2";
	static constexpr auto _SKBUILD_CORE_VERSION = "0.11.6";
	static constexpr auto _SKBUILD_DATA_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/data";
	static constexpr auto _SKBUILD_HEADERS_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/headers";
	static constexpr auto _SKBUILD_METADATA_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/metadata";
	static constexpr auto _SKBUILD_NULL_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/null";
	static constexpr auto _SKBUILD_PLATLIB_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/platlib";
	static constexpr auto _SKBUILD_PROJECT_NAME = "paynt";
	static constexpr auto _SKBUILD_PROJECT_VERSION = "0.2.1";
	static constexpr auto _SKBUILD_PROJECT_VERSION_FULL = "0.2.1";
	static constexpr auto _SKBUILD_SABI_COMPONENT = "";
	static constexpr auto _SKBUILD_SABI_VERSION = "";
	static constexpr auto _SKBUILD_SCRIPTS_DIR = "/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/tmpsqrpeys0/wheel/scripts";
	static constexpr auto _SKBUILD_SOABI = "cpython-314-darwin";
	static constexpr auto _SKBUILD_STATE = "wheel";
	static constexpr auto _STORM_ALLWARNINGS = "OFF";
	static constexpr auto _STORM_BIN_INSTALL_DIR = "bin/storm";
	static constexpr auto _STORM_CARL_GIT_REPO = "https://github.com/moves-rwth/carl-storm.git";
	static constexpr auto _STORM_CMAKE_INSTALL_DIR = "lib/cmake/storm";
	static constexpr auto _STORM_COMPILE_WITH_ADDRESS_SANITIZER = "OFF";
	static constexpr auto _STORM_COMPILE_WITH_ALL_SANITIZERS = "OFF";
	static constexpr auto _STORM_DEVELOPER = "OFF";
	static constexpr auto _STORM_DIR_HINT = "";
	static constexpr auto _STORM_DISABLE_GLPK = "OFF";
	static constexpr auto _STORM_DISABLE_GMM = "OFF";
	static constexpr auto _STORM_DISABLE_GUROBI = "OFF";
	static constexpr auto _STORM_DISABLE_MATHSAT = "OFF";
	static constexpr auto _STORM_DISABLE_SOPLEX = "OFF";
	static constexpr auto _STORM_DISABLE_SPOT = "OFF";
	static constexpr auto _STORM_DISABLE_XERCES = "OFF";
	static constexpr auto _STORM_DISABLE_Z3 = "OFF";
	static constexpr auto _STORM_GIT_REPO = "https://github.com/moves-rwth/storm.git";
	static constexpr auto _STORM_GIT_TAG = "1.11.1";
	static constexpr auto _STORM_INCLUDE_INSTALL_DIR = "include/storm";
	static constexpr auto _STORM_LIB_INSTALL_DIR = "lib/storm";
	static constexpr auto _STORM_LOAD_QVBS = "OFF";
	static constexpr auto _STORM_LOG_DISABLE_DEBUG = "ON";
	static constexpr auto _STORM_RESOURCE_INCLUDE_INSTALL_DIR = "include/storm/resources";
	static constexpr auto _STORM_RESOURCE_LIBRARY_INSTALL_DIR = "lib/storm/resources";
	static constexpr auto _STORM_SPOT_FORCE_SHIPPED = "OFF";
	static constexpr auto _STORM_USE_CLN_EA = "OFF";
	static constexpr auto _STORM_USE_CLN_RF = "ON";
	static constexpr auto _TIMING = "OFF";
	static constexpr auto _USE_BLISS = "OFF";
	static constexpr auto _USE_COCOA = "OFF";
	static constexpr auto _USE_MPFR_FLOAT = "OFF";
	static constexpr auto _USE_Z3_NUMBERS = "OFF";
	static constexpr auto _Z3_DIR = "/opt/homebrew/lib/cmake/z3";
	static constexpr auto _pybind11_DIR = "/private/var/folders/y6/nj790rtn62lfktb1sh__79hc0000gn/T/build-env-tcamnpgp/lib/python3.14/site-packages/pybind11/share/cmake/pybind11";
}

}
