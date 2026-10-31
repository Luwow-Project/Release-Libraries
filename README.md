# Libraries build repository for Luwow-Project

This repository builds Luwow's libraries for a release of [Luwow](https://github.com/Luwow-Project/Release). Each library is a submodule under `libraries/`.

By default the libraries are built as DLLs, against the SDK the release publishes. They only load into that release's executables. A static build instead builds the release's executables from its sources, with the libraries bound into them.

## Requirements

* C++ 20 compatible compiler
* CMake 3.16 or later
* An internet connection at configure time, for the release's SDK (or its sources, for a static build)
* Linux: libcurl, for `net.request` (`libcurl4-openssl-dev`)

-----

## Supported Platforms

* Windows (Visual C++)
* MacOS (Xcode's Clang)
* Linux (GCC or Clang), without gui

-----

## Setting Up

### 1. Clone the Repository

```bash
git clone <this repository> LuwowLibraries --recurse-submodules
cd LuwowLibraries
```

If you forget the --recurse-submodules flag, you can follow up with:
```bash
git submodule update --init --recursive
```

### 2. Configure and Build

The DLLs, for the release in `CMakeLists.txt`'s `RELEASE_VERSION`:
```bash
cmake -S . -B build -D CMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

They're written to `build/libraries` (`build/libraries/Release` with Visual Studio). For another release:
```bash
cmake -S . -B build -D RELEASE_VERSION=v2026.10.31
```

Executables with the libraries bound in:
```bash
cmake -S . -B build-static -D CMAKE_BUILD_TYPE=Release -D STATIC_BUILD=ON
cmake --build build-static --config Release
```

| Option | Default | |
|---|---|---|
| `RELEASE_VERSION` | the release in `CMakeLists.txt` | The Luwow release whose SDK, or sources, the libraries are built with |
| `STATIC_BUILD` | `OFF` | Builds the release's executables with the libraries bound in, instead of DLLs |
| `LuwowSDK_DIR` | | An SDK's `cmake` folder to use instead of downloading the release's, such as a local Release build's |
| `FETCHCONTENT_SOURCE_DIR_LUWOWRELEASE` | | A Release checkout to use instead of downloading its sources, for a static build |
| `LUWOW_<NAME>_MODE` | the library's first | A library's run mode, `SERIAL` or `PARALLEL`, where it supports both |

### 3. Run the Tests

With the release's executables, from its `luwow-<version>-<os>.zip`:
```bash
python tests/run_tests.py --bin <folder with runscript>
```

A static build's executables have the libraries in them:
```bash
python tests/run_tests.py --bin build-static/bin/Release --static
```

-----

## Usage

Extract `luwow-libraries-<version>-<os>.zip` next to the release's executables. It has two folders: `libraries`, the DLLs a `.config.luau`'s `dlls` points at, and `types`, each library's types from its source.

```luau
return {
    luau = {
        aliases = { Luwow = "./types" },
        dlls = "./libraries",
    },
}
```

`cmake --install build --config Release --prefix <folder> --component libraries` lays out the same two folders from a local build. To learn how to use the libraries, you can head over to the [documentation](https://luwow-project.github.io/Documentation/tutorials/setup/#usage).
