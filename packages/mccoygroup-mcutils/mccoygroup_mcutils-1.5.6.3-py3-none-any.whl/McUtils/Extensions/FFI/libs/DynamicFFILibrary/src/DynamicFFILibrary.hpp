#ifndef RYNLIB_FFIDYNAMICLIBRARY_HPP
#define RYNLIB_FFIDYNAMICLIBRARY_HPP

#include "plzffi/FFIModule.hpp"
#include "ffi.h"
#include <dlfcn.h>
using libffi_type = ffi_type;

// struct CFuncPtrStub { 
//     // only taking the first few fields of a true PyObjectCFuncPtr
//     // as the ctypes.h header isn't provided by default
//     // and as long as python doesn't change it's parameter packing order
//     // this will be fine, but obviously this is playing with _maaajor_ fire
//     // and has a decent chance of just dying altogether
//     PyObject_HEAD
//     char *b_ptr;                /* pointer to memory block */
//     int  b_needsfree;           /* need _we_ free the memory? */
// };

namespace DynamicFFILibrary {
    // class FFILibraryFunction {
    //     pyobj func;
    // };
    using namespace plzffi;

    using debug = mcutils::python::pyadeeb;
    using DebugLevel = mcutils::python::DebugLevel;
    using mcutils::python::pyobj;
    using mcutils::python::py_printf;

    template <typename T>
    struct libffi_type_converter {
        // going for a compile time error here if we ask for a ::value for
        // an uninstantiated template
        // static const libffi_type& value = &L;
        static libffi_type* const value() { throw std::runtime_error("no libffi mapping for type"); }
    };
    template <> struct libffi_type_converter<void> { static libffi_type* const value() { return &ffi_type_void; } };
    template <> struct libffi_type_converter<npy_uint8> { static libffi_type* const value() { return &ffi_type_uint8; }};
    template <> struct libffi_type_converter<npy_uint16> { static libffi_type* const value() { return &ffi_type_uint16; }};
    template <> struct libffi_type_converter<npy_uint32> { static libffi_type* const value() { return &ffi_type_uint32; }};
    template <> struct libffi_type_converter<npy_uint64> { static libffi_type* const value() { return &ffi_type_uint64; }};

    template <> struct libffi_type_converter<npy_int8> { static libffi_type* const value() { return &ffi_type_sint8; }};
    template <> struct libffi_type_converter<npy_int16> { static libffi_type* const value() { return &ffi_type_sint16; }};
    template <> struct libffi_type_converter<npy_int32> { static libffi_type* const value() { return &ffi_type_sint32; }};
    template <> struct libffi_type_converter<npy_int64> { static libffi_type* const value() { return &ffi_type_sint64; }};

    // template <> struct libffi_type_converter<unsigned char> { constexpr static libffi_type* const value() { return &ffi_type_uchar;} };
    // template <> struct libffi_type_converter<unsigned short> { constexpr static libffi_type* const value() { return &ffi_type_ushort; }};
    // template <> struct libffi_type_converter<unsigned int> { constexpr static libffi_type* const value() { return &ffi_type_uint; }};
    // template <> struct libffi_type_converter<unsigned long> { constexpr static libffi_type* const value() { return &ffi_type_ulong; }};

    template <> struct libffi_type_converter<char> { static libffi_type* const value() { return &ffi_type_schar; }};
    // template <> struct libffi_type_converter<short> { constexpr static libffi_type* const value() { return &ffi_type_sshort; }};
    // template <> struct libffi_type_converter<int> { constexpr static libffi_type* const value() { return &ffi_type_sint; }};
    // template <> struct libffi_type_converter<long> { constexpr static libffi_type* const value() { return &ffi_type_slong; }};

    template <> struct libffi_type_converter<float> { static libffi_type* const value() { return &ffi_type_float; }};
    template <> struct libffi_type_converter<double> { static libffi_type* const value() { return &ffi_type_double; }};
    template <> struct libffi_type_converter<long double> { static libffi_type* const value() { return &ffi_type_longdouble; }};

