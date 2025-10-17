#ifndef RYNLIB_FFIWINDOWS_HPP
#define RYNLIB_FFIWINDOWS_HPP

// check various compiler setups
#if defined(__amd64__) || defined(__amd64) || defined(__x86_64__) || defined(__x86_64) || defined(_M_AMD64)
    #include "amd64/include/ffi.h"
#else
#if defined(__aarch64__)
    #include "arm64/include/ffi.h"
#else
#if defined(_WIN32)
    #include "win32/include/ffi.h"
#else 
    error "Indeterminate architectured"
#endif
#endif
#endif