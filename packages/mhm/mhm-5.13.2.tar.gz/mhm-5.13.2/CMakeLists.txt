# mHM cmake script
cmake_minimum_required(VERSION 3.14)
# get version and date from files (version.txt and version_date.txt)
include(cmake/version.cmake)
get_version(MHM_VER MHM_VER_DEV MHM_DATE)
# create the project
project(mhm
  VERSION ${MHM_VER}
  DESCRIPTION "The mesoscale Hydrological Model"
  HOMEPAGE_URL "https://www.ufz.de/mhm"
  LANGUAGES Fortran C
)

message(STATUS "mHM: build type - ${CMAKE_BUILD_TYPE}")

option(BUILD_MHM_DRIVER "Build mHM with executable driver." ON)
option(BUILD_MHM_PYBIND "Build mHM python bindings." OFF)
option(BUILD_MHM_LIB_SHARED "Build mhm library as shared." OFF)
option(BUILD_MHM_LIB_PIC "Build mhm library as position independent." OFF)

if(BUILD_MHM_PYBIND)
  set(BUILD_MHM_LIB_SHARED OFF)
  set(BUILD_MHM_LIB_PIC ON)
  set(BUILD_MHM_DRIVER OFF)
endif()

add_subdirectory(src)

if(BUILD_MHM_DRIVER)
  add_executable(mhm src/mHM/mhm_driver.f90)
  target_link_libraries(mhm PRIVATE mhm_lib)
  install(TARGETS mhm DESTINATION bin)
endif()

if(BUILD_MHM_PYBIND)
  add_subdirectory(pybind/src)
endif()

# add full version and date to pre-processor flags (qoutes need in before hand)
target_compile_definitions(mhm_lib PRIVATE
  MHMVERSION='${MHM_VER_DEV}'
  MHMDATE='${MHM_DATE}'
)

# setup coverage with GNU
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU" AND CMAKE_WITH_COVERAGE AND EXISTS "CI-scripts")
  message(STATUS "mHM: add coverage")
  include(cmake/CodeCoverage.cmake)
  append_coverage_compiler_flags_to_target(mhm_lib)
  append_coverage_compiler_flags_to_target(mhm)
  SETUP_TARGET_FOR_COVERAGE_LCOV(
    NAME mhm_coverage_CI
    EXECUTABLE ../CI-scripts/run_cmake_coverage.sh
    DEPENDENCIES mhm mhm_lib
    GENHTML_ARGS -t "mHM coverage" --html-prolog ../doc/html_files/cov_header.prolog
  )
endif()
# automatically enable testing (OFF by default)
option(BUILD_TESTING "Build with pfUnit tests." OFF)
include(CTest)
# add pfunit test folder
if(BUILD_TESTING AND EXISTS "src/tests")
  add_subdirectory(src/tests)
endif()

# With this, paths are added to the INSTALL_RPATH, and via the second command also to the build.
if (CMAKE_BUILD_MODULE_SYSTEM_INDEPENDENT)
  set_target_properties(mhm
    PROPERTIES
    INSTALL_RPATH "${CMAKE_Fortran_IMPLICIT_LINK_DIRECTORIES}"
    BUILD_WITH_INSTALL_RPATH ON
  )
endif()
