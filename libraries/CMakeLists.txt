# Every library, in one place for both builds: added from this repository's CMakeLists.txt for DLLs, and
# from the release's through LUWOW_LIBRARY_DIRS for static builds. luwow_add_library comes from the SDK or
# the release's sources, ENGINE_ROOT and Luau.VM likewise.

set(GUI_ROOT ${CMAKE_CURRENT_LIST_DIR}/gui)
set(TASK_ROOT ${CMAKE_CURRENT_LIST_DIR}/task)
set(FS_ROOT ${CMAKE_CURRENT_LIST_DIR}/fs)
set(IO_ROOT ${CMAKE_CURRENT_LIST_DIR}/io)
set(NET_ROOT ${CMAKE_CURRENT_LIST_DIR}/net)
set(SIGNAL_ROOT ${CMAKE_CURRENT_LIST_DIR}/signal)
set(LIBUV_ROOT ${CMAKE_CURRENT_LIST_DIR}/../extern/libuv)

set(LUWOW_LIBRARIES task fs io signal net)
if(WIN32 OR APPLE)
    list(PREPEND LUWOW_LIBRARIES gui)
endif()

# Each library's DLL from its src folder, and its types, scripts/<name>.luau,
# into a types folder besides the libraries folder.
foreach(name IN LISTS LUWOW_LIBRARIES)
    add_subdirectory(${CMAKE_CURRENT_LIST_DIR}/${name}/src ${name})
    install(FILES ${CMAKE_CURRENT_LIST_DIR}/${name}/scripts/${name}.luau DESTINATION types COMPONENT libraries)
endforeach()

# Only the static uv_a is linked into task, skip building uv.dll and libuv's tests
set(LIBUV_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(LIBUV_BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(${LIBUV_ROOT} libuv)
