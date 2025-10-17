
#ifndef RYNLIB_FFIMODULE_HPP
#define RYNLIB_FFIMODULE_HPP

#include "PyAllUp.hpp"
#include "FFIParameters.hpp"
#include <string>
#include <vector>
#include <stdexcept>

#ifdef _OPENMP
#include <omp.h> // comes with -fopenmp
#endif

#ifdef _TBB // Generally one _won't_ have TBB available
#include "tbb/parallel_for.h"
#include "tbb/task_arena.h"
#endif

namespace plzffi {

    using debug = mcutils::python::pyadeeb;
    using mcutils::python::py_printf;

//        template <typename >
//        typedef T (*Func)(const FFIParameters&);

   // data for an FFI method so that FFIModule gets a uniform interface

    class Arguments {
        std::vector<FFIParameters*> params;
    public:
        Arguments(std::initializer_list<FFIParameters*> pdat): params{pdat} {};
        Arguments(std::vector<FFIParameters*>& pdat): params(pdat) {};

        FFIParameters* get_params(std::string& key) {
            // printf("testing against %lu param sets...\n", params.size());
            for (auto p: params) {
                // printf("keys: %p", &p);
                // for (auto k:p.keys()) {printf("%s, ", k.c_str());};
                // printf("?\n");
                if (p->contains(key)) { return p; }
            }
            std::string msg = "key " + key + " not found";
            throw std::runtime_error(msg);
        }
        template <typename T>
        T value(std::string& key) {
            return get_params(key)->value<T>(key);
        }
        template <typename T>
        T value(const char *key) {
            std::string ks = key;
            return value<T>(ks);
        }

        std::vector<size_t> shape(std::string& key) {
            return get_params(key)->shape(key);
        }
        std::vector<size_t> shape(const char *key) {
            std::string ks = key;
            return shape(ks);
        }
    };

   auto FFIEmptyCompoundType = FFICompoundType {};
   struct FFIMethodData {
       std::string name;
       std::vector<FFIArgument> args;
       FFIType ret_type;
       FFICompoundType comp_type;
       bool vectorized;
   };
   template<typename T>
   class FFIMethod {
       FFIMethodData data;
       T (*function_pointer)(Arguments &);

   public:
       FFIMethod(
               FFIMethodData& data,
               T (*function)(Arguments &)
       ) : data(data), function_pointer(function) {};
       FFIMethod(
               std::string &method_name,
               std::vector<FFIArgument> &arg,
               const FFIType return_type,
               bool vectorized,
               T (*function)(Arguments &)
       ) : data(FFIMethodData{method_name, arg, return_type, FFIEmptyCompoundType,  vectorized}), function_pointer(function) { type_check(); };
       FFIMethod(
               const char *method_name,
               std::vector<FFIArgument> arg,
               const FFIType return_type,
               bool vectorized,
               T (*function)(Arguments &)
       ) : data(FFIMethodData{method_name, arg, return_type, FFIEmptyCompoundType,  vectorized}), function_pointer(function) { type_check(); };

       FFIMethod(
               std::string &method_name,
               std::vector<FFIArgument> &arg,
               FFICompoundType return_type,
               bool vectorized,
               T (*function)(Arguments &)
       ) : data(FFIMethodData{method_name, arg, FFIType::Compound, return_type,  vectorized}), function_pointer(function) { type_check(); };
       FFIMethod(
               const char *method_name,
               std::vector<FFIArgument> arg,
               FFICompoundType return_type,
               bool vectorized,
               T (*function)(Arguments &)
       ) : data(FFIMethodData{method_name, arg, FFIType::Compound, return_type,  vectorized}), function_pointer(function) { type_check(); };

       void type_check() {
           FFITypeHandler<T>::validate(return_type());
       }

        T call(Arguments &args) {
           if (debug::debug_print(DebugLevel::Excessive)) py_printf("  > calling function pointer on parameters...\n");
           return function_pointer(args);
       }
    //    void call(Arguments &args, T*) {
    //        if (debug::debug_print(DebugLevel::Excessive)) py_printf("  > calling function pointer on parameters...\n");
    //        T res = function_pointer(args);
    //        T[0] = res; // copy value in
    //    }
       T call(FFIParameters &params) {
           Arguments call_args {&params};
           return call(call_args);
       }

       auto method_data() const { return data; }
       auto method_name() const { return data.name; }
       auto method_arguments() const { return data.args; }
       auto return_type() const { return data.ret_type; }

       pyobj python_signature() {
           auto name = data.name;
           auto args = data.args;
           auto ret_type = data.ret_type;

           std::vector<pyobj> py_args(args.size());
           for (size_t i=0; i < args.size(); i++) {
               py_args[i] = args[i].as_tuple();
           }
           return pyobj(Py_BuildValue(
                   "(NNN)",
                   mcutils::python::as_python_object<std::string>(name),
                   mcutils::python::as_python_tuple_object<pyobj>(py_args),
                   mcutils::python::as_python_object<int>(static_cast<int>(ret_type))
                   ));
       }

   };

