set (LIB_NAME mhm_lib)
# use all mo_*.f90/F90 files for the library
file(GLOB sources_mpr MPR/*mo_*.*90)
file(GLOB sources_mhm mHM/*mo_*.*90)
file(GLOB sources_mrm mRM/*mo_*.*90)
file(GLOB sources_common common/*mo_*.*90)
file(GLOB sources_meteo meteo/*mo_*.*90)
file(GLOB sources_coupling coupling/*mo_*.*90)
list(APPEND sources ${sources_mpr} ${sources_mhm} ${sources_mrm} ${sources_common} ${sources_meteo} ${sources_coupling})

if(BUILD_MHM_LIB_SHARED)
  add_library(${LIB_NAME} SHARED ${sources})
else()
  add_library(${LIB_NAME} STATIC ${sources})
endif()

if(BUILD_MHM_LIB_PIC)
  set_property(TARGET ${LIB_NAME} PROPERTY POSITION_INDEPENDENT_CODE ON)
endif()

target_include_directories(${LIB_NAME} PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

# add FORCES
# when building sdist download forces to top folder with CPM by setting "source cache"
if(${SKBUILD_STATE} MATCHES "sdist")
  set(FORCES_WITH_NETCDF OFF)  # we don't need netcdf to create sdist
  message(STATUS "mHM: downloading forces for sdist")
  file(REMOVE_RECURSE "${CMAKE_CURRENT_SOURCE_DIR}/../forces")
endif()
# use CPM
include(../cmake/CPM.cmake)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../forces")
  message(STATUS "mHM: found local forces directory")
  set(CPM_forces_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/../forces" CACHE PATH "Local source path for FORCES.")
else()
  set(CPM_forces_SOURCE $ENV{MHM_BUILD_FORCES_PATH} CACHE PATH "Local source path for FORCES.")
endif()
# check forces version file
file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/../version_forces.txt" ver_forces LIMIT_COUNT 1)
# cmake directive to specify forces version: CPM_forces_VERSION
set(CPM_forces_VERSION "${ver_forces}" CACHE STRING "FORCES version to download with CPM.")
CPMAddPackage("https://git.ufz.de/chs/forces.git#${CPM_forces_VERSION}")
if(BUILD_MHM_LIB_SHARED OR BUILD_MHM_LIB_PIC)
  set_property(TARGET forces PROPERTY POSITION_INDEPENDENT_CODE ON)
endif()
target_link_libraries(${LIB_NAME} PUBLIC forces)

if(${SKBUILD_STATE} MATCHES "sdist")
    file(COPY "${FORCES_SOURCE_DIR}" DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}/..")
    get_filename_component(_fpath "${FORCES_SOURCE_DIR}" NAME)
    file(RENAME "${CMAKE_CURRENT_SOURCE_DIR}/../${_fpath}" "${CMAKE_CURRENT_SOURCE_DIR}/../forces")
    message(STATUS "mHM: copied forces from '${FORCES_SOURCE_DIR}' to './forces'.")
endif()

# check mhm specific env-vars
if(DEFINED ENV{MHM_BUILD_PARALLEL})
  set(CMAKE_WITH_OpenMP $ENV{MHM_BUILD_PARALLEL})
endif()
# add all compile options (MPI, OpenMP, Lapack, Coverage)
include(../cmake/compileoptions.cmake)
if (CMAKE_WITH_MPI)
  message(STATUS "mHM: use MPI")
  target_compile_definitions(${LIB_NAME} PRIVATE MPI)
  target_link_libraries(${LIB_NAME} PRIVATE MPI::MPI_Fortran)
endif()
if (CMAKE_WITH_OpenMP)
  message(STATUS "mHM: use OpenMP")
  target_link_libraries(${LIB_NAME} PRIVATE OpenMP::OpenMP_Fortran)
endif()

# by setting compile options and definitions PUBLIC, they are also used by
# programms linking agains it (mhm exe in this case)
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
  target_compile_definitions(${LIB_NAME} PRIVATE GFORTRAN)
  target_compile_options(${LIB_NAME} PUBLIC
    -ffree-line-length-none
    $<$<CONFIG:DEBUG>:-Og -g -Wall -Wextra -Wimplicit-interface -Wsurprising
      -fimplicit-none -fbacktrace -fcheck=all
      -ffpe-trap=zero,overflow,underflow -finit-real=snan -pedantic-errors>
    $<$<CONFIG:RELEASE>:-O3>
    $<$<BOOL:${CMAKE_WITH_GPROF}>:-pg>
  )
  # https://www.scivision.dev/gfortran-15-external-argument-mismatch
  # AND: passed procedures with pointer attribute should be called with positional arguments
  # see: mo_mrm_objective_function_runoff / mo_objective_function
  if(CMAKE_Fortran_COMPILER_VERSION VERSION_GREATER_EQUAL "15.0")
    target_compile_options(${LIB_NAME} PRIVATE $<$<CONFIG:DEBUG>:-Wno-external-argument-mismatch>)
  endif()
endif()
# ifort (Classic)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "Intel")
  target_compile_definitions(${LIB_NAME} PRIVATE INTEL)
  target_compile_options(${LIB_NAME} PUBLIC
    -nofixed "SHELL:-assume byterecl" -standard-realloc-lhs
    $<$<CONFIG:DEBUG>:-g -fp-model=source "SHELL:-warn all" "SHELL:-check all" "SHELL:-check noarg_temp_created" -debug -traceback -fp-stack-check -O0>
    $<$<CONFIG:RELEASE>:-O3 -qoverride-limits -fp-model=precise -fprotect-parens>
  )
endif()
# ifx (IntelLLVM)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "IntelLLVM")
  target_compile_definitions(${LIB_NAME} PRIVATE INTEL)
  target_compile_options(${LIB_NAME} PUBLIC
    -nofixed "SHELL:-assume byterecl" -standard-realloc-lhs
    $<$<CONFIG:DEBUG>:-g -fp-model=source "SHELL:-warn all" "SHELL:-check all" "SHELL:-check noarg_temp_created" "SHELL:-check nouninit" -traceback -O0>
    $<$<CONFIG:RELEASE>:-O3 -qoverride-limits -fp-model=precise -fprotect-parens>
  )
endif()
if(CMAKE_Fortran_COMPILER_ID MATCHES "NAG")
  target_compile_definitions(${LIB_NAME} PRIVATE NAG)
  target_compile_options(${LIB_NAME} PUBLIC
    -fpp -colour -unsharedf95 -ideclient
    # "-C=all" is not set, only "-C -C=alias -C=dangling" and "-ieee=full" instead of "-ieee=stop" because
    # this effectively omits the -C=intovf flag which checks for integer overflow
    # we need to exclude that as the random number generator relies on that technique
    # -ieee=full is needed for mo_utils (is_nan, is_finite etc. fails with -ieee=stop)
    $<$<CONFIG:DEBUG>:-gline -g -nan -O0 -C -C=alias -C=dangling -strict95 -ieee=full>
    $<$<CONFIG:RELEASE>:-O4 -ieee=full>
  )
endif()
