cmake_minimum_required(VERSION 3.20)
project(GoDesktop LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

# Compiler warnings
add_compile_options(-Wall -Wextra -Werror)

# Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)

# Sources
set(SOURCES
    src/main.cpp
    src/core/api_client.cpp
    src/core/auth_window.cpp
    src/core/auth_widget.cpp
    src/core/main_widget.cpp
    src/core/theme_manager.cpp
    src/core/translator.cpp
)

set(HEADERS
    src/core/api_client.h
    src/core/auth_window.h
    src/core/auth_widget.h
    src/core/main_widget.h
    src/core/theme_manager.h
    src/core/translator.h
)

# Resources
set(RESOURCES assets/resources.qrc)

# Executable
add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS} ${RESOURCES})

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
)