   enum class FFIThreadingMode {
       OpenMP,
       TBB,
       SERIAL
   };

   template<typename T, typename C> // return type and coords data type
   class FFIThreader {
       FFIMethod<T> method;
       FFIThreadingMode mode;
   public:
       FFIThreader(FFIMethod<T> &method, FFIThreadingMode mode) :
       method(method), mode(mode) {}

       FFIThreader(FFIMethod<T> &method, const std::string &mode_name) : method(method) {
           if (mode_name == "OpenMP") {
               mode = FFIThreadingMode::OpenMP;
           } else if (mode_name == "TBB") {
               mode = FFIThreadingMode::TBB;
           } else if (mode_name == "Serial") {
               mode = FFIThreadingMode::SERIAL;
           } else {
               std::string msg="FFIThreader: unknown threading method " + mode_name;
               throw std::runtime_error(msg);
           }
       }

       auto call_inner(C* coords, const std::vector<size_t>& shape, FFIParameters& params, const std::string& var, FFIParameter& new_param, size_t block_size) {
           if constexpr (std::is_same_v<T, void>) {
               switch (mode) {
                 case FFIThreadingMode::OpenMP:
                   _call_omp(coords, shape, params, new_param, var, block_size);
                   break;
                 case FFIThreadingMode::TBB:
                   _call_tbb(coords, shape, params, new_param, var, block_size);
                   break;
                 case FFIThreadingMode::SERIAL:
                   _call_serial(coords, shape, params, new_param, var, block_size);
                   break;
                 default:
                   std::string msg = "FFIThreader: unknown threading method " + std::to_string(static_cast<int>(mode));
                   throw std::runtime_error("FFIThreader: unknown threading method");
               }
           } else {
               std::vector<T> ret_data(shape[0]);  // set up values for return
               switch (mode) {
                 case FFIThreadingMode::OpenMP:
                   _call_omp(ret_data, coords, shape, params, new_param, var, block_size);
                   break;
                 case FFIThreadingMode::TBB:
                   _call_tbb(ret_data, coords, shape, params, new_param, var, block_size);
                   break;
                 case FFIThreadingMode::SERIAL:
                   _call_serial(ret_data, coords, shape, params, new_param, var, block_size);
                   break;
                 default:
                   std::string msg = "FFIThreader: unknown threading method " + std::to_string(static_cast<int>(mode));
                   throw std::runtime_error("FFIThreader: unknown threading method");
               }
               return ret_data;
           }
       }
       auto call(FFIParameters& params, const std::string& var) {
           auto threaded_param = params.get_parameter(var);
           auto coords = threaded_param.value<C*>();
           auto shape = threaded_param.shape();

           params.disable_parameter(var);

           std::vector<size_t> shp;  // Final data shape...
           // TODO: want to go to a version that can do multiple elements at once
           size_t block_size;  // params.value<size_t>('chunk_size', 1); // precompute the block size for taking chunks of data
           if (shape.size() > 1) {
               shp.resize(shape.size() - 1);
               block_size = shape[1];
               shp[0] = block_size;
               for (size_t b = 2; b < shape.size(); b++) {
                 shp[b - 1] = shape[b];
                 block_size *= shape[b];
               }
           } else {
               block_size = 1;
           }

           FFIArgument arg(var, FFITypeHandler<C>().ffi_type(), shp);
           FFIParameter new_param(arg);

           if constexpr (std::is_same_v<T, void>) {
               call_inner(coords, shape, params, var, new_param, block_size);
               params.enable_parameter(var);
           } else {
               auto res = call_inner(coords, shape, params, var, new_param, block_size);
               params.enable_parameter(var);
               return res;
           }
       }

