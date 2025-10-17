# This file fetches the non-GPL ffmpeg libraries from the torchcodec S3 bucket,
# and exposes them as CMake targets so we can dynamically link against them.
# These libraries were built on the CI via the build_ffmpeg.yaml workflow.

# Avoid warning: see https://cmake.org/cmake/help/latest/policy/CMP0135.html
if (CMAKE_VERSION VERSION_GREATER_EQUAL "3.24.0")
    cmake_policy(SET CMP0135 NEW)
endif()

include(FetchContent)

if (UNIX AND NOT APPLE)
    set(LINUX TRUE)
else()
    set(LINUX FALSE)
endif()

set(
    base_url
    https://pytorch.s3.amazonaws.com/torchcodec/ffmpeg/2025-03-14
)

if (LINUX)
    set(lib_dir "lib")

    set(
        platform_url
        ${base_url}/linux_x86_64
    )

    set(
        f4_sha256
        1a083f1922443bedb5243d04896383b8c606778a7ddb9d886c8303e55339fe0c
    )
    set(
        f5_sha256
        65d6ad54082d94dcb3f801d73df2265e0e1bb303c7afbce7723e3b77ccd0e207
    )
    set(
        f6_sha256
        8bd5939c2f4a4b072e837e7870c13fe7d13824e5ff087ab534e4db4e90b7be9c
    )
    set(
        f7_sha256
        1cb946d8b7c6393c2c3ebe1f900b8de7a2885fe614c45d4ec32c9833084f2f26
    )
    set(
        f8_sha256
        c55b3c1a4b5e4d5fdd7c632bea3ab6f45b4e37cc8e0999dda3f84a8ed8defad8
    )
    set(
       f4_library_file_names
       libavutil.so.56
       libavcodec.so.58
       libavformat.so.58
       libavdevice.so.58
       libavfilter.so.7
       libswscale.so.5
       libswresample.so.3
    )
    set(
       f5_library_file_names
       libavutil.so.57
       libavcodec.so.59
       libavformat.so.59
       libavdevice.so.59
       libavfilter.so.8
       libswscale.so.6
       libswresample.so.4
    )
    set(
       f6_library_file_names
       libavutil.so.58
       libavcodec.so.60
       libavformat.so.60
       libavdevice.so.60
       libavfilter.so.9
       libswscale.so.7
       libswresample.so.4
    )
    set(
       f7_library_file_names
       libavutil.so.59
       libavcodec.so.61
       libavformat.so.61
       libavdevice.so.61
       libavfilter.so.10
       libswscale.so.8
       libswresample.so.5
    )
    set(
       f8_library_file_names
       libavutil.so.60
       libavcodec.so.62
       libavformat.so.62
       libavdevice.so.62
       libavfilter.so.11
       libswscale.so.9
       libswresample.so.6
    )
elseif (APPLE)
    set(lib_dir "lib")
    set(
        platform_url
        ${base_url}/macos_arm64
    )
    set(
        f4_sha256
        f0335434529d9e19359eae0fe912dd9e747667534a1c92e662f5219a55dfad8c
    )
    set(
        f5_sha256
        cfc3449c9af6863731a431ce89e32c08c5f8ece94b306fb6b695828502a76166
    )
    set(
        f6_sha256
        ec47b4783c342038e720e33b2fdfa55a9a490afb1cf37a26467733983688647e
    )
    set(
        f7_sha256
        48a4fc8ce098305cfd4a58f40889249c523ca3c285f66ba704b5bad0e3ada53a
    )
    set(
        f8_sha256
        beb936b76f25d2621228a12cdb67c9ae3d1eff7aa713ef8d1167ebf0c25bd5ec
    )

    set(
       f4_library_file_names
       libavutil.56.dylib
       libavcodec.58.dylib
       libavformat.58.dylib
       libavdevice.58.dylib
       libavfilter.7.dylib
       libswscale.5.dylib
       libswresample.3.dylib
    )
    set(
       f5_library_file_names
       libavutil.57.dylib
       libavcodec.59.dylib
       libavformat.59.dylib
       libavdevice.59.dylib
       libavfilter.8.dylib
       libswscale.6.dylib
       libswresample.4.dylib
    )
    set(
       f6_library_file_names
       libavutil.58.dylib
       libavcodec.60.dylib
       libavformat.60.dylib
       libavdevice.60.dylib
       libavfilter.9.dylib
       libswscale.7.dylib
       libswresample.4.dylib
    )
    set(
       f7_library_file_names
       libavutil.59.dylib
       libavcodec.61.dylib
       libavformat.61.dylib
       libavdevice.61.dylib
       libavfilter.10.dylib
       libswscale.8.dylib
       libswresample.5.dylib
    )
    set(
       f8_library_file_names
       libavutil.60.dylib
       libavcodec.62.dylib
       libavformat.62.dylib
       libavdevice.62.dylib
       libavfilter.11.dylib
       libswscale.9.dylib
       libswresample.6.dylib
    )

