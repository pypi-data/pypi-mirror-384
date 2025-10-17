#ifndef RYNLIB_FFIINCLUDE_HPP
#define RYNLIB_FFIINCLUDE_HPP

// adapted from https://stackoverflow.com/questions/5919996/how-to-detect-reliably-mac-os-x-ios-linux-windows-in-c-preprocessor
#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__) || defined(__NT__)
    #include "libffi/win/ffi.h"
#elif __APPLE__
    #ifndef MACOSX
    #define MACOSX
    #endif
    #include "libffi/osx/include/ffi.h"
#else
    #include <ffi.h> 
#endif

#endif