       void _loop_inner(
           std::vector<T>& data, const size_t i,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _loop_inner(
           const size_t i,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );

       void _call_serial(
           std::vector<T>& data,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _call_serial(
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _call_omp(
           std::vector<T>& data,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _call_omp(
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _call_tbb(
           std::vector<T>& data,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
       void _call_tbb(
           C* coords, const std::vector<size_t>& shape,
           FFIParameters& params, FFIParameter& threaded_param,
           const std::string& var, const size_t block_size
       );
   };

   template <typename T, typename C>
   void FFIThreader<T, C>::_loop_inner(
           std::vector<T>& data, const size_t i,
           C* coords, [[maybe_unused]] const std::vector<size_t>& shape,
           FFIParameters &params, 
           FFIParameter& threaded_param, const std::string &var, const size_t block_size
           ) {
       FFIParameters extra;
       auto new_param = threaded_param; // copy this...?
       auto chunk = coords + (i * block_size);
       new_param.set<C*>(chunk);
       extra.set_parameter(var, new_param);
       Arguments call_args({&extra, &params});
       auto val = method.call(call_args); // done for thread safety
       data[i] = val;
   }
   template <typename T, typename C>
   void FFIThreader<T, C>::_loop_inner(
           const size_t i,
           C* coords, [[maybe_unused]] const std::vector<size_t>& shape,
           FFIParameters &params, 
           FFIParameter& threaded_param, const std::string &var, const size_t block_size
           ) {
       FFIParameters extra;
       auto new_param = threaded_param; // copy this...?
       auto chunk = coords + (i * block_size);
       new_param.set<C*>(chunk);
       extra.set_parameter(var, new_param);
       Arguments call_args({&extra, &params});
       method.call(call_args);
   }

   template <typename T, typename C>
   void FFIThreader<T, C>::_call_serial(
           std::vector<T>& data,
           C* coords, const std::vector<size_t>& shape,
           FFIParameters &params, 
           FFIParameter& threaded_param, const std::string &var, const size_t block_size
           ) {

       for (size_t w = 0; w < shape[0]; w++) {
           _loop_inner(data, w, coords, shape, params, threaded_param, var, block_size);
       }
//            py_printf(">>>> boopy %f\n", pots.vector()[0]);
   }
   template <typename T, typename C>
   void FFIThreader<T, C>::_call_serial(
           C* coords, const std::vector<size_t>& shape,
           FFIParameters &params, 
           FFIParameter& threaded_param, const std::string &var, const size_t block_size
           ) {

       for (size_t w = 0; w < shape[0]; w++) {
           _loop_inner(w, coords, shape, params, threaded_param, var, block_size);
       }
//            py_printf(">>>> boopy %f\n", pots.vector()[0]);
   }

   template<typename T, typename C>
   void FFIThreader<T, C>::_call_omp(
           [[maybe_unused]] std::vector<T> &data,
           [[maybe_unused]] C *coords, [[maybe_unused]] const std::vector<size_t> &shape,
           [[maybe_unused]] FFIParameters &params,
           [[maybe_unused]] FFIParameter& threaded_param, [[maybe_unused]] const std::string &var, [[maybe_unused]] const size_t block_size
           ) {
#ifdef _OPENMP

#pragma omp parallel for
       for (size_t w = 0; w < shape[0]; w++) {
           _loop_inner(data, w, coords, shape, params, threaded_param, var, block_size);
       }
#else
       throw std::runtime_error("OpenMP not installed");

#endif
   }
   template<typename T, typename C>
   void FFIThreader<T, C>::_call_omp(
           [[maybe_unused]] C *coords, [[maybe_unused]] const std::vector<size_t> &shape,
           [[maybe_unused]] FFIParameters &params,
           [[maybe_unused]] FFIParameter& threaded_param, [[maybe_unused]] const std::string &var, [[maybe_unused]] const size_t block_size
           ) {
#ifdef _OPENMP

#pragma omp parallel for
       for (size_t w = 0; w < shape[0]; w++) {
           _loop_inner(w, coords, shape, params, threaded_param, var, block_size);
       }
#else
       throw std::runtime_error("OpenMP not installed");

#endif
   }

   template<typename T, typename C>
   void FFIThreader<T, C>::_call_tbb(
           [[maybe_unused]] std::vector<T> &data,
           [[maybe_unused]] C *coords, [[maybe_unused]] const std::vector<size_t> &shape,
           [[maybe_unused]] FFIParameters &params,
           [[maybe_unused]] FFIParameter& threaded_param, [[maybe_unused]] const std::string &var, [[maybe_unused]] const size_t block_size
           ) {
#ifdef _TBB
       tbb::parallel_for(
               tbb::blocked_range<size_t>(0, shape[0]),
               [&](const tbb::blocked_range <size_t> &r) {
                   for (size_t w = r.begin(); w < r.end(); ++w) {
                       _loop_inner(data, w, coords, shape, params, threaded_param, var, block_size);
                   }
               }
       );
#else
       throw std::runtime_error("TBB not installed");
#endif
   }
   template<typename T, typename C>
   void FFIThreader<T, C>::_call_tbb(
           [[maybe_unused]] C *coords, [[maybe_unused]] const std::vector<size_t> &shape,
           [[maybe_unused]] FFIParameters &params,
           [[maybe_unused]] FFIParameter& threaded_param, [[maybe_unused]] const std::string &var, [[maybe_unused]] const size_t block_size
           ) {
#ifdef _TBB
       tbb::parallel_for(
               tbb::blocked_range<size_t>(0, shape[0]),
               [&](const tbb::blocked_range <size_t> &r) {
                   for (size_t w = r.begin(); w < r.end(); ++w) {
                       _loop_inner(w, coords, shape, params, threaded_param, var, block_size);
                   }
               }
       );
#else
       throw std::runtime_error("TBB not installed");
#endif
   }

   class FFIModule {
       // possibly memory leaky, but barely so & thus we won't worry too much until we _know_ it's an issue
       std::string name;
       std::string docstring;
       int size = -1;                    // size of module per interpreter...for future use
       std::string attr = "_FFIModule";  // attribute use when attaching to Python module
       std::string capsule_name;
       std::vector<void*> method_pointers;  // pointers to FFI methods, but return types are ambiguous
       // we maintain a secondary cache of this data just because it's easier
       std::vector<FFIMethodData> method_data;
       void (*loader)(FFIModule* mod);
       PyModuleDef module_def;

      public:
       FFIModule() = default;

       FFIModule(const std::string& module_name, const std::string& module_doc)
           : name(module_name),
             docstring(module_doc) { init(); }
       FFIModule(const char* module_name, const char* module_doc)
           : name(module_name),
             docstring(module_doc) { init(); }

       FFIModule(const std::string& module_name, const std::string& module_doc, void (*module_loader)(FFIModule* mod))
           : name(module_name),
             docstring(module_doc),
             loader(module_loader) { init(); }
       FFIModule(const char* module_name, const char* module_doc, void (*module_loader)(FFIModule* mod))
           : name(module_name),
             docstring(module_doc),
             loader(module_loader) { init(); }

       void init() {
           capsule_name = name + "." + attr;
       }

       PyObject* create_module() {
           if (loader == NULL) {
               std::string msg = "in loading module " + name + ": ";
               msg += "no module loader defined";
               PyErr_SetString(
                   PyExc_ImportError,
                   msg.c_str()
               );
               return NULL;
           }
           try {
               loader(this);
               get_def();
               return PyModule_Create(&module_def);
           } catch (std::exception& e) {
               std::string msg = "in loading module " + name + ": ";
               msg += e.what();
               PyErr_SetString(
                   PyExc_ImportError,
                   msg.c_str()
               );
               return NULL;
           };
       }

       template <typename T>
       void add_method(FFIMethod<T>& method) {
           //        plzffi::set_debug_print(true);
           if (debug::debug_print(DebugLevel::All)) {
               py_printf(" > adding method %s to module %s\n", method.method_data().name.c_str(), name.c_str());
           }
           method_data.push_back(method.method_data());
           method_pointers.push_back((void*)&method);
       }

       template <typename T>
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           const FFIType return_type,
           T (*function)(Arguments&)
       ) {
           // TODO: need to introduce destructor to FFIModule to clean up all of these methods once we go out of scope
           auto meth = new FFIMethod<T>(method_name, arg, return_type, false, function);
           add_method(*meth);
       }
       template <typename T>
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           T (*function)(Arguments&)
       ) {
           // need to introduce destructor to FFIModule to clean up all of these methods once we go out of scope
           auto constexpr return_type = FFITypeHandler<T>::ffi_type();
           auto meth = new FFIMethod<T>(method_name, arg, return_type, false, function);
           add_method(*meth);
       }
       template <typename T>
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           const FFIType return_type,
           std::vector<T> (*function)(Arguments&)
       ) {
           auto meth = new FFIMethod<std::vector<T>>(method_name, arg, return_type, true, function);
           add_method(*meth);
       }
       template <typename T>
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           std::vector<T> (*function)(Arguments&)
       ) {
           auto constexpr return_type = FFITypeHandler<T>::ffi_type();
           auto meth = new FFIMethod<std::vector<T>>(method_name, arg, return_type, true, function);
           add_method(*meth);
       }
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           FFICompoundType return_type,
           FFICompoundReturn (*function)(Arguments&)
       ) {
           // TODO: need to introduce destructor to FFIModule to clean up all of these methods once we go out of scope
           auto meth = new FFIMethod<FFICompoundReturn>(method_name, arg, return_type, false, function);
           add_method(*meth);
       }
       void add(
           const char* method_name,
           std::vector<FFIArgument> arg,
           FFICompoundType return_type,
           std::vector<FFICompoundReturn> (*function)(Arguments&)
       ) {
           auto meth = new FFIMethod<std::vector<FFICompoundReturn>>(method_name, arg, return_type, true, function);
           add_method(*meth);
       }

       size_t get_method_index(const std::string& method_name) {
            for (size_t i = 0; i < method_data.size(); i++) {
                if (method_data[i].name == method_name) {
                   if (debug::debug_print(DebugLevel::Excessive))
                     py_printf("  > method %s is the %lu-th method in %s\n", method_name.c_str(), i, name.c_str());
                    return i;
                }
            }
           throw std::runtime_error("method " + method_name + " not found");
       }
       template <typename T>
       FFIMethod<T> get_method(const std::string& method_name) {
            return FFIModule::get_method_from_index<T>(get_method_index(method_name));
           throw std::runtime_error("method " + method_name + " not found");
       }
       template <typename T>
       FFIMethod<T> get_method_from_index(size_t i) {
           if (debug::debug_print(DebugLevel::Excessive))
                py_printf("  > checking return type...\n");
           if constexpr (std::is_same_v<T, void>) {
                if (method_data[i].ret_type != FFIType::Void) {
                    throw std::runtime_error("void type mismatch");
                }
           } else {
                FFITypeHandler<T>::validate(method_data[i].ret_type);
           }
           if (debug::debug_print(DebugLevel::Excessive))
                py_printf("  > casting method pointer...\n");
           auto methodptr = static_cast<FFIMethod<T>*>(method_pointers[i]);
           if (methodptr == NULL) {  // is this a bad check...?
                std::string err = "Bad pointer for method '%s'" + method_data[i].name;
                throw std::runtime_error(err.c_str());
           }

           auto method = *methodptr;

           return method;
       }

       FFIMethodData get_method_data(const std::string& method_name);

       // pieces necessary to hook into the python runtime
       PyObject* get_py_name();

       PyObject* get_capsule();

       PyObject* attach(PyObject* module);
       PyObject* attach();

       const char* doc();

       void get_def();

       std::string ffi_module_attr() { return capsule_name; };

       template <typename T>
       auto call_method(const std::string& method_name, FFIParameters& params) {
           auto caller = get_method<T>(method_name);
           if (debug::debug_print(DebugLevel::Excessive))
                py_printf("  > calling method...\n");
           if constexpr (std::is_same_v<T, void>) {
               caller.call(params);
           } else {
               return caller.call(params);
           }
       }
       template <typename T, typename C>
       auto call_method_threaded(const std::string& method_name, FFIParameters& params, const std::string& threaded_var, const std::string& mode) {
           if constexpr (std::is_same_v<C, void>) {
               throw std::runtime_error("can't thread over void argument");
           } else {
               auto meth = get_method<T>(method_name);
//               py_printf("  > building threader to call method...\n");
               auto wat = FFIThreader<T, C>(meth, mode);
               if constexpr (std::is_same_v<T, void>) {
                    wat.call(params, threaded_var);
               } else {
                    return wat.call(params, threaded_var);
               }
           }
       }

    //    size_t get_method_index(std::string& method_name);

       pyobj python_signature();
       pyobj py_call_method(pyobj method_name, pyobj params);
       pyobj py_call_method_threaded(pyobj method_name, pyobj params, pyobj looped_var, pyobj threading_mode);

       static FFIModule from_capsule(PyObject* captup) {  // TODO: make this cached against the stored cap_obj...

           if (captup == NULL)
               throw std::runtime_error("NULL capsule passed to `FFIModule::from_capsule`\n");

           py_printf(DebugLevel::Excessive, "Checking capsule tuple validity...\n");

           if (!PyTuple_Check(captup)) {
               PyErr_SetString(
                   PyExc_TypeError,
                   "FFIModule spec. expected to be a tuple looking like (name, capsule)"
               );
               throw std::runtime_error("bad tuple shiz");
           }
           auto capsule_obj = pyobj(captup);

           if (debug::debug_print(DebugLevel::Excessive))
               py_printf("Got FFIModule spec \"%s\"\n", capsule_obj.repr().c_str());
           auto name_obj = capsule_obj.get_item<pyobj>(0);
           if (!name_obj.valid())
               throw std::runtime_error("bad tuple indexing");
           if (debug::debug_print(DebugLevel::All))
               py_printf("Pulling FFIModule for module \"%s\"\n", name_obj.repr().c_str());
           auto cap_obj = capsule_obj.get_item<pyobj>(1);
           if (!cap_obj.valid())
               throw std::runtime_error("bad tuple indexing");
           if (debug::debug_print(DebugLevel::Excessive))
               py_printf("  extracting from capsule \"%s\"\n", cap_obj.repr().c_str());
           std::string name = name_obj.convert<std::string>();
           std::string doc;
           FFIModule mod(name, doc);  // empty module
           if (debug::debug_print(DebugLevel::Excessive))
               py_printf("  pulling pointer with name \"%s\"\n", mod.ffi_module_attr().c_str());
           return mcutils::python::from_python_capsule<FFIModule>(cap_obj, mod.ffi_module_attr().c_str());
       }
    };