elseif (WIN32)
    set(lib_dir "bin")
    set(
        platform_url
        ${base_url}/windows_x86_64
    )
    set(
        f4_sha256
        270a1aa8892225267e68a7eb87c417931da30dccbf08ee2bde8833e659cab5cb
    )
    set(
        f5_sha256
        b8b2a349a847e56a6da875b066dff1cae53cb8ee7cf5ba9321ec1243dea0cde0
    )
    set(
        f6_sha256
        5d9f8c76dc55f790fa31d825985e9270bf9e498b8bfec21a0ad3a1feb1fa053a
    )
    set(
        f7_sha256
        ae391ace382330e912793b70b68529ee7c91026d2869b4df7e7c3e7d3656bdd5
    )
    set(
        f8_sha256
        bac845ac79876b104959cb0e7b9dec772a261116344dd17d2f97e7ddfac4a73f
    )

    set(
        f4_library_file_names
        avutil.lib
        avcodec.lib
        avformat.lib
        avdevice.lib
        avfilter.lib
        swscale.lib
        swresample.lib
    )
    set(
        f5_library_file_names
        avutil.lib
        avcodec.lib
        avformat.lib
        avdevice.lib
        avfilter.lib
        swscale.lib
        swresample.lib
    )
    set(
        f6_library_file_names
        avutil.lib
        avcodec.lib
        avformat.lib
        avdevice.lib
        avfilter.lib
        swscale.lib
        swresample.lib
    )
    set(
        f7_library_file_names
        avutil.lib
        avcodec.lib
        avformat.lib
        avdevice.lib
        avfilter.lib
        swscale.lib
        swresample.lib
    )
    set(
        f8_library_file_names
        avutil.lib
        avcodec.lib
        avformat.lib
        avdevice.lib
        avfilter.lib
        swscale.lib
        swresample.lib
    )
else()
    message(
        FATAL_ERROR
        "Unsupported operating system: ${CMAKE_SYSTEM_NAME}"
    )
endif()

FetchContent_Declare(
    f4
    URL ${platform_url}/4.4.4.tar.gz
    URL_HASH
    SHA256=${f4_sha256}
)
FetchContent_Declare(
    f5
    URL ${platform_url}/5.1.4.tar.gz
    URL_HASH
    SHA256=${f5_sha256}
)
FetchContent_Declare(
    f6
    URL ${platform_url}/6.1.1.tar.gz
    URL_HASH
    SHA256=${f6_sha256}
)
FetchContent_Declare(
    f7
    URL ${platform_url}/7.0.1.tar.gz
    URL_HASH
    SHA256=${f7_sha256}
)
FetchContent_Declare(
    f8
    URL ${platform_url}/8.0.tar.gz
    URL_HASH
    SHA256=${f8_sha256}
)

FetchContent_MakeAvailable(f4 f5 f6 f7 f8)

add_library(ffmpeg4 INTERFACE)
add_library(ffmpeg5 INTERFACE)
add_library(ffmpeg6 INTERFACE)
add_library(ffmpeg7 INTERFACE)
add_library(ffmpeg8 INTERFACE)

# Note: the f?_SOURCE_DIR variables were set by FetchContent_MakeAvailable
target_include_directories(ffmpeg4 INTERFACE ${f4_SOURCE_DIR}/include)
target_include_directories(ffmpeg5 INTERFACE ${f5_SOURCE_DIR}/include)
target_include_directories(ffmpeg6 INTERFACE ${f6_SOURCE_DIR}/include)
target_include_directories(ffmpeg7 INTERFACE ${f7_SOURCE_DIR}/include)
target_include_directories(ffmpeg8 INTERFACE ${f8_SOURCE_DIR}/include)


list(
    TRANSFORM f4_library_file_names
    PREPEND ${f4_SOURCE_DIR}/${lib_dir}/
    OUTPUT_VARIABLE f4_library_paths
)
list(
    TRANSFORM f5_library_file_names
    PREPEND ${f5_SOURCE_DIR}/${lib_dir}/
    OUTPUT_VARIABLE f5_library_paths
)
list(
    TRANSFORM f6_library_file_names
    PREPEND ${f6_SOURCE_DIR}/${lib_dir}/
    OUTPUT_VARIABLE f6_library_paths
)
list(
    TRANSFORM f7_library_file_names
    PREPEND ${f7_SOURCE_DIR}/${lib_dir}/
    OUTPUT_VARIABLE f7_library_paths
)
list(
    TRANSFORM f8_library_file_names
    PREPEND ${f8_SOURCE_DIR}/${lib_dir}/
    OUTPUT_VARIABLE f8_library_paths
)

target_link_libraries(
    ffmpeg4
    INTERFACE
    ${f4_library_paths}
)
target_link_libraries(
    ffmpeg5
    INTERFACE
    ${f5_library_paths}
)
target_link_libraries(
    ffmpeg6
    INTERFACE
    ${f6_library_paths}
)
target_link_libraries(
    ffmpeg7
    INTERFACE
    ${f7_library_paths}
)
target_link_libraries(
    ffmpeg8
    INTERFACE
    ${f8_library_paths}
)
