cmake_minimum_required(VERSION 3.10 FATAL_ERROR)
project(native-test VERSION 0.1)

if (MSVC)
  add_compile_definitions(UNICODE=1 _UNICODE=1 __SSE__=1
    _CRT_SECURE_NO_WARNINGS=1 D_SCL_SECURE_NO_WARNINGS=1
    _SCL_SECURE_NO_DEPRECATE=1 _CRT_NONSTDC_NO_WARNINGS=1
    _ENABLE_EXTENDED_ALIGNED_STORAGE=1 NOMINMAX=1)
endif()

find_package(Python "${PYTHON_VERSION}" EXACT REQUIRED COMPONENTS Development)

add_library(native_test STATIC
            cmake_lib.c
            )
target_link_libraries(native_test PUBLIC Python::Module)