    // // I need to add some "size_of" checks here to make sure this compiled right...;_; or just define the numpy types and hope for the best?
    // template <> struct libffi_type_converter<unsigned long long> { constexpr static libffi_type* const value() { return &ffi_type_uint64; }};
    // template <> struct libffi_type_converter<long long> { constexpr static libffi_type* const value() { return &ffi_type_sint64; }};

    template <> struct libffi_type_converter<bool> { static libffi_type* const value() { return &ffi_type_uint8; }}; // ??

    template <typename T> struct libffi_type_converter<T*> { static libffi_type* const value() { return &ffi_type_pointer; }};
    template <> struct libffi_type_converter<std::string> { static libffi_type* const value() { return &ffi_type_pointer; }}; // pointer to c_str()


    // FFITypePair<FFIType::PyObject, pyobj>
    //         ,FFITypePair<FFIType::LongLong, long long>
    //         ,FFITypePair<FFIType::UnsignedLongLong, unsigned long long>
    //         ,FFITypePair<FFIType::PySizeT, Py_ssize_t>
    //         ,FFITypePair<FFIType::Float, float>
    //         ,FFITypePair<FFIType::Double, double>
    //         ,FFITypePair<FFIType::Bool, bool>
    //         ,FFITypePair<FFIType::String, std::string>
    //         ,FFITypePair<FFIType::Compound, FFICompoundReturn >
    //         ,FFITypePair<FFIType::NUMPY_Bool, npy_bool>
    //         ,FFITypePair<FFIType::NUMPY_Int8, npy_int8>
    //         ,FFITypePair<FFIType::NUMPY_Int16, npy_int16>
    //         ,FFITypePair<FFIType::NUMPY_Int32, npy_int32>
    //         ,FFITypePair<FFIType::NUMPY_Int64, npy_int64>
    //         ,FFITypePair<FFIType::NUMPY_UnsignedInt8, npy_uint8>
    //         ,FFITypePair<FFIType::NUMPY_UnsignedInt16, npy_uint16>
    //         ,FFITypePair<FFIType::NUMPY_UnsignedInt32, npy_uint32>
    //         ,FFITypePair<FFIType::NUMPY_UnsignedInt64, npy_uint64>
    //         ,FFITypePair<FFIType::NUMPY_Float16, npy_float16>
    //         ,FFITypePair<FFIType::NUMPY_Float32, npy_float32>
    //         ,FFITypePair<FFIType::NUMPY_Float64, npy_float64>
    //         ,FFITypePair<FFIType::NUMPY_Float128, npy_float128>
    

    struct libffi_type_converter_caller {
        template <typename T>
        static auto call(const FFIType type) { return libffi_type_converter<T>::value(); }
    };
    auto libffi_type_convert(const FFIType type) {
        return FFITypeDispatcher::dispatch<libffi_type_converter_caller>::call(type);
    }

    struct libffi_type_byte_size_caller {
        template <typename T>
        static auto call(const FFIType type, const std::vector<size_t>& shape, const FFIContainerType ctype) {
            if (ffiobj::is_array_type(type, shape, ctype)) {
                return sizeof(T*);
            } else if constexpr(std::is_same_v<T, void>) {
                throw std::runtime_error("no byte size for void type");
            } else {
                return sizeof(T); 
            }
        }
    };
    auto libffi_type_byte_size(const FFIType type, const std::vector<size_t>& shape, const FFIContainerType ctype) {
        return FFITypeDispatcher::dispatch<libffi_type_byte_size_caller>::call(type, shape, ctype);
    }

    struct ffi_arg_ptr {
        void* ptr;
        bool is_ptr; // means we need to take another address when constructing the final call stack

        ~ffi_arg_ptr() { // don't free data held by ptr (that's the job of the passing code)

        }
    };
    template <typename T>
    ffi_arg_ptr libffi_convert(T& val) {
        if constexpr(std::is_pointer_v<T>) {
            return ffi_arg_ptr{(void*)val, true};
        } else {
            return ffi_arg_ptr{(void*)&val, false};
        }
    }
    template <>
    ffi_arg_ptr libffi_convert<std::string>(std::string& val) {
        auto char_buf = val.c_str();
        return libffi_convert<const char*>(char_buf);
    }