    // FFIModule ffi_from_capsule(pyobj capsule); // why am I predeclaring this...?

    struct FFIMethodCaller {
        // using map = FFITypeMap;
        // using pairs = FFITypePairs;

        template <typename D>
        static pyobj call_method(FFIModule& mod, const std::string& method_name, FFIParameters& params) {
           if (debug::debug_print(DebugLevel::Excessive)) py_printf(" > FFIModuleMethodCaller found appropriate type dispatch!\n");
           pyobj obj;
           auto mdat = mod.get_method_data(method_name); // Don't support raw pointer returns...
           if constexpr (std::is_same_v<D, void>) {
                mod.call_method<D>(method_name, params);
                return pyobj::None();
           } else {
            if (mdat.vectorized) {
                py_printf(DebugLevel::Excessive, "  > evaluating vectorized potential\n");
                auto val = mod.call_method<std::vector<D> >(method_name, params);
                //    if (debug::debug_print(DebugLevel::All)) py_printf("  > constructing python return value for typename/FFIType pair std::vector<%s>/%i\n", mcutils::type_name<D>::c_str(), T::value);
                obj = pyobj::cast<D>(std::move(val));
            } else {
                if (debug::debug_print(DebugLevel::Excessive)) py_printf("  > evaluating non-vectorized potential\n");
                D val = mod.call_method<D>(method_name, params);
                //    if (debug::debug_print(DebugLevel::All)) py_printf("  > constructing python return value for typename/FFIType pair %s/%i\n", mcutils::type_name<D>::c_str(), T::value);
                obj = pyobj::cast<D>(std::move(val));
            }
            // need to actually return the values...
            return obj;
           }
       }
        template <FFIType F>
        static pyobj call_method(FFIModule& mod, const std::string& method_name, FFIParameters& params) {
            using T = typename FFITypeMap::find_type<F>;
            return call_method<T>(mod, method_name, params);
        }
        struct call_method_caller {
            template <typename T>
            static auto call(
                [[maybe_unused]] const FFIType type, FFIModule& mod, const std::string& method_name, FFIParameters& params
                ) {
                return call_method<T>(mod, method_name, params);
            }
        };
        static auto call_method(
            const FFIType type, FFIModule& mod, const std::string& method_name, FFIParameters& params
            ) {
            return FFITypeDispatcher::dispatch<call_method_caller>::call(
                type, mod, method_name, params
            );
        }

