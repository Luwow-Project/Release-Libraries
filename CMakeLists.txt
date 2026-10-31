cmake_minimum_required(VERSION 3.16)
# Downloaded files get the time they're extracted, so a new SDK rebuilds what uses it
if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()
project(LuwowLibraries LANGUAGES C CXX)
if(APPLE)
    enable_language(OBJCXX)
endif()

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(WIN32)
    # Define WIN32_LEAN_AND_MEAN to exclude rarely-used APIs.
    add_compile_definitions(
        WIN32_LEAN_AND_MEAN
    )
endif()

# Build options
#   Library DLLs, against the release's SDK:              -D RELEASE_VERSION=<tag>
#   Executables with the libraries bound into them:       -D RELEASE_VERSION=<tag> -D STATIC_BUILD=ON
# The DLLs only load into the executables of the release they were built against.
set(RELEASE_VERSION "v2026.10.31" CACHE STRING "The Luwow release the libraries are built for, such as v2026.10.31")
option(STATIC_BUILD "Build the release's executables with the libraries bound in, instead of the libraries as DLLs" OFF)

# Where the release comes from
set(LUWOW_RELEASE_REPOSITORY "https://github.com/Luwow-Project/Release" CACHE STRING "The Luwow Release repository")

include(FetchContent)

if(STATIC_BUILD)
    # The release's sources, which build the executables and bind in the libraries the folder below adds. A
    # local checkout can be used instead with -D FETCHCONTENT_SOURCE_DIR_LUWOWRELEASE=<folder>.
    message(STATUS "Luwow release ${RELEASE_VERSION}: executables with the libraries bound in")
    FetchContent_Declare(LuwowRelease
        GIT_REPOSITORY ${LUWOW_RELEASE_REPOSITORY}
        GIT_TAG ${RELEASE_VERSION}
        GIT_SHALLOW TRUE
    )
    set(LUWOW_LIBRARY_MODE "STATIC" CACHE STRING "" FORCE)
    set(LUWOW_LIBRARY_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/libraries" CACHE STRING "" FORCE)
    set(LUWOW_RELEASE_VERSION ${RELEASE_VERSION} CACHE STRING "" FORCE)
    FetchContent_MakeAvailable(LuwowRelease)
    return()
endif()

# The release's SDK for this platform, unless LuwowSDK_DIR already points at one, such as a local build's
if(NOT LuwowSDK_DIR)
    if(WIN32)
        set(sdkPlatform "windows")
    elseif(APPLE)
        set(sdkPlatform "macos")
    else()
        set(sdkPlatform "linux")
    endif()
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|ARM64|aarch64)$")
        string(APPEND sdkPlatform "-arm64")
    else()
        string(APPEND sdkPlatform "-x64")
    endif()
    set(LUWOW_SDK_PLATFORM ${sdkPlatform} CACHE STRING "The platform of the release's SDK zip, such as windows-x64")

    message(STATUS "Luwow release ${RELEASE_VERSION}: the SDK for ${LUWOW_SDK_PLATFORM}")
    FetchContent_Declare(LuwowSDK
        URL "${LUWOW_RELEASE_REPOSITORY}/releases/download/${RELEASE_VERSION}/luwow-sdk-${RELEASE_VERSION}-${LUWOW_SDK_PLATFORM}.zip"
    )
    FetchContent_MakeAvailable(LuwowSDK)
    set(LuwowSDK_DIR "${luwowsdk_SOURCE_DIR}/cmake")
endif()

find_package(LuwowSDK REQUIRED CONFIG)
message(STATUS "Luwow SDK ${LUWOW_SDK_VERSION}, module ABI ${LUWOW_SDK_ABI_VERSION}")

# What the libraries' CMake expects from a source build of the release
get_target_property(sdkIncludes Luwow::SDK INTERFACE_INCLUDE_DIRECTORIES)
get_target_property(sdkDefinitions Luwow::SDK INTERFACE_COMPILE_DEFINITIONS)
if(NOT sdkDefinitions)
    set(sdkDefinitions "")
endif()
set(ENGINE_ROOT ${sdkIncludes})
add_library(Luau.VM INTERFACE IMPORTED)
set_target_properties(Luau.VM PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${sdkIncludes}"
    INTERFACE_COMPILE_DEFINITIONS "${sdkDefinitions}"
)

add_subdirectory(libraries)

install(FILES .config.luau DESTINATION . COMPONENT libraries)