    struct libffi_convert_caller {
        template <typename T>
        static auto call(const FFIType type, FFIParameters& params, const std::string& name, const std::vector<size_t>& shape, const FFIContainerType ctype) {
            if (ffiobj::is_array_type(type, shape, ctype)) {
                auto val = params.value<T*>(name);  // always store a pointer to the underlying data ... except when we don't want to ...
                auto ptr = libffi_convert(val);
                // if constexpr (std::is_same_v<T, int>) {
                //   printf("w1...\n");
                //   printf("w1at %p -> %d\n", ptr.ptr, *(int*)ptr.ptr);
                // }
                return ptr;
            } else {
                if constexpr (std::is_same_v<T, void>) {
                  throw std::runtime_error("can't convert param to void");
                } else {
                  auto val = params.value<T*>(name);  // always store a pointer to the underlying data so it doesn't go out of scope...
                  auto ptr = libffi_convert(*val); // just returns out pointer back to us
                //   auto val = params.value<T>(name);
                //   auto ptr = libffi_convert(val);
                //   if constexpr (std::is_same_v<T, int>) {
                //     printf("urgh %p -> %p -> %d -> %d\n", ptr.ptr, (int*)ptr.ptr, *(int*)ptr.ptr, *val);
                //   }
                  return ptr;
                }
            }
        }
    };
    auto libffi_convert(const FFIType type, FFIParameters& params, const std::string& name, const std::vector<size_t>& shape, const FFIContainerType ctype) {
        // auto shape = params.shape(name);
        auto ptr = FFITypeDispatcher::dispatch<libffi_convert_caller>::call(
            type, params, name, shape, ctype
        );

        // if (type==FFIType::Int && ctype==FFIContainerType::Raw) {
        //     printf("w...\n");
        //     printf("wat %p -> %d\n", ptr.ptr, *(int*)ptr.ptr);
        // }
        return ptr;
        
    }

    using ffi_ptr = void(*)(void);
    // ffi_ptr extract_func(pyobj ctypes_func) {
    //     if (debug::debug_print(DebugLevel::Excessive))
    //         py_printf("  extracting void function from %s...\n", ctypes_func.repr().c_str());
    //     auto cfptr = (CFuncPtrStub*) ctypes_func.obj();
    //     return (ffi_ptr)cfptr->b_ptr; // mimicking ctypes.h?
    // }

    class LibFFIMethod {
        ffi_ptr func;
        FFIType rtype;
        std::vector<FFIArgument> args;
        bool vectorized;
        std::vector<libffi_type*> types;
        ffi_cif cif;
        bool initialized = false;
    public:
        LibFFIMethod(ffi_ptr f,  const FFIType res_type, std::vector<FFIArgument>& arg_list, bool is_vectorized) :
            func(f), rtype(res_type), args(arg_list), vectorized(is_vectorized) {};
        // LibFFIMethod(pyobj& ctypes_func, const FFIType res_type, std::vector<FFIArgument>& arg_list, bool is_vectorized) :
        //     func(extract_func(ctypes_func)), rtype(res_type), args(arg_list), vectorized(is_vectorized) {};
        static LibFFIMethod from_python(pyobj fdata) {

            auto lib = fdata.getattr<pyobj>("library");
            auto handle_obj = lib.getattr<pyobj>("_handle");
            // handle.apply_check(PyLong_Check);
            auto lib_handle = handle_obj.as_void_ptr();
            auto name = fdata.getattr<std::string>("name");
            auto func = (ffi_ptr) dlsym(lib_handle, name.c_str()); // this will need to be made platform independent...
            if (func == NULL) {
                std::string msg = "no symbol " + name;
                throw std::runtime_error(msg);
            }
            auto rtype = fdata.getattr<FFIType>("return_type");
            auto args = fdata.getattr<std::vector<FFIArgument>>("args");
            auto vectorized = fdata.getattr<bool>("vectorized");

            if (debug::debug_print(DebugLevel::Excessive)) {
                if (vectorized) {
                    py_printf("Initializing LibFFIMethod<vec<FFIType(%d)>>(", static_cast<int>(rtype));
                } else {
                    py_printf("Initializing LibFFIMethod<FFIType(%d)>(", static_cast<int>(rtype));
                }
                for (auto &a: args) { py_printf("%s<FFIType(%d)>, ", a.name().c_str(), static_cast<int>(a.type())); };
                py_printf(")\n");
            };

            return {func, rtype, args, vectorized};
        }

