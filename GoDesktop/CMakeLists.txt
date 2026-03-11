cmake_minimum_required(VERSION 3.20)
project(GoDesktop LANGUAGES CXX VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build type defaults
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Compiler warnings
add_compile_options(-Wall -Wextra -Werror -Wpedantic)

# Debug/Release specific flags
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_definitions(QT_QML_DEBUG)
    add_compile_options(-g -O0)
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O2 -DNDEBUG)
endif()

# Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network PrintSupport)

# OpenSSL (AES-ECB + RSA for upstream encrypt)
find_package(OpenSSL REQUIRED)

# Sources — core
set(CORE_SOURCES
    src/core/add_agent_dialog.cpp
    src/core/api_client.cpp
    src/core/api_error.cpp
    src/core/auth_window.cpp
    src/core/auth_widget.cpp
    src/core/confirm_dialog.cpp
    src/core/cookies_dialog.cpp
    src/core/customers_page.cpp
    src/core/date_range_picker.cpp
    src/core/flow_layout.cpp
    src/core/home_page.cpp
    src/core/loading_overlay.cpp
    src/core/main_widget.cpp
    src/core/report_page_builder.cpp
    src/core/report_pages.cpp
    src/core/settings_dialog.cpp
    src/core/theme_manager.cpp
    src/core/toast_widget.cpp
    src/core/toggle_switch.cpp
    src/core/translator.cpp
    src/core/upstream_client.cpp
    src/core/upstream_crypto.cpp
)

# Sources — utils
set(UTILS_SOURCES
    src/utils/feedback.cpp
    src/utils/upstream_translate.cpp
)

# Headers — core
set(CORE_HEADERS
    src/core/add_agent_dialog.h
    src/core/api_client.h
    src/core/api_error.h
    src/core/auth_window.h
    src/core/auth_widget.h
    src/core/confirm_dialog.h
    src/core/cookies_dialog.h
    src/core/customers_page.h
    src/core/date_range_picker.h
    src/core/flow_layout.h
    src/core/home_page.h
    src/core/icon_defs.h
    src/core/loading_overlay.h
    src/core/main_widget.h
    src/core/report_page_builder.h
    src/core/report_pages.h
    src/core/settings_dialog.h
    src/core/toast_widget.h
    src/core/toggle_switch.h
    src/core/theme_manager.h
    src/core/translator.h
    src/core/upstream_client.h
    src/core/upstream_crypto.h
)

# Headers — utils
set(UTILS_HEADERS
    src/utils/feedback.h
    src/utils/upstream_translate.h
)

# Resources
set(RESOURCES assets/resources.qrc)

# Executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    ${CORE_SOURCES}
    ${UTILS_SOURCES}
    ${CORE_HEADERS}
    ${UTILS_HEADERS}
    ${RESOURCES}
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
    Qt6::PrintSupport
    OpenSSL::SSL
    OpenSSL::Crypto
)