        template <typename T, typename D>
        static auto call_threaded(
            FFIModule& mod,
            const std::string& method_name,
            const std::string& threaded_var,
            const std::string& mode,
            FFIParameters& params
        ) {
            if constexpr (std::is_same_v<D, void>) {
                // throw std::runtime_error("can't thread over void");
                return pyobj::None(); 
            } else {
                if constexpr(std::is_same_v<T, void>) {
                    mod.call_method_threaded<T, D>(method_name, params, threaded_var, mode);
                    return pyobj::None();
                } else {
                    auto val = mod.call_method_threaded<T, D>(method_name, params, threaded_var, mode);
                    return pyobj::cast<T>(std::move(val));  // we explicitly don't need this value anymore
                }
            }
        }
        template <typename T>
        struct call_threaded_thread_caller {
            template <typename D>
            static auto call(  // note the loss of type
                [[maybe_unused]] const FFIType thread_type,
                FFIModule& mod, const std::string& method_name,
                const std::string& threaded_var, const std::string& mode,
                FFIParameters& params
            ) {
                if constexpr (std::is_same_v<D, void>) {
                    throw std::runtime_error("can't thread over void");
                    return pyobj::None();
                } else {
                    return call_threaded<T, D>(mod, method_name, threaded_var, mode, params);
                }
            }
        };
       struct call_threaded_caller { // we resolve the return type first
            template <typename T>
            static auto call(
                [[maybe_unused]] const FFIType type, const FFIType thread_type,
                FFIModule& mod, const std::string& method_name, 
                const std::string& threaded_var, const std::string& mode,
                FFIParameters& params
            ) {
                return FFITypeDispatcher::dispatch<call_threaded_thread_caller<T>>::call(
                    thread_type,
                    mod, method_name, threaded_var, mode, params
                );
            }
        };
        static auto call_threaded(
            const FFIType type, const FFIType thread_type, 
            FFIModule& mod, const std::string& method_name, 
            const std::string& threaded_var, const std::string& mode,
            FFIParameters& params
        ) {
            return FFITypeDispatcher::dispatch<call_threaded_caller>::call(
                type, thread_type, mod, method_name, threaded_var, mode, params
            );
        }

    };