        auto return_type() const {return rtype;}
        auto arguments() const {return args;}
        auto is_vectorized() const {return vectorized;}
        auto function() const {return func;}
        auto call_interface() {return &cif;}

        static std::vector<libffi_type*>  get_libffi_types(const std::vector<FFIArgument>& arg_list) {
            std::vector<libffi_type*> types(arg_list.size());
            size_t i = 0;
            for (const auto &a : arg_list) {
                auto type = a.type();
                auto shape = a.shape();
                auto ctype = a.container_type();
                if (ffiobj::is_array_type(type, shape, ctype)) {
                    types[i] = &ffi_type_pointer;
                } else {
                    types[i] = libffi_type_convert(type);
                }
                i++;
            }
            return types;
        }

        static std::vector<ffi_arg_ptr> get_libffi_vals(FFIParameters& params, const std::vector<FFIArgument>& arg_list) {
            std::vector<ffi_arg_ptr> values(arg_list.size());
            size_t i = 0;
            for (auto &a : arg_list) {
                auto name = a.name(); // need const reference
                auto type = a.type();
                auto shape = a.shape();
                auto ctype = a.container_type();
                auto ptr = libffi_convert(type, params, name, shape, ctype);
                values[i] = ptr;
                // if (type==FFIType::Int && ctype==FFIContainerType::Raw) {
                //     printf("w2...\n");
                //     printf("w2at %p -> %d\n", ptr.ptr, *(int*)ptr.ptr);
                // }
                i++;
            }
            return values;
        }

        template <typename restype>
        bool initialize_cif() { // I should really be checking if the rtype has changed...
                types = get_libffi_types(args);  // this keeps the types alive
                initialized = ffi_prep_cif(&cif, FFI_DEFAULT_ABI, types.size(), libffi_type_converter<restype>::value(), types.data()) == FFI_OK;
                return initialized;
        }
        template <typename restype>
        void init() {
            if (!initialized) {
                initialize_cif<restype>();
                if (!initialized)
                    throw std::runtime_error("failed to initialize CIF");
            }
        }
        void call_buffer(void* res, void** buf) {
            ffi_call(&cif, func, res, buf);
        }
        template <typename restype>
        pyobj call(std::vector<ffi_arg_ptr>& values) {
            init<restype>();

            std::vector<void*> buf(values.size());
            for (size_t i=0; i<values.size(); i++) {
                if (values[i].is_ptr) {
                    buf[i] = &values[i].ptr;
                } else {
                    // if constexpr (std::is_same_v<T, int>) {
                    // printf("urgh2 %p -> %p -> %d\n", values[i].ptr, (int*)values[i].ptr, *(int*)values[i].ptr);
                    // }
                    buf[i] = values[i].ptr;
                }
            }
            if constexpr (std::is_same_v<restype, void>) {
                    
                    if (debug::debug_print(DebugLevel::Excessive)) {
                        py_printf("  calling void function with values from %p...\n", buf.data());
                    }

                long double res;
                call_buffer(&res, buf.data());
                return pyobj::None();
            } else {
                if (vectorized) {  // not sure if this even makes sense to be honest...
                    if (debug::debug_print(DebugLevel::Excessive)) py_printf("  wtf why are we here???\n");

                    std::vector<restype> res;
                    call_buffer(&res, buf.data());
                    return pyobj::cast<restype>(std::move(res));
                } else {
                    
                    if (debug::debug_print(DebugLevel::Excessive)) {
                        py_printf("  calling %s function with values from %p...\n", mcutils::type_name<restype>::c_str(), buf.data());
                    }
                    
                    restype res;
                    call_buffer(&res, buf.data());
                    // return pyobj::None();
                    return pyobj::cast<restype>(std::move(res));
                }
            }
        }
        template <typename restype>
        pyobj call(FFIParameters& params) {
            if (debug::debug_print(DebugLevel::All)) py_printf("Calling FFI method...\n");
            if (debug::debug_print(DebugLevel::Excessive)) py_printf("  extracting FFI values...\n");
            auto values = get_libffi_vals(params, args);
            return call<restype>(values);
        }

    };

