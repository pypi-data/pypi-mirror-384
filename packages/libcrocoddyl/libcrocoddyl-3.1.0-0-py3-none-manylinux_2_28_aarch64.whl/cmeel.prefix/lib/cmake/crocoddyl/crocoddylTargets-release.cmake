#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "crocoddyl::crocoddyl" for configuration "Release"
set_property(TARGET crocoddyl::crocoddyl APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(crocoddyl::crocoddyl PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libcrocoddyl.so"
  IMPORTED_SONAME_RELEASE "libcrocoddyl.so"
  )

list(APPEND _cmake_import_check_targets crocoddyl::crocoddyl )
list(APPEND _cmake_import_check_files_for_crocoddyl::crocoddyl "${_IMPORT_PREFIX}/lib/libcrocoddyl.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