   //endregion

   // This used to be in FFIModule.cpp but I'm going header-only

   using mcutils::python::py_printf;

   PyObject* FFIModule::get_capsule() {
//            auto full_name = ffi_module_attr();
//            py_printf("wat %s\n", capsule_name.c_str());
       auto cap = PyCapsule_New((void *) this, capsule_name.c_str(), NULL); // do I need a destructor?
       return Py_BuildValue(
               "(OO)",
               get_py_name(),
               cap
       );
   }

   PyObject* FFIModule::get_py_name() {
       return mcutils::python::as_python_object<std::string>(name);
   }

   PyObject* FFIModule::attach(PyObject* module) {
       PyObject *capsule = get_capsule();
       if (capsule == NULL) return NULL;
       bool i_did_good = (PyModule_AddObject(module, attr.c_str(), capsule) == 0);
       if (!i_did_good) {
           Py_XDECREF(capsule);
           Py_DECREF(module);
           return NULL;
       } else {
           PyObject *pyname = get_py_name();
           i_did_good = (PyModule_AddObject(module, "name", pyname) == 0);
           if (!i_did_good) {
               Py_XDECREF(capsule);
               Py_XDECREF(pyname);
               Py_DECREF(module);
           }
       }

       return module;
   }
   PyObject* FFIModule::attach() {
       auto m = create_module();
       if (m == NULL) return m;
       return attach(m);
   }