    struct LibFFIMethodCaller {

        // static std::vector<libffi_type*> get_libffi_types(FFIParameters& params);
        // static std::vector<void*> get_libffi_vals(FFIParameters& params);

        template <typename rtype>
        static pyobj call_method(LibFFIMethod& func, FFIParameters& params) {
            return func.call<rtype>(params);
        }
        template <FFIType F>
        static auto call_method(LibFFIMethod& func, FFIParameters& params) {
            using T = typename FFITypeMap::find_type<F>;
            return call_method<T>(func, params);
        }
        struct call_method_caller {
            template <typename T>
            static auto call(
                [[maybe_unused]] const FFIType type, LibFFIMethod& func, FFIParameters& params
                ) {
                return call_method<T>(func, params);
            }
        };
        static auto call_method(
            LibFFIMethod& func, FFIParameters& params
            ) {
            return FFITypeDispatcher::dispatch<call_method_caller>::call(
                func.return_type(), func, params
            );
        }

    };


    struct LibFFIThreadedCaller {

       static FFIThreadingMode get_mode(const std::string &mode_name) {
           if (mode_name == "OpenMP") {
               return FFIThreadingMode::OpenMP;
           } else if (mode_name == "TBB") {
               return FFIThreadingMode::TBB;
           } else if (mode_name == "Serial") {
               return FFIThreadingMode::SERIAL;
           } else {
               std::string msg="FFIThreader: unknown threading method " + mode_name;
               throw std::runtime_error(msg);
           }
       }
       
       template <typename restype>
       static void _call_serial(
           restype* res_buffer,
           ffi_ptr func, ffi_cif* cif,
           std::vector<ffi_arg_ptr>& values,
           size_t nels,
           std::vector<size_t>& thread_inds,
           std::vector<size_t>& block_byte_offsets_sizes
       );
       template <typename restype>
       static void _call_omp(
           restype* res_buffer,
           ffi_ptr func, ffi_cif* cif,
           std::vector<ffi_arg_ptr>& values,
           size_t nels,
           std::vector<size_t>& thread_inds,
           std::vector<size_t>& block_byte_offsets_sizes
       );
       template <typename restype>
       static void _call_tbb(
           restype* res_buffer,
           ffi_ptr func, ffi_cif* cif,
           std::vector<ffi_arg_ptr>& values,
           size_t nels,
           std::vector<size_t>& thread_inds,
           std::vector<size_t>& block_byte_offsets_sizes
       );

       template <typename rt>
       struct _rbuf_type {using type=rt;};
       template <>
       struct _rbuf_type<void> {using type=char;};
       template <typename restype>
       static pyobj call_threaded_dispatcher(
           FFIThreadingMode mode,
           LibFFIMethod& method, std::vector<ffi_arg_ptr>& values,
           size_t nels,
           std::vector<size_t>& thread_inds,
           std::vector<size_t>& block_byte_offsets_sizes
       ) {
            using T = typename _rbuf_type<restype>::type;
            auto ret_data = new T[nels];  // set up values for return
            switch (mode) {
                case FFIThreadingMode::OpenMP:
                _call_omp<restype>((restype*)ret_data, method.function(), method.call_interface(), values, nels, thread_inds, block_byte_offsets_sizes);
                break;
                case FFIThreadingMode::TBB:
                _call_tbb<restype>((restype*)ret_data, method.function(), method.call_interface(), values, nels, thread_inds, block_byte_offsets_sizes);
                break;
                case FFIThreadingMode::SERIAL:
                _call_serial<restype>((restype*)ret_data, method.function(), method.call_interface(), values, nels, thread_inds, block_byte_offsets_sizes);
                break;
                default:
                std::string msg = "FFIThreader: unknown threading method " + std::to_string(static_cast<int>(mode));
                throw std::runtime_error("FFIThreader: unknown threading method");
            }
            if constexpr(std::is_same_v<restype, void>) {
                delete[] ret_data;
                return pyobj::None();
            } else {
                std::vector<size_t> shp {nels};
                return mcutils::python::numpy_from_data<restype>((restype*)ret_data, shp, false); // no need to copy --> numpy can manage the memory now
            }
       }

        template <typename restype>
        static void call_threaded_inner(
            size_t idx,
            restype* res_buffer,
            // LibFFIMethod& method,
            ffi_ptr func, ffi_cif* cif,
            std::vector<ffi_arg_ptr>& values,
            std::vector<size_t>& thread_inds,
            std::vector<size_t>& block_byte_offsets_sizes
        ) {
            std::vector<void*> buf(values.size());
            std::vector<char*> tmp(values.size());
//            void* buf[values.size()];
//            char* tmp[values.size()]; // allocate space for temporary storage of offset pointers
            for (size_t i = 0; i < values.size(); i++) {  // initial pass
                if (values[i].is_ptr) {
                buf[i] = &values[i].ptr;
                } else {
                buf[i] = values[i].ptr;
                }
            }
            for (size_t j = 0; j < thread_inds.size(); j++) {  // cleanup pass
                auto i = thread_inds[j];
                auto offset = block_byte_offsets_sizes[j];
                if (values[j].is_ptr) {
                    tmp[i] = *(char**)buf[i];
                    tmp[i] += offset * idx;
                    // printf("%lu, %lu: ptr %p offset %lu\n", idx, i, buf[i], offset * idx);
                    // buf[i] = (char*)buf[i] + offset * idx; // read as a char ptr just so we can apply the offset...
                    // buf[i] += offset * idx;  // increment by appropriate amount
                    // printf("%lu: new ptr(%lu): %p\n", idx, i, base);
                    buf[i] = (void*)&(tmp[i]);
                    // printf("%lu: new new ptr(%lu): %p\n", idx, i, *(char**)buf[i]);
                } else {
                    throw std::runtime_error("can't thread over non-pointer argument");
                }
            }
            if constexpr (std::is_same_v<restype, void>) {
                // long double res; // should I protect users against a mis-specified return type??? ... nah not yet
                // we make a new one every time since we can't do pointer arithmetic with void easily
                // and we should never depend on the void result
                if (debug::debug_print(DebugLevel::Excessive)) {
                    py_printf("  calling void function(%p & cif %p) with values from %p...\n", func, cif, buf.data());
                }
                ffi_call(cif, func, NULL, buf.data());
            } else {
                long double res;
                if (debug::debug_print(DebugLevel::Excessive))
                py_printf("  calling %s function with values from %p to populate %p...\n", mcutils::type_name<restype>::c_str(), buf.data(), res_buffer + idx);
                ffi_call(cif, func, &res, buf.data());
            }
        }

        static size_t prep_block_data(
            std::vector<size_t>& thread_inds,
            std::vector<size_t>& block_byte_offsets_sizes,
            FFIParameters& params, const std::vector<FFIArgument>& args,
            const std::vector<std::string>& threaded_vars
        ) {
            size_t nels;
            size_t i = 0;
            for (auto& key : threaded_vars) {
                size_t idx = 0;
                for (auto& a : args) {
                    if (a.name() == key) { break; }
                    idx++;
                }
                if (idx == args.size()) {
                    throw std::runtime_error("bad threading variable");
                }
                thread_inds[i] = idx;

                auto shape = params.shape(key);
                auto type = params.typecode(key);
                auto ctype = params.container_type(key);
                size_t block_size;  // params.value<size_t>('chunk_size', 1); // precompute the block size for taking chunks of data
                nels = shape[0];
                if (shape.size() > 1) {
                    block_size = shape[1];
                    for (size_t b = 2; b < shape.size(); b++) { block_size *= shape[b]; }
                } else {
                    block_size = 1;
                }
                block_size *= libffi_type_byte_size(type, shape, ctype);  // scale by number of bytes in the type...
                block_byte_offsets_sizes[i] = block_size;

                i++;
            }
            return nels;
        }