   const char *FFIModule::doc() {
       return docstring.c_str();
   }

   PyObject *_pycall_python_signature(PyObject *self, PyObject *args);
   PyObject *_pycall_module_name(PyObject *self, PyObject *args);
   PyObject *_pycall_evaluate_method(PyObject *self, PyObject *args);
   PyObject *_pycall_evaluate_method_threaded(PyObject *self, PyObject *args);
   void FFIModule::get_def() {
       // once I have them, I should hook into python methods to return, e.g. the method names and return types
       // inside the module
       auto *methods = new PyMethodDef[5]; // I think Python manages this memory if def() only gets called once
       // but we'll need to be careful to avoid any memory leaks
       methods[0] = {"get_signature", _pycall_python_signature, METH_VARARGS, "gets the signature for an FFI module"};
       methods[1] = {"get_name", _pycall_module_name, METH_VARARGS, "gets the module name for an FFI module"};
       methods[2] = {"call_method", _pycall_evaluate_method, METH_VARARGS, "calls a method from an FFI module"};
       methods[3] = {"call_method_threaded", _pycall_evaluate_method_threaded, METH_VARARGS, "calls a method from an FFI module using a threading strategey"};
       methods[4] = {NULL, NULL, 0, NULL};
       module_def = {
               PyModuleDef_HEAD_INIT,
               name.c_str(),   /* name of module */
               doc(), /* module documentation, may be NULL */
               size,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
               methods
       };
   }

   pyobj FFIModule::python_signature() {

       std::vector<pyobj> py_sigs(method_data.size());
       for (size_t i = 0; i < method_data.size(); i++) {

           auto args = method_data[i].args;
           if (debug::debug_print(DebugLevel::Excessive)) {
               py_printf(" > constructing signature for %s\n", method_data[i].name.c_str());
           };
//                    py_printf("....wat %lu\n", args.size());
           std::vector<pyobj> subargs(args.size());
           for (size_t j = 0; j < args.size(); j++) {
               subargs[j] = args[j].as_tuple();
           }

           py_sigs[i] = pyobj(Py_BuildValue(
                   "(NNNN)",
                   mcutils::python::as_python_object<std::string>(method_data[i].name),
                   mcutils::python::as_python_tuple_object<pyobj>(subargs),
                   mcutils::python::as_python_object<FFIType>(method_data[i].ret_type), // to be python portable
                   mcutils::python::as_python_object<bool>(method_data[i].vectorized)
           ));
       }

       return pyobj(Py_BuildValue(
               "(NN)",
               mcutils::python::as_python_object<std::string>(name),
               mcutils::python::as_python_tuple_object<pyobj>(py_sigs)
       ));

   }

//    size_t FFIModule::get_method_index(std::string &method_name) {
//        for (size_t i = 0; i < method_data.size(); i++) {
//            if (method_data[i].name == method_name) { return i; }
//        }
//        throw std::runtime_error("method " + method_name + " not found");
//    }

   FFIMethodData FFIModule::get_method_data(const std::string &method_name) { //...why is this like this???
       for (auto &data : method_data) {
           if (data.name == method_name) {
//                py_printf("Method %s is the %lu-th method in %s\n", method_name.c_str(), i, name.c_str());
               return data;
           }
       }
       throw std::runtime_error("method " + method_name + " not found");
   }

   pyobj FFIModule::py_call_method(pyobj method_name, pyobj params) {

       if (debug::debug_print(DebugLevel::All)) py_printf("Calling from python into method ");
       auto mname = method_name.convert<std::string>();
       if (debug::debug_print(DebugLevel::All)) py_printf("%s\n", mname.c_str());
       auto meth_idx = get_method_index(mname);
       auto argtype = method_data[meth_idx].ret_type;

       if (debug::debug_print(DebugLevel::Excessive)) py_printf(" > loading parameters...\n");
       auto args = FFIParameters(params);

       if (debug::debug_print(DebugLevel::Excessive)) py_printf(" > calling on parameters...\n");
       return FFIMethodCaller::call_method(argtype, *this, mname, args);
   }