        template <typename restype>
        static auto prep_and_call(
            FFIThreadingMode mode,
            LibFFIMethod& method,
            FFIParameters& params,
            const std::vector<std::string>& threaded_vars
        ) {
            method.init<restype>();

            auto args = method.arguments();
            auto values = LibFFIMethod::get_libffi_vals(params, args);
            std::vector<size_t> thread_inds(threaded_vars.size());
            std::vector<size_t> block_byte_offsets_sizes(threaded_vars.size());
            auto nels = prep_block_data(thread_inds, block_byte_offsets_sizes, params, args, threaded_vars);

            return call_threaded_dispatcher<restype>(
                mode, method, values,
                nels, thread_inds, block_byte_offsets_sizes
            );
        }

        struct prep_and_call_caller {
            template <typename restype>
            static auto call(
                [[maybe_unused]] const FFIType type,
                FFIThreadingMode mode,
                LibFFIMethod& method,
                FFIParameters& params,
                const std::vector<std::string>& threaded_vars
            ) {
                return prep_and_call<restype>(mode, method, params, threaded_vars);
            }
        };

        static auto call_threaded(
            LibFFIMethod& method,
            FFIThreadingMode mode,
            FFIParameters& params,
            const std::vector<std::string>& threaded_vars
        ) {
            return FFITypeDispatcher::dispatch<prep_and_call_caller>::call(method.return_type(), mode, method, params, threaded_vars);
        }
    };

    template <typename restype>
    void LibFFIThreadedCaller::_call_serial(
            restype* res_buffer,
            // LibFFIMethod& method, 
            ffi_ptr func, ffi_cif* cif,
            std::vector<ffi_arg_ptr>& values,
            size_t nels,
            std::vector<size_t>& thread_inds,
            std::vector<size_t>& block_byte_offsets_sizes
        ) {

        for (size_t w = 0; w < nels; w++) {
            // py_printf("...%lu\n", w);
            call_threaded_inner(w, res_buffer, func, cif, values, thread_inds, block_byte_offsets_sizes);
        }
    //            py_printf(">>>> boopy %f\n", pots.vector()[0]);
    }

   template<typename restype>
   void LibFFIThreadedCaller::_call_omp(
           [[maybe_unused]] restype* res_buffer,
        //    [[maybe_unused]] LibFFIMethod& method, 
           [[maybe_unused]] ffi_ptr func, [[maybe_unused]] ffi_cif* cif,
           [[maybe_unused]] std::vector<ffi_arg_ptr>& values,
           [[maybe_unused]] size_t nels,
           [[maybe_unused]] std::vector<size_t>& thread_inds,
           [[maybe_unused]] std::vector<size_t>& block_byte_offsets_sizes
           ) {
#ifdef _OPENMP

#pragma omp parallel for
       for (size_t w = 0; w < nels; w++) {
            // py_printf("...%lu\n", w);
            call_threaded_inner(w, res_buffer, func, cif, values, thread_inds, block_byte_offsets_sizes);
       }
#else
       throw std::runtime_error("OpenMP not installed");

#endif
   }

   template<typename restype>
   void LibFFIThreadedCaller::_call_tbb(
           [[maybe_unused]] restype* res_buffer,
        //    [[maybe_unused]] LibFFIMethod& method, 
           [[maybe_unused]] ffi_ptr func, [[maybe_unused]] ffi_cif* cif,
           [[maybe_unused]] std::vector<ffi_arg_ptr>& values,
           [[maybe_unused]] size_t nels,
           [[maybe_unused]] std::vector<size_t>& thread_inds,
           [[maybe_unused]] std::vector<size_t>& block_byte_offsets_sizes
           ) {
#ifdef _TBB
       tbb::parallel_for(
               tbb::blocked_range<size_t>(0, nels),
               [&](const tbb::blocked_range <size_t> &r) {
                   for (size_t w = r.begin(); w < r.end(); ++w) {
                    call_threaded_inner(w, res_buffer, func, cif, values, thread_inds, block_byte_offsets_sizes);
                   }
               }
       );
#else
       throw std::runtime_error("TBB not installed");
#endif
   }

    pyobj call_ffi_func(Arguments &base_params) {
        // I could probably link this in better but this is fine as 
        // a stub to demo how these modules work
        auto fdat = base_params.value<pyobj>("function_data");
        auto method = LibFFIMethod::from_python(fdat);
        auto params = FFIParameters(base_params.value<pyobj>("parameters"));
        return LibFFIMethodCaller::call_method(method, params);
    }

    pyobj call_ffi_func_threaded(Arguments &base_params) {
        // I could probably link this in better but this is fine as 
        // a stub to demo how these modules work
        auto fdat = base_params.value<pyobj>("function_data");
        auto method = LibFFIMethod::from_python(fdat);
        auto pobj = base_params.value<pyobj>("parameters");
        auto params = FFIParameters(pobj);
        auto threaded_vars_obj = base_params.value<pyobj>("threading_vars");
        auto threaded_vars = threaded_vars_obj.convert<std::vector<std::string>>();
        auto mode_str = base_params.value<std::string>("threading_mode");
        auto mode = LibFFIThreadedCaller::get_mode(mode_str);
        return LibFFIThreadedCaller::call_threaded(method, mode, params, threaded_vars);
    }

        // need a load function that can be called in PYMODINIT
    void load(FFIModule *mod) {

        // add data for vectorized version
        mod->add<pyobj>(
                "call_libffi",
                {
                        {"function_data", FFIType::PyObject, {}},
                        {"parameters", FFIType::PyObject, {}},
                },
                call_ffi_func
        );

        mod->add<pyobj>(
                "call_libffi_threaded",
                {
                        {"function_data", FFIType::PyObject, {}},
                        {"parameters", FFIType::PyObject, {}},
                        {"threading_vars", FFIType::PyObject, {0}},
                        {"threading_mode", FFIType::String, {}}
                },
                call_ffi_func_threaded
        );

        // // add data for threaded version
        // mod->add<pyobj>(
        //         "call_threaded",
        //         {
        //                 {"function_data", FFIType::PyObject, {}},
        //                 {"parameters", FFIType::PyObject, {}},
        //         },
        //         call_ffi_func_threaded
        // );

    };

    static FFIModule Data(
        "DynamicFFILibrary",
        "provides dynamic library linkage for plzffi",
        load
        );
}

extern "C" {
//    void print_hi() { printf("hi\n"); }
//    void print_int(int i) { printf("--> %d\n", i+1);  }
//    int print_ret_int(int i) { printf("--> %d\n", i+1); return i; }
//    int print_int_ptr(int* i) {
//        printf("....?\n");
//        printf("ip> %p\n", i);
//        printf("ii> %d\n", *i);
//        return *i;
//    }
//    // void print_int_ptr(int* i) {
//    //     printf("....?\n");
//    //     printf("ip> %p\n", i);
//    //     printf("ii> %d\n", *i);
//    // }
//    void print_int_crd(int* i, double* coords) { printf("ic> %d %f\n", *i, coords[0]); }
//    void print_ij(int64_t* i, int64_t* j) {
//        printf("ij> %lld %lld\n", *i, *j);
//        printf("ip> %p %p\n", i, j);
//        // printf("ip1> %p %p\n", i + 1, j + 1);
//        // printf("ij1> %lld %lld\n", *(i + 1), *(j + 1));
//    }
//
//    double print_coords(int* nwaters, double* energy, double* coords) {
//         printf("ic> %d %f\n", *nwaters, *energy);
//         printf("crds(");
//         for (size_t i=0; i<9; i++) {
//             printf("%f, ", coords[i]);
//         }
//         printf(")\n");
//        //  energy = &20.0;
//         return *energy;
//         }
}

PyMODINIT_FUNC PyInit_DynamicFFILibrary(void) {
    return DynamicFFILibrary::Data.attach();
}

#endif