   pyobj FFIModule::py_call_method_threaded(
           pyobj method_name,
           pyobj params,
           pyobj looped_var,
           pyobj threading_mode
   ) {

       auto mname = method_name.convert<std::string>();
       auto meth_idx = get_method_index(mname);
       auto argtype = method_data[meth_idx].ret_type;
       auto args = FFIParameters(params);

       auto varname = looped_var.convert<std::string>();
       auto mode = threading_mode.convert<std::string>();
       auto thread_var = args.get_parameter(varname);
       auto ttype = thread_var.type();

       return FFIMethodCaller::call_threaded(
               argtype,
               ttype,
               *this,
               mname,
               varname, mode,
               args
       );

   }

   PyObject *_pycall_python_signature(PyObject *self, PyObject *args) {

       PyObject *cap;
       int debug_level;
       auto parsed = PyArg_ParseTuple(args, "Oi", &cap, &debug_level);
       if (!parsed) { return NULL; }
       debug::set_debug_level(debug_level);

       try {
           auto obj = FFIModule::from_capsule(cap);
           auto sig = obj.python_signature();
           return sig.obj();
       } catch (std::exception &e) {
           if (!PyErr_Occurred()) {
               std::string msg = "in signature call: ";
               msg += e.what();
               PyErr_SetString(
                       PyExc_SystemError,
                       msg.c_str()
               );
           }
           return NULL;
       }
   }

   PyObject *_pycall_module_name(PyObject *self, PyObject *args) {

       PyObject *cap;
       int debug_level;
       auto parsed = PyArg_ParseTuple(args, "Oi", &cap, &debug_level);
       if (!parsed) { return NULL; }
       debug::set_debug_level(debug_level);

       try {
           auto obj = FFIModule::from_capsule(cap);
           auto name = obj.get_py_name();
           return name;
       } catch (std::exception &e) {
           if (!PyErr_Occurred()) {
               std::string msg = "in module_name call: ";
               msg += e.what();
               PyErr_SetString(
                       PyExc_SystemError,
                       msg.c_str()
               );
           }
           return NULL;
       }

   }

   PyObject *_pycall_evaluate_method(PyObject *self, PyObject *args) {

       PyObject *cap, *method_name, *params;
       int debug_level;//, *looped_var, *threading_mode;
       auto parsed = PyArg_ParseTuple(args, "OOOi",
                                      &cap,
                                      &method_name,
                                      &params,
                                      &debug_level
       );
       if (!parsed) { return NULL; }

       debug::set_debug_level(debug_level);

       if (debug::debug_print(DebugLevel ::Excessive)) {
           py_printf("Calling method from python... %p, %p, %p\n", cap, method_name, params);
       }

       try {
           py_printf(DebugLevel ::Excessive, "Extracting module...\n");
           auto obj = FFIModule::from_capsule(cap);
           py_printf(DebugLevel ::Excessive, "Calling method module method...\n");
           return obj.py_call_method(pyobj(method_name), pyobj(params)).obj();
       } catch (std::exception &e) {
           if (!PyErr_Occurred()) {
               std::string msg = "in method call: ";
               msg += e.what();
               PyErr_SetString(
                       PyExc_SystemError,
                       msg.c_str()
               );
           }
           return NULL;
       }

   }

   PyObject *_pycall_evaluate_method_threaded(PyObject *self, PyObject *args) {
       PyObject *cap, *method_name, *params, *looped_var, *threading_mode;
       int debug_level;
       auto parsed = PyArg_ParseTuple(args, "OOOOOi", &cap, &method_name, &params, &looped_var, &threading_mode, &debug_level);
       if (!parsed) { return NULL; }

       debug::set_debug_level(debug_level);

       py_printf(DebugLevel ::Excessive, "Calling method from python with threading...\n");

       try {
           py_printf(DebugLevel ::Excessive, "Extracting module...\n");
           auto obj = FFIModule::from_capsule(cap);
           py_printf(DebugLevel ::Excessive, "Calling method module method...\n");
           return obj.py_call_method_threaded(
                   pyobj(method_name),
                   pyobj(params),
                   pyobj(looped_var),
                   pyobj(threading_mode)
                   ).obj();
       } catch (std::exception &e) {
           if (!PyErr_Occurred()) {
               std::string msg = "in method call: ";
               msg += e.what();
               PyErr_SetString(
                       PyExc_SystemError,
                       msg.c_str()
               );
           }
           return NULL;
       }

   }

}

#endif //RYNLIB_FFIMODULE_HPP
