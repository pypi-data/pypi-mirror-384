
#ifndef RYNLIB_PYALLUP_HPP
#define RYNLIB_PYALLUP_HPP

#include "Python.h"

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "numpy/ndarrayobject.h"
#include <vector>
#include <numeric>
#include <string>
#include <stdexcept>


// Stack Overflow helper for demangling...
#ifdef __GNUG__
#include <cstdlib>
#include <memory>
#include <cxxabi.h>

namespace mcutils {
    std::string demangle(const char *name) {

        int status = -4; // some arbitrary value to eliminate the compiler warning
        std::unique_ptr<char, void (*)(void *)> res{
                abi::__cxa_demangle(name, NULL, NULL, &status),
                std::free
        };

        return (status == 0) ? res.get() : name;
    }

    template <typename T>
    struct type_name {
        static std::string value;
        static const char* raw_name;
        static const char* c_str() {
            return value.c_str();
        }
    };
    template <typename T>
    auto type_name<T>::value = demangle(typeid(T).name());
    template <typename T>
    auto type_name<T>::raw_name = typeid(T).name();

}

#else

namespace mcutils {
// does nothing if not g++
    std::string demangle(const char* name) {
        return name;
    }

    template <typename T>
    std::string type_name() {
        return demangle(typeid(T).name());
    }

}


#endif

namespace mcutils {
    namespace python {

        enum DebugLevel {
            Quiet = 0,
            Normal = 5,
            More = 10,
            All = 50,
            Excessive = 100 // For every last little bit of info about the execution of the program
        };

        class PyallupDebugFuckery {
        public:
            static int debug_level;
#ifdef _NODEBUG
            static bool debug_print(int level) {
                return false;
            }
#else
            static bool debug_print(int level) {
                return level <= debug_level;
            }
#endif
            static bool debug_print() {
                return debug_print(DebugLevel::Normal);
            }
            static void set_debug_level(int level) {
                debug_level = level;
            }
        };

        using pyadeeb = PyallupDebugFuckery;
        auto pyadeeb::debug_level = static_cast<int>(DebugLevel::Quiet);
#ifdef _NODEBUG
        void py_printf(const char* fmt, ...) {}
        void py_printf(int debug_level, const char* fmt) {}
#else
        void py_printf(const char* fmt, ...) {
            va_list args;
            va_start(args, fmt);
//            printf("PRINTING: ");
            auto print_err = vprintf(fmt, args);
            va_end(args);
            if (print_err <= 0) {
                std::string msg = "printf shat the bed with ferror = " + std::to_string(print_err);
                PyErr_SetString(
                        PyExc_SystemError,
                        msg.c_str()
                        );
                throw std::runtime_error(msg);
            }
        }
        void py_printf(int debug_level, const char* fmt) {
            if (pyadeeb::debug_print(debug_level)) {
                py_printf(fmt);
            }
        }
#endif

        std::string get_python_repr(PyObject* obj);

        std::string python_type_name(PyTypeObject* type);

        /*
         * PyObject* interface type to keep the raw pointers safe
         *
         *
         */
        class pyiter;

        class pyobj {
            std::shared_ptr<PyObject> ptr;
            bool stolen = false;
        public:
            pyobj() : ptr(NULL) {}
            explicit pyobj(PyObject* py_obj, bool new_ref = false) :
                ptr(
                        std::shared_ptr<PyObject>(
                                py_obj,
                                [](PyObject* ref){
                                    if (ref != NULL && pyadeeb::debug_print(DebugLevel::Excessive) && ref->ob_refcnt == 1) {
                                        py_printf("     --->  freeing shared_ptr to object of type %s at %p\n", ref->ob_type->tp_name, ref);
                                    }
                                    // Py_XDECREF(ref);
                                }
                                )
                        ),
                stolen(new_ref) {
                if (!stolen) {
                    Py_XINCREF(ptr.get());
                };
            }
            pyobj(const pyobj& other) : ptr(other.ptr), stolen(other.stolen) {
                // we assume the other object managed this
//                Py_XINCREF(ptr.get());
            }
            pyobj& operator=(const pyobj& other) {
                    if ( &other != this )
                    {
                        this->ptr = other.ptr;
                        this->stolen = other.stolen; // don't want to steal twice
                    }
                    return *this;
            }
            ~pyobj() {
                if (valid() && pyadeeb::debug_print(DebugLevel::Excessive) && refcnt() == 1) {
                    py_printf("     -->  deleting object of type %s at %p\n", type_name().c_str(), obj(), refcnt());
                }
//                Py_XDECREF(ptr); // handled by the shared ptr now
            }

            static PyObject* new_NONE() { Py_RETURN_NONE; }
            static pyobj None() { return pyobj(new_NONE()); }
            static PyObject* new_TRUE() { Py_RETURN_TRUE; }
            static pyobj True() { return pyobj(new_TRUE()); }
            static PyObject* new_FALSE() { Py_RETURN_FALSE; }
            static pyobj False() { return pyobj(new_FALSE()); }

            std::string type_name() {
                return python_type_name(obj()->ob_type);
            }

            // bool apply_check(bool(*checker)(PyObject*), bool raise=false, const std::string& err="PyObject check failed") {
            //     auto res = checker(obj());
            //     if (raise && !res) {
            //         throw std::runtime_error(err);
            //     }
            //     return res;
            // }
            void* as_void_ptr() {
                if (!PyLong_Check(obj())) {
                    std::string msg = "object " + repr() + " is not an address to memory";
                    // apply_check(PyLong_Check, true, msg);
                    throw std::runtime_error(msg);
                }
                return (void *)PyLong_AsVoidPtr(obj());
            }

            PyObject* obj() const {return ptr.get();}

            bool operator==(const pyobj &other) {return obj() == other.ptr.get();}
            bool operator!=(const pyobj &other) {return obj() != other.ptr.get();}

            void incref() {Py_XINCREF(obj());}
            void decref() { // don't let PyObject* ref count get to 0 while pyobj still alive
                auto p = ptr.get();
                if (p!=NULL && p->ob_refcnt > 1) {
                    // Py_XDECREF(ptr.get());
                }
            }
            void steal() { // mark as stolen ref so refcount can drop when necessary
                if (!stolen) {
                    decref();
                    stolen = true;
                }
            }
            Py_ssize_t refcnt() { return obj()->ob_refcnt; }
            bool valid() {return obj() != NULL;}
            std::string repr() { return get_python_repr(obj()); }

            template<typename T>
            T convert() const;
            template <typename T>
            static pyobj cast(T val, bool is_new);
            template <typename T>
            static pyobj cast(T val);
            template <typename T>
            static pyobj cast(std::vector<T> val, bool is_new);
            template <typename T>
            static pyobj cast(std::vector<T> val);
//            template <typename T>
//            static pyobj cast(T* val, bool is_new);
//            template <typename T>
//            static pyobj cast(T* val) { return cast<T>(val, false);}

            template<typename T>
            T getattr(std::string& attr);
            template<typename T>
            T getattr(const char* attr) {
                std::string ats = attr;
                return getattr<T>(ats);
            }

            template<typename T>
            T get_item(size_t idx);
            template<typename T>
            T get_key(const char* key);
            template<typename T>
            T get_key(std::string& key) {
                return get_item<T>(key.c_str());
            }


            pyiter get_iter();
            Py_ssize_t len() { return PyObject_Size(obj()); }

        };

        /*
         * Iterator interface for pyobj
         *
         *
         */
        // Start/end sentinels
        pyobj IteratorStart(PyTuple_New(0));
        pyobj IteratorEnd(PyTuple_New(0));
        class pyiter {
            using iterator_category = std::input_iterator_tag;
            using difference_type   = std::ptrdiff_t;
            using value_type        = pyobj;
            using pointer           = pyobj*;  // or also value_type*
            using reference         = pyobj&;  // or also value_type&

            pyobj consumer;
            pyobj cur;
        public:
            explicit pyiter(pyobj vals) : consumer(vals), cur(IteratorStart) {
                next();
            };
            pyiter(pyobj vals, pyobj cur) : consumer(vals), cur(cur) {};
            bool valid() { return cur.valid(); }

//            explicit operator bool() { return !done; }

            reference operator*() {
//                printf("...*\n");
                return cur;
            }
            pointer operator->() {
//                printf("...->\n");
                return &cur;
            }

            void next() {
                if (!cur.valid()) { throw std::runtime_error("iterator exhausted..."); }
                cur = pyobj(PyIter_Next(consumer.obj()), true);
                if (!cur.valid()) {
//                    printf("...done?\n");
                    cur = IteratorEnd;
                }
            }

            // Prefix increment
            pyiter& operator++() {
//                printf("++...\n");
                next();
                return *this;
            }
            // Postfix increment
            const pyiter operator++(int) {
//                printf("++...\n");
                pyiter tmp = *this;
                ++(*this);
                return tmp;
            }

            bool operator== (pyiter& b) {
//                printf("comparing %s == %s\n", cur.repr().c_str(), b.cur.repr().c_str());
                return cur == b.cur;
            };
            bool operator!= (pyiter& b) {
//                printf("comparing %s != %s\n", cur.repr().c_str(), b.cur.repr().c_str());
                return cur != b.cur;
            };

            pyiter begin() { return *this; }
            pyiter end()   { return pyiter(pyobj(), IteratorEnd); }

        };
        pyiter pyobj::get_iter() {
            auto iter_obj = pyobj(PyObject_GetIter(obj()), true);
            return pyiter(iter_obj);
        }

        // random print function...
        void print_obj(const char* fmt, pyobj obj);


        /*
         * NECESSARY NUMPY FUCKERY
         *
         *
         *
         */
        long* _np_fuckery() {
            if(PyArray_API == NULL) {
                import_array();
                return NULL;
            } else {
                return NULL;
            }
        }
        void _np_init() {
            auto p = _np_fuckery();
            if (p != NULL) throw std::runtime_error("NumPy failed to load");
        }

        void _check_py_arr(PyObject* array) {
            if (!PyArray_Check(array)) {
                std::string msg = "expected numpy array got " + get_python_repr(array);
                PyErr_SetString(PyExc_TypeError, msg.c_str());
                throw std::runtime_error("requires NumPy array");
            }
        }


        /*
         * CONVERSIONS FROM C++ OBJECTS TO PYTHON OBJECTS
         *
         *
         *
         */

        template <typename T>
        class conversion_type_error : public std::runtime_error {
            std::string msg;
        public:
//            conversion_type_error() : std::runtime_error(typeid(T).name()), msg(typeid(T).name()) {};
            explicit conversion_type_error(const char* message) : std::runtime_error(message), msg(message) {};
            explicit conversion_type_error(std::string message) : std::runtime_error(message), msg(message) {};
            static std::string type_id() { return mcutils::type_name<T>::value; }
            const char * what() const noexcept override { return msg.c_str(); }
        };

        template<typename T>
        T from_python([[maybe_unused]] pyobj data) {
            auto typestr = conversion_type_error<T>::type_id();
            std::string msg = "Failed to convert from python for dtype: " + typestr + "\n";
            if (pyadeeb::debug_print(DebugLevel::Normal)) py_printf( "ERROR: Failed to convert from python for dtype %s\n", typestr.c_str());
            throw conversion_type_error<T>(msg);
        }
        template<typename T>
        T from_python(pyobj data, const char* typechar) {
            PyObject* argtup = PyTuple_Pack(1, data.obj());
            T val;
            int successy = PyArg_ParseTuple(argtup, typechar, &val);
            Py_XDECREF(argtup);
            if (!successy || PyErr_Occurred()) throw std::runtime_error("failed to build value...");
            return val;
        }
        template <>
        pyobj from_python<pyobj>(pyobj data) { return data; }
        template <>
        int from_python<int>(const pyobj data) { return from_python<int>(data, "i"); }
        template <>
        char from_python<char>(const pyobj data) { return (char) from_python<int>(data); } // meh
        template <>
        unsigned char from_python<unsigned char>(const pyobj data) { return from_python<unsigned char>(data, "b"); }
        template <>
        unsigned int from_python<unsigned int>(const pyobj data) { return from_python<unsigned int>(data, "I"); }
        template <>
        short from_python<short>(const pyobj data) { return from_python<short>(data, "h"); }
        template <>
        unsigned short from_python<unsigned short>(const pyobj data) { return from_python<unsigned short>(data, "H"); }
        template <>
        long from_python<long>(const pyobj data) { return from_python<long>(data, "l"); }
        template <>
        unsigned long from_python<unsigned long>(const pyobj data) { return from_python<unsigned long>(data, "k"); }
        template <>
        long long from_python<long long>(const pyobj data) { return from_python<long long>(data, "L"); }
        template <>
        unsigned long long from_python<unsigned long long>(const pyobj data) { return from_python<unsigned long long>(data, "K"); }
        template <>
        float from_python<float>(const pyobj data) { return from_python<float>(data, "f"); }
        template <>
        double from_python<double>(const pyobj data) { return from_python<double>(data, "d"); }
        template <>
        bool from_python<bool>(const pyobj data) { return PyObject_IsTrue(data.obj()); } // I guess this is more direct...
        template <>
        std::string from_python<std::string >(pyobj data) {
            // we're ditching even the pretense of python 2 support
            PyObject* pyStr = NULL;
            pyStr = PyUnicode_AsEncodedString(data.obj(), "utf-8", "strict");
            if (pyStr == NULL) { throw std::runtime_error("bad python shit"); };
            const char *strExcType =  PyBytes_AsString(pyStr);
            std::string str = strExcType; // data needs to be copied...will this do it?
            Py_XDECREF(pyStr);
            return str;
        }

        template<typename T>
        std::vector<T> from_python_iterable(pyobj data, Py_ssize_t num_els) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting from iterable %s\n", data.repr().c_str());

            std::vector<T> vec(num_els);
            // iterate through list
            auto iterator = data.get_iter();
            if (!iterator.valid()) { throw std::runtime_error("Iteration error"); }
            Py_ssize_t i = 0;
            for (pyobj item:iterator) {
//                printf("item %zd\n", i);
                if (i >= num_els) {
                    std::string msg =
                            "object was expected to have length "
                            + std::to_string(num_els) +
                            " but got more than that";
                    PyErr_SetString(
                            PyExc_ValueError,
                            msg.c_str()
                    );
                    throw std::runtime_error("Iterating beyond len()");
                }
                if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf("     --> getting item %zu\n", i);
                if (PyErr_Occurred()) {
                    py_printf(DebugLevel::Excessive, "     --> ...and we failed somehow\n");
                    throw std::runtime_error("Iteration error");
                }
                py_printf(DebugLevel::Excessive, "     --> converting from python types\n");
                vec[i] = item.convert<T>();
                i+=1;
            }
            if (PyErr_Occurred()) {
                throw std::runtime_error("Iteration error");
            }
            if (i < num_els) {
                std::string msg =
                        "object was expected to have length "
                        + std::to_string(num_els) +
                        " but got " + std::to_string(i) + " elements";
                PyErr_SetString(
                        PyExc_ValueError,
                        msg.c_str()
                );
                throw std::runtime_error("Iteration error");
            }

            return vec;
        }
        template<typename T>
        std::vector<T> from_python_iterable(pyobj data) {
            auto num_els = data.len();
            if (num_els < 0) {
                if (!PyErr_Occurred()) {
                    std::string msg = "expected iterable object but got " + data.repr();
                    PyErr_SetString(
                            PyExc_ValueError,
                            msg.c_str()
                    );
                }
                throw std::runtime_error("size issues in iterable %s");
            }
            return from_python_iterable<T>(data, num_els);
        }

        /*
         * Definition of print functions now that we have conversions
         *
         *
         *
         */
        std::string get_python_repr(PyObject* obj) {
            PyObject* repr = PyObject_Repr(obj);
            auto rep = from_python<std::string>(pyobj(repr));
            Py_XDECREF(repr);
            return rep;
        }

        void print_obj(const char* fmt, pyobj obj) {
            auto garb = obj.repr();
            py_printf(fmt, garb.c_str());
        }


        /*
         * CONVERSIONS FROM C++ OBJECTS TO PYTHON OBJECTS
         *
         *
         *
         */

        template<typename T>
        PyObject* as_python_object([[maybe_unused]] T data) {
            auto typestr = conversion_type_error<T>::type_id();
            std::string msg = "Failed to convert to python for dtype: " + typestr + "\n";
            if (pyadeeb::debug_print(DebugLevel::Normal))py_printf( "ERROR: Failed to convert to python for dtype %s\n", typestr.c_str());
            throw conversion_type_error<T>(msg);
        }
        template <>
        PyObject* as_python_object<PyObject*>(PyObject* data) {
            if (pyadeeb::debug_print()) py_printf("     --> Converting as PyObject*");
            return data;
        }
        template <>
        PyObject* as_python_object<char>(char data) { py_printf(DebugLevel::All, "     --> Converting as char\n"); return Py_BuildValue("b", data); }
        template <>
        PyObject* as_python_object<unsigned char>(unsigned char data) { py_printf(DebugLevel::All, "     --> Converting as unsigned char\n"); return Py_BuildValue("B", data); }
        template <>
        PyObject* as_python_object<short>(short data) { py_printf(DebugLevel::All, "     --> Converting as short\n"); return Py_BuildValue("h", data); }
        template <>
        PyObject* as_python_object<unsigned short>(unsigned short data) { py_printf(DebugLevel::All, "     --> Converting as unsigned short\n"); return Py_BuildValue("H", data); }
        template <>
        PyObject* as_python_object<int>(int data) { py_printf(DebugLevel::All, "     --> Converting as int\n"); return Py_BuildValue("i", data); }
        template <>
        PyObject* as_python_object<unsigned int>(unsigned int data) { py_printf(DebugLevel::All, "     --> Converting as unsigned int\n"); return Py_BuildValue("I", data); }
        template <>
        PyObject* as_python_object<long>(long data) { py_printf(DebugLevel::All, "     --> Converting as long\n"); return Py_BuildValue("l", data); }
        template <>
        PyObject* as_python_object<unsigned long>(unsigned long data) { py_printf(DebugLevel::All, "     --> Converting as unsigned long\n"); return Py_BuildValue("k", data); }
        template <>
        PyObject* as_python_object<long long>(long long data) { py_printf(DebugLevel::All, "     --> Converting as long long\n"); return Py_BuildValue("L", data); }
        template <>
        PyObject* as_python_object<unsigned long long>(unsigned long long data) { py_printf(DebugLevel::All, "     --> Converting as unsigned long long\n"); return Py_BuildValue("K", data); }
//        template <>
//        Py_ssize_t convert<Py_ssize_t>(pyobj data) { return PyLong_AsSsize_t(data);  }
//        template <>
//        size_t convert<size_t>(pyobj data) { return PyLong_AsSize_t(data); }
        template <>
        PyObject* as_python_object<float>(float data) { py_printf(DebugLevel::All, "     --> Converting as float\n"); return Py_BuildValue("f", data); }
        template <>
        PyObject* as_python_object<double>(double data) { py_printf(DebugLevel::All, "     --> Converting as double\n"); return Py_BuildValue("d", data); }
        template <>
        PyObject* as_python_object<bool>(bool data) {
            py_printf(DebugLevel::All, "     --> Converting as bool\n");
            if (data) {
                Py_RETURN_TRUE;
            } else {
                Py_RETURN_FALSE;
            }
        }
        template <>
        PyObject* as_python_object<std::string>(std::string data) {
            py_printf(DebugLevel::All, "     --> Converting as string\n");
            return Py_BuildValue("s", data.c_str());
        }
        template <>
        PyObject* as_python_object<const char*>(const char* data) {
            py_printf(DebugLevel::All, "     --> Converting as string\n");
            return Py_BuildValue("s", data);
        }

        template<typename T>
        pyobj as_python(T data) {
            return pyobj(as_python_object<T>(data));
        }
        template<>
        pyobj as_python<pyobj>(pyobj data) {
            return data;
        }
        template <>
        PyObject* as_python_object<pyobj>(pyobj data) {
            return data.obj();
        }

        template<typename T>
        PyObject* as_python_tuple_object(std::vector<T> data, Py_ssize_t num_els) {
            auto tup = PyTuple_New(num_els);
            if (tup == NULL) return NULL; // Assume the error is caught lower down
            for (size_t i = 0; i < data.size(); i++) {
                PyTuple_SET_ITEM(tup, i, as_python_object<T>(data[i]));
            }
            return tup;
        }
        template<typename T>
        PyObject* as_python_tuple_object(std::vector<T> data) {
            return as_python_tuple_object<T>(data, data.size());
        }

        template<typename T>
        pyobj as_python_tuple(std::vector<T> data, Py_ssize_t num_els) {
            return pyobj(as_python_tuple_object<T>(data, num_els));
        }
        template<typename T>
        pyobj as_python_tuple(std::vector<T> data) {
            return pyobj(as_python_tuple_object<T>(data, data.size()));
        }


        PyObject* as_python_dict_object(
                const std::vector<std::string>& keys,
                std::vector<pyobj>& values
        ) {
            // very basic dict builder

            auto dict = PyDict_New();
            for (size_t i = 0; i < keys.size(); i++) {

                if (pyadeeb::debug_print(DebugLevel::All)) {
                    py_printf("     --> assigning object %s to key %s\n", values[i].repr().c_str(), keys[i].c_str());
                }

                auto k = keys[i];
                if (PyDict_SetItemString(dict, k.c_str(), values[i].obj()) < 0) {
                    Py_XDECREF(dict);
                    return NULL;
                }
            }

            return dict;

        }

        pyobj as_python_dict(
                const std::vector<std::string>& keys,
                std::vector<pyobj>& values
        ) {
            return pyobj(as_python_dict_object(keys, values));
        }

        /*
         * PyCapsule CONVERSIONS
         *
         *
         */

        template<typename T>
        T get_pycapsule_ptr(PyObject* cap, const char* name) {
            auto obj = PyCapsule_GetPointer(cap, name);
            if (obj == NULL) { throw std::runtime_error("Capsule error"); }
            return T(obj); // explicit cast
        }
        template<typename T>
        T get_pycapsule_ptr(PyObject* cap, std::string& name) {
            return get_pycapsule_ptr<T>(cap, name.c_str());
        }
        template<typename T>
        T from_python_capsule(PyObject* cap, const char* name) {
            return *get_pycapsule_ptr<T*>(cap, name); // explicit dereference
        }
        template<typename T>
        T from_python_capsule(PyObject* cap, std::string& name) {
            return from_python_capsule<T>(cap, name.c_str());
        }
        template<typename T>
        T from_python_capsule(pyobj cap, const char* name) {
            return *get_pycapsule_ptr<T*>(cap.obj(), name); // explicit dereference
        }
        template<typename T>
        T from_python_capsule(pyobj cap, std::string& name) {
            return from_python_capsule<T>(cap.obj(), name);
        }
        template<typename T>
        T from_python_capsule(pyobj cap, std::string name) {
            return from_python_capsule<T>(cap.obj(), name);
        }

        /*
         * NUMPY CONVERSIONS
         *
         *
         */

        template<typename T>
        T* get_numpy_data(PyObject *array) {
            _np_init();
            _check_py_arr(array);
            auto py_arr = (PyArrayObject*) array;
            return (T*) PyArray_DATA(py_arr);
        }
        template<typename T>
        T* from_python_buffer(PyObject* data) { // Pointer types _only_ allowed for NumPy arrays
            return get_numpy_data<T>(data);
        }
        template<typename T>
        T* from_python_buffer(pyobj data) { // Pointer types _only_ allowed for NumPy arrays
            return get_numpy_data<T>(data.obj());
        }

        template<typename T>
        struct numpy_type {
            static NPY_TYPES value() {
//                char msg[60] = "";
//                sprintf(msg, "can't resolve type %s to numpy type...", typeid(T).name());
//                throw std::runtime_error(msg);
                auto typestr = conversion_type_error<T>::type_id();
                std::string msg = "Failed to convert from python for numpy dtype: " + typestr + "\n";
                if (pyadeeb::debug_print(DebugLevel::Normal))
                    py_printf("ERROR: Failed to convert from python for numpy dtype %s\n", typestr.c_str());
                throw conversion_type_error<T>(msg);
            };
        };
        template <>
        struct numpy_type<npy_bool> { static NPY_TYPES value() {return NPY_BOOL;  } };
        template <>
        struct numpy_type<pyobj> { static NPY_TYPES value() {return NPY_OBJECT;  } };
        template <>
        struct numpy_type<npy_int8> { static NPY_TYPES value() {return NPY_INT8;  } };
        template <>
        struct numpy_type<npy_int16> { static NPY_TYPES value() {return NPY_INT16;  } };
        template <>
        struct numpy_type<npy_int32> { static NPY_TYPES value() {return NPY_INT32;  } };
        template <>
        struct numpy_type<npy_int64> { static NPY_TYPES value() {return NPY_INT64;  } };
        template <>
        struct numpy_type<npy_uint16> { static NPY_TYPES value() {return NPY_UINT16;  } };
        template <>
        struct numpy_type<npy_uint32> { static NPY_TYPES value() {return NPY_UINT32;  } };
        template <>
        struct numpy_type<npy_uint64> { static NPY_TYPES value() {return NPY_UINT64;  } };
        template <>
        struct numpy_type<npy_float32> { static NPY_TYPES value() {return NPY_FLOAT32;  } };
        template <>
        struct numpy_type<npy_float64> { static NPY_TYPES value() {return NPY_FLOAT64;  } };
        template <>
        struct numpy_type<npy_float128> { static NPY_TYPES value() {return NPY_FLOAT128;  } };
//
//        template <>
//        NPY_TYPES numpy_type<pyobj>() { return NPY_OBJECT; }
//        template <>
//        NPY_TYPES numpy_type<npy_int8>() { return NPY_INT8; }
//        template <>
//        NPY_TYPES numpy_type<npy_int16>() { return NPY_INT16; }
//        template <>
//        NPY_TYPES numpy_type<npy_int32>() { return NPY_INT32; }
//        template <>
//        NPY_TYPES numpy_type<npy_int64>() { return NPY_INT64; }
////        template <>
////        NPY_TYPES numpy_type<npy_uint8>() { return NPY_UINT8; }
//        template <>
//        NPY_TYPES numpy_type<npy_uint16>() { return NPY_UINT16; }
//        template <>
//        NPY_TYPES numpy_type<npy_uint32>() { return NPY_UINT32; }
//        template <>
//        NPY_TYPES numpy_type<npy_uint64>() { return NPY_UINT64; }
////        template <>
////        NPY_TYPES numpy_type<npy_float16>() { return NPY_FLOAT16; }
//        template <>
//        NPY_TYPES numpy_type<npy_float32>() { return NPY_FLOAT32; }
//        template <>
//        NPY_TYPES numpy_type<npy_float64>() { return NPY_FLOAT64; }
//        template <>
//        NPY_TYPES numpy_type<npy_float128>() { return NPY_FLOAT128; }
////        template <>
////        NPY_TYPES numpy_type<double>() { return NPY_DOUBLE; }
////        template <>
////        NPY_TYPES numpy_type<float>() { return NPY_FLOAT; }


        // Stack Overflow solution to allow me to determine if our types are vectors
        // in which case I'll concat a fat ol' vec and call again
        template<typename Test, template<typename...> class Ref>
        struct is_specialization : std::false_type {};
        template<template<typename...> class Ref, typename... Args>
        struct is_specialization<Ref<Args...>, Ref>: std::true_type {};

        template<typename base, template<typename...> class container>
        struct base_type { using value=base; };
        template<template<typename, typename...> class container, typename base, typename... Args>
        struct base_type<container<base, Args...>, container>: base_type<base, container> {};
//
        template<typename base, template<typename...> class container>
        struct sub_type { using value=base; };
        template<template<typename, typename...> class container, typename base, typename... Args>
        struct sub_type<container<base, Args...>, container> { using value=base; };

        size_t total_elements(std::vector<size_t>& shape) {
            size_t start = 1;
            return std::accumulate(shape.begin(), shape.end(), start, std::multiplies<size_t>()); // explicit cast b.c. shape is positive
        }

        template<typename base, template<typename...> class container>
//        struct shape_extractor;
        struct shape_extractor {
            using type=base;
            static void extract([[maybe_unused]] std::vector<size_t>& shape, [[maybe_unused]] base& val) {}
        };
        template<template<typename, typename...> class container, typename base, typename... Args>
        struct shape_extractor<container<base, Args...>, container> {
            using type=base;
            static void extract(std::vector<size_t>& shape, container<base, Args...>& vec) {
                shape.push_back(vec.size());
                if constexpr(is_specialization<base, container>::value) {
                    auto v = vec[0];
                    shape_extractor<base, container>::extract(shape, v);
                }
            }
        };
        template<template<typename, typename...> class container, typename... Args>
        struct shape_extractor<container<bool, Args...>, container> {
            static void extract(std::vector<size_t>& shape, container<bool, Args...>& vec) {
                shape.push_back(vec.size());
            }
        };
//        template <typename T>
//        void extract_shape(std::vector<size_t>& shape, std::vector<T>& vec) {
//            shape.push_back(vec.size());
//            if (is_specialization<T, std::vector>::value) {
//                using D = typename sub_type<T, std::vector>::value;
//                std::vector<D> v = vec[0];
//                extract_shape<D>(shape, v);
//            }
//        }
        template <typename T>
        std::vector<size_t> extract_shape(std::vector<T>& vec) {
            if constexpr(is_specialization<T, std::vector>::value) {
                std::vector<size_t> shape;
                shape_extractor<std::vector<T>, std::vector>::extract(shape, vec);
                return shape;
            } else {
                return {vec.size()};
            }
        }

        std::vector<size_t> manage_shape(size_t num_els, std::vector<size_t>& base_shape) {
            size_t zero_loc = base_shape.size();
            size_t block_size = 1;
            size_t s;
            for (size_t i=0; i < base_shape.size(); i++) {
                s = base_shape[i];
                if (s > 0) {
                    block_size *= s;
                } else if (zero_loc >= base_shape.size()) {
                    throw std::runtime_error("indeterminate shape");
                } else {
                    zero_loc = i;
                }
            }

//            py_printf("block size: %lu & zero loc: %lu\n", block_size, zero_loc);

            if (zero_loc == base_shape.size()) {
                return base_shape;
            } else {
                auto new_shape(base_shape);
                new_shape[zero_loc] = num_els / block_size;
                return new_shape;
            }

        }
        template <typename T>
        std::vector<size_t> manage_shape(std::vector<T>& vec, std::vector<size_t>& base_shape) {
            if (base_shape.empty()) {
                return {vec.size()};
            } else {
                auto shp = extract_shape<T>(vec);
    //            py_printf( "          - extracted shape: ( ");
    //            for (auto s: shp) py_printf( "%lu ", s);
    //            py_printf(")\n");
    //            py_printf( "          - base shape: ( ");
    //            for (auto s: base_shape) py_printf( "%lu ", s);
    //            py_printf(")\n");
                return manage_shape(total_elements(shp), base_shape);
            }
        }

        template<typename T>
        void populate_numpy_array(PyObject* arr, T* buffer, size_t buffer_size) {
            T* npy_buf = get_numpy_data<T>(arr);
            size_t bytes = sizeof(T) * buffer_size;
            memcpy(npy_buf, buffer, bytes);
        }

        template<>
        void populate_numpy_array(PyObject* arr, pyobj* buffer, size_t buffer_size) {
            auto npy_buf = get_numpy_data<PyObject*>(arr);
            for (size_t i = 0; i < buffer_size; i++) {
                npy_buf[i] = buffer[i].obj();
            }
        }

        template<>
        void populate_numpy_array(PyObject* arr, std::string* buffer, size_t buffer_size) {
            auto npy_buf = get_numpy_data<char*>(arr);
            for (size_t i = 0; i < buffer_size; i++) {
                strcpy(npy_buf[i], buffer[i].c_str());
            }
        }

        template<typename T>
        PyObject* numpy_object_from_data(
                T* buffer, size_t buffer_size,
                NPY_TYPES dtype,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            _np_init();
            auto dims = (npy_intp*) shape.data();
            auto nd = shape.size();
//            py_printf("huh fack %lu %lu %lu %lu\n", dims[0], dims[1], dims[2], dims[3]);
            if (copy) {
                if (pyadeeb::debug_print(DebugLevel::Excessive)) {
                    py_printf("     --> creating new numpy array of dtype %s by copying buffer of size %lu shape (", mcutils::type_name<T>::c_str(), buffer_size);
                    for (auto s: shape) py_printf( "%lu ", s);
                    py_printf(")\n");
                };
                PyObject* arr = PyArray_SimpleNew(
                        static_cast<int>(nd), // should I check the size of `nd` first or let numpy do that...?
                        dims,
                        dtype
                );
                if (arr == NULL) {
                    throw std::runtime_error("bad numpy shit");
                }
                populate_numpy_array(arr, buffer, buffer_size);
//                T* npy_buf = get_numpy_data<T>(arr);
//                size_t bytes = sizeof(T) * buffer_size;
//                memcpy(npy_buf, buffer, bytes);
 //               auto arr = PyArray_EMPTY(0, 0, dtype, false);
 //               if (arr == NULL) {
 //                   throw std::runtime_error("bad numpy shit");
 //               }
                // Py_XINCREF(arr);
                return arr;
            } else {
                if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf("     --> creating new numpy array of dtype %s by reusing buffer\n", mcutils::type_name<T>::c_str());

                PyObject* arr = PyArray_SimpleNewFromData(
                        nd,
                        dims,
                        dtype,
                        buffer
                );
                if (arr == NULL) {
                    throw std::runtime_error("bad numpy shit");
                }
                // Py_XINCREF(arr);
                return arr;
            }

        }
        template<typename T>
        PyObject* numpy_object_from_data(
                T* buffer,
                NPY_TYPES dtype,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            return numpy_object_from_data<T>(buffer, total_elements(shape), dtype, shape, copy);
        }

//        template<typename D, typename V>
//        class buffer_populator {
//            D *buffer;
//            size_t &cur_pos;
//        public:
//            buffer_populator(D *buf, size_t &cur) : buffer(buf), cur_pos(cur) {}
//            void populate(V& cur_obj) {
//                if (!is_specialization<V, std::vector>::value) {
//                    throw std::runtime_error("type mismatch");
//                } else {
//                    throw std::runtime_error("wwtf???");
//                }
//            };
//            void populate(std::vector<V> &cur_vec) {
//                if (std::is_same_v<V, D>) { // two non-vector types
//                    for (size_t i = 0; i < cur_vec.size(); i++) {
//                        buffer[cur_pos + i] = cur_vec[i];
//                    }
//                    cur_pos = cur_pos + cur_vec.size();
//                } else if (is_specialization<V, std::vector>::value) {
//                    // V = std::vector<P>
//                    auto pop = buffer_populator<D, V>(buffer, cur_pos);
//                    for (auto v:cur_vec) { pop.populate(v); }
//                } else {
//                    throw std::runtime_error("type mismatch");
//                }
//            };
//        };
//        template<typename D, typename V>
//        class buffer_populator<D, std::vector<V>> { // digs in one level
//            D *buffer;
//            size_t &cur_pos;
//        public:
//            buffer_populator(D *buf, size_t &cur) : buffer(buf), cur_pos(cur) {}
//            void populate(std::vector<V> &cur_vec) {
//                auto pop = buffer_populator<D, V>(buffer, cur_pos);
//            };
//        };
////        template<>
////        class buffer_populator<bool, bool> {
////            bool *buffer;
////            size_t &cur_pos;
////        public:
////            buffer_populator(bool *buf, size_t &cur) : buffer(buf), cur_pos(cur) {}
////            void populate(std::vector<bool> &cur_vec) {
////                for (size_t i = 0; i < cur_vec.size(); i++) {
////                    buffer[cur_pos + i] = cur_vec[i];
////                }
////                cur_pos = cur_pos + cur_vec.size();
////            };
////            void populate(std::vector<std::vector<bool>> &cur_vec) {
////                for (auto& v:cur_vec) {
////                    populate(v);
////                }
////            };
////        };
//
//        template<typename T>
//        class numpy_object_from_data_converter {
//            T* buffer;
//            std::vector<size_t>& shape;
//            bool copy;
//        public:
//            numpy_object_from_data_converter(T* buf, std::vector<size_t>& shp, bool cpy = true) :
//                buffer(buf), shape(shp), copy(cpy) {}
//            PyObject* convert() {
//                auto npy_type = numpy_type<T>();
//                return numpy_object_from_data<T>(buffer, npy_type, shape, copy);
//            }
//        };
//        template<typename V>
//        class numpy_object_from_data_converter<std::vector<V>> {
//            std::vector<V>* buffer;
//            std::vector<size_t>& shape;
//            bool copy;
//        public:
//            numpy_object_from_data_converter(std::vector<V>* buf, std::vector<size_t>& shp, bool cpy = true) :
//                    buffer(buf), shape(shp), copy(cpy) {}
//            PyObject* convert() {
//                using D = typename base_type<V, std::vector>::value;
//                size_t nels = std::accumulate(shape.begin(), shape.end(), 1, std::multiplies<>());
//                D new_vec[nels];
//                size_t cur_pos = 0;
//                buffer_populator<D, V> pop(new_vec, cur_pos);
//                for (size_t i = 0; i < shape[0]; i ++) {
//                    std::vector<V> sub_vec = buffer[i];
//                    pop.populate(sub_vec);
//                }
//                auto conv = numpy_object_from_data_converter<D>(new_vec, shape, true);
//                return conv.convert();
//            }
//        };

        template <typename D, typename V>
        D* apply_multindex(std::vector<V>* vec, std::vector<size_t>& idx) {
            if constexpr (std::is_same_v<D, V>) {
                return vec[idx[0]].data();
            } else {
                std::vector<V> v = vec[idx[0]];
                return apply_multindex<D, V>(v, idx, 1);
            }
        }
        template <typename D, typename V>
        D* apply_multindex(std::vector<std::vector<V>>& vec, std::vector<size_t>& idx, size_t cur) {
            return apply_multindex<D, V>(vec[idx[cur]], idx, cur+1);
        }
        template <typename D, typename V>
        D* apply_multindex(std::vector<V>& vec, std::vector<size_t>& idx, size_t cur) {
            if constexpr (std::is_same_v<D, V>) {
                return vec.data();
            } else {
                using S = typename sub_type<V, std::vector>::value;
                return apply_multindex<D, S>(vec, idx, cur + 1);
            }
        }
        // version that will populate a subbuffer instead of returning a pointer to data (just for bool vecs)
        template <typename D, typename V>
        void apply_multindex(std::vector<V>* vec, std::vector<size_t>& idx, D* target) {
            if constexpr (std::is_same_v<D, V>) {
                std::copy(vec[idx[0]].begin(), vec[idx[0]].end(), target);
            } else {
                std::vector<V> v = vec[idx[0]];
                return apply_multindex<D, V>(v, idx, target, 1);
            }
        }
        template<>
        void apply_multindex<bool, bool>(std::vector<bool>* vec, std::vector<size_t>& idx, bool* target) {
            auto v = vec[idx[0]];
            for (size_t i = 0; i < v.size(); i++) {
                target[i] = v[i];
            }
        }
        template <typename D, typename V>
        void apply_multindex(std::vector<std::vector<V>>& vec, std::vector<size_t>& idx, D* target, size_t cur) {
            apply_multindex<D, V>(vec[idx[cur]], idx, target, cur+1);
        }
        template <typename D, typename V>
        void apply_multindex(std::vector<V>& vec, std::vector<size_t>& idx, D* target, size_t cur) {
            if constexpr (std::is_same_v<D, V>) {
                std::copy(vec.begin(), vec.end(), target);
            } else {
                using S = typename sub_type<V, std::vector>::value;
                apply_multindex<D, S>(vec, idx, target, cur + 1);
            }
        }

        std::vector<size_t> get_multindex(std::vector<size_t>& shape, size_t block_base, size_t lindex) {
            auto ndim = shape.size();
            std::vector<size_t> mindex(ndim);

            auto block_size = block_base;
            for (size_t d = 0; d < ndim; d++ ) {
                block_size /= shape[d]; // get subblock size
                mindex[d] = lindex / block_size; // which block are we in
                lindex = lindex % block_size; // reset for the subindices
            }
            return mindex;
        }
        std::vector<size_t> get_multindex(std::vector<size_t>& shape, size_t lindex) {
            return get_multindex(
                    shape,
                    total_elements(shape),
                    lindex
                    );
        }

        template<typename T>
        PyObject* numpy_object_from_data(
                T* buffer, size_t buffer_size,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf( "     --> converting buffer to numpy\n");
            auto npy_type = numpy_type<T>::value();
            return numpy_object_from_data<T>(buffer, buffer_size, npy_type, shape, copy);
        }

        template<typename T>
        PyObject* numpy_object_from_data(
                T* buffer,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            return numpy_object_from_data<T>(buffer, total_elements(shape), shape, copy);
        }
        template<typename V>
        PyObject* numpy_object_from_data(
                std::vector<V>* buffer, size_t buffer_size,
                std::vector<size_t>& shape,
                [[maybe_unused]] bool copy = true
        ) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf( "     --> flattening nested buffer of vectors\n");
            using D = typename base_type<V, std::vector>::value;
//            using V = typename sub_type<T, std::vector>::value;

            auto subshape = extract_shape<V>(buffer[0]);
            std::vector<size_t> fullshape(1 + subshape.size());
            fullshape[0] = buffer_size;
            std::copy(subshape.begin(), subshape.end(), fullshape.begin() + 1);

            // the vector offset and shape of tensor of vectors
            auto offset = subshape[subshape.size()-1];
            std::vector<size_t> core_shape(fullshape.begin(), fullshape.end()-1);

            auto nels = total_elements(fullshape);
            auto nvecs = nels/offset; // number of vecs to flatten
            size_t cur_pos = 0;

            // hacky way to concat the arrays, skipping the final
            // elements which we assume will be primitive typed
            if (pyadeeb::debug_print(DebugLevel::All)) {
                py_printf( "          - full shape: ( ");
                    for (auto s: fullshape) py_printf( "%lu ", s);
                    py_printf(")\n");
                py_printf( "          - %lu subvectors\n", nvecs);
                py_printf( "          - subvector size?: %lu\n", offset);
            }

            // if (pyadeeb::debug_print(DebugLevel::All)) {
            //     py_printf( "          - allocating buffer of size");
            //     py_printf( "..........???????!\n");
            // }

            if (pyadeeb::debug_print(DebugLevel::Excessive)) {
                py_printf( "          - allocating buffer %s[%lu]\n", mcutils::type_name<D>::value.c_str(), nels);
            }
            


            auto new_vec = new D[nels]; // allocate on _heap_

            // if (pyadeeb::debug_print(DebugLevel::All)) {
            //     py_printf( "..........???????!\n");
            // }
            
            if constexpr (std::is_same_v<D, bool>) {

//                bool subbuffer[offset];
                for (size_t i = 0; i < nvecs; i++) {
                    auto mindex = get_multindex(core_shape, nels, i);
                    apply_multindex<D, V>(buffer, mindex, new_vec + cur_pos); // fills buffer instead of returning buffer b.c. vec<bool> is special
//                    std::copy(subbuffer, subbuffer + offset, new_vec + cur_pos);
                    cur_pos += offset;
                    //                for (size_t j = 0; j < subv.size(); j++) {
                    //                    new_vec[cur_pos + j] = subv[j];
                    //                }
                }
            } else {

                for (size_t i = 0; i < nvecs; i++) {
                    auto mindex = get_multindex(core_shape, nvecs, i);

                    // py_printf( "          - pos: %lu ", i);
                    // if (pyadeeb::debug_print(DebugLevel::Excessive)) {
                    //     py_printf("idx: ( "); for (auto s: mindex) py_printf( "%lu ", s); py_printf(")\n");
                    // }

                    //                std::vector<V> v = buffer[mindex[0]]; // does this copy...?
                    D *subv = apply_multindex<D, V>(buffer, mindex); // returns raw pointer to hopefully ensure no copies
                    std::copy(subv, subv + offset, new_vec + cur_pos);
                    cur_pos += offset;
                    //                for (size_t j = 0; j < subv.size(); j++) {
                    //                    new_vec[cur_pos + j] = subv[j];
                    //                }
                }
            }

            // if (pyadeeb::debug_print(DebugLevel::All)) {
            //     py_printf( "          - finished populating:\n");
            // }

            return numpy_object_from_data<D>(new_vec, nels, shape, false); // will be managed by numpy since we heap allocated
//            return numpy_object_from_data<std::vector<T>>(buffer, shape, copy);
        }
        template<>
        PyObject* numpy_object_from_data<bool>(
                bool* buffer,
                std::vector<size_t>& shape,
                bool copy
        ) {
            if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf( "     --> converting buffer of bools\n");
            auto npy_type = numpy_type<bool>::value();
            return numpy_object_from_data<bool>(buffer, npy_type, shape, copy);
        }

//        template<>
//        PyObject* numpy_object_from_data<double>(
//                double* buffer,
//                std::vector<size_t>& shape,
//                bool copy
//        ) {
////            py_printf("....? %f %f %f\n", buffer[0], buffer[1], buffer[2]);
//            auto wat = numpy_object_from_data<double>(buffer, NPY_FLOAT64, shape, copy );
////            print_obj("wat %s\n", wat);
//            return wat;
//        }

        PyObject* numpy_copy_array(PyObject* obj) {
            _np_init();
            _check_py_arr(obj);
            auto arr = (PyArrayObject*) obj; // I think this is how one builds an array obj...?
            auto descr = PyArray_DESCR(arr);
            Py_XINCREF(descr);
            return PyArray_FromArray(arr, descr, NPY_ARRAY_ENSURECOPY);
        }
        pyobj numpy_copy_array(pyobj obj) {
            return pyobj(numpy_copy_array(obj.obj()));
        }

        template<typename T>
        PyObject* numpy_object_from_data(
                std::vector<T>& vec,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting std::vector<%s> to numpy array\n", mcutils::type_name<T>::c_str());
            if (!vec.empty()) {
                T *buffer = vec.data();
                auto new_shape = manage_shape<T>(vec, shape);
                return numpy_object_from_data<T>(buffer, new_shape, copy);
            } else {
                std::vector<npy_intp> dim_vec;
                auto dims = (npy_intp*) dim_vec.data();
                auto npy_type = numpy_type<T>::value();
                auto arr = PyArray_EMPTY(0, dims, npy_type, false);
                return arr;
            }
        }
        template<typename T>
        PyObject* numpy_object_from_data(
                std::vector<std::vector<T>>& vec,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            if (!vec.empty()) {
                std::vector<T> *buffer = vec.data();
                auto new_shape = manage_shape<std::vector<T>>(vec, shape); // do I want to manage now???
                return numpy_object_from_data<T>(buffer, vec.size(), new_shape, copy);
            } else {
                std::vector<npy_intp> dim_vec;
                auto dims = (npy_intp*) dim_vec.data();
                auto npy_type = numpy_type<T>::value();
                auto arr = PyArray_EMPTY(0, dims, npy_type, false);
                return arr;
            }
        }
        template<>
        PyObject* numpy_object_from_data<bool>(
                std::vector<bool>& vec,
                std::vector<size_t>& shape,
                bool copy
        ) {
            if (!vec.empty()) {
                auto nels = vec.size();
                auto buffer = new bool[nels];
                auto new_shape = manage_shape(nels, shape);
//                for (auto s:new_shape) {
//                    printf("???? %zu ", s);
//                }
//                printf("\n");
                for (size_t i=0; i < nels; i++) { buffer[nels] = vec[i]; }
                return numpy_object_from_data<bool>(buffer, new_shape, copy);
//                return numpy_copy_array(arr); // We'll let other parts of the code-base do copies if they want
            } else {
                std::vector<npy_intp> dim_vec;
                auto dims = (npy_intp*) dim_vec.data();
                auto npy_type = numpy_type<bool>::value();
                auto arr = PyArray_EMPTY(0, dims, npy_type, false);
                return arr;
            }
        }

        template<typename T>
        PyObject* as_python_object(std::vector<T> data) {
            if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf("     --> converting std::vector<%s> to PyObject*\n", mcutils::type_name<T>::c_str());
//            return as_python_tuple_object<T>(data);
            std::vector<size_t> shape = extract_shape<T>(data);
            return numpy_object_from_data<T>(data, shape);
        }
        template<>
        PyObject* as_python_object<std::vector<pyobj>>(std::vector<pyobj> data) {
            if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf("     --> converting std::vector<pyobj> to PyObject*\n");
            return as_python_tuple_object<pyobj>(data);
        }
        template<typename T>
        pyobj as_python(std::vector<T> data) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting std::vector<%s> to pyobj\n", mcutils::type_name<T>::c_str());
            return pyobj(as_python_object<T>(data));
        }

        template<typename T>
        pyobj numpy_from_data(
                T* buffer,
                NPY_TYPES dtype,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            return pyobj(numpy_object_from_data<T>(buffer, dtype, shape, copy));
        }
        template<typename T>
        pyobj numpy_from_data(
                T* buffer,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            return pyobj(numpy_object_from_data<T>(buffer, shape, copy));
        }
        template<typename T>
        pyobj numpy_from_data(
                std::vector<T>* buffer,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            return pyobj(numpy_object_from_data<T>(buffer, shape, copy));
        }
        template<typename T>
        pyobj numpy_from_data(
                std::vector<T>& vec,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting std::vector<%s> to pyobj(numpy)\n", mcutils::type_name<T>::c_str());

//            if (mcutils::python::pyadeeb::debug_print(DebugLevel::All)) {
//                mcutils::python::py_printf("Converting object of type std::vector<%s> to numpy\n", typeid(T).name());
//            }
            return pyobj(numpy_object_from_data<T>(vec, shape, copy));
        }
        template<typename T>
        pyobj numpy_from_data(
                std::vector<std::vector<T>>& vec,
                std::vector<size_t>& shape,
                bool copy = true
        ) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting nested std::vector<std::vector<%s>> to pyobj(numpy)\n", mcutils::type_name<T>::c_str());
//            if (mcutils::python::pyadeeb::debug_print(DebugLevel::All)) {
//                mcutils::python::py_printf("Converting object of type std::vector<%s> to numpy\n", typeid(T).name());
//            }
            return pyobj(numpy_object_from_data<T>(vec, shape, copy));
        }

        std::vector<size_t> numpy_shape_as_size_t(PyObject* obj) {
            _np_init();
            _check_py_arr(obj);
            auto arr = (PyArrayObject*) obj; // I think this is how one builds an array obj...?
            auto shp = (size_t*) PyArray_SHAPE(arr);
            return std::vector<size_t>(shp, shp + PyArray_NDIM(arr));
        }
        template <typename T>
        std::vector<T> numpy_shape(PyObject* obj) {
            auto base_shape = numpy_shape_as_size_t(obj);
            return std::vector<T>(base_shape.begin(), base_shape.end());
        }
        template <>
        std::vector<size_t> numpy_shape<size_t>(PyObject* obj) {
            return numpy_shape_as_size_t(obj);
        }

        std::string get_py_err_msg() {
            PyObject *ptype, *pvalue, *ptraceback;
            PyErr_Fetch(&ptype, &pvalue, &ptraceback);
            std::string err_msg;
            if (ptype != NULL) {
                if (pvalue != NULL && ptype != PyExc_SystemError) { err_msg = get_python_repr(pvalue); }
                PyErr_Restore(ptype, pvalue, ptraceback);
            }
            return err_msg;
        }

        /*
         * Full suite of conversions for pyobj using template specification
         *
         *
         */

        template <typename T>
        class PyObject_converter {
            pyobj obj;
        public:
            explicit PyObject_converter(pyobj py_obj) : obj(py_obj) {};
            T value() {
                if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting pyobj to %s\n", mcutils::type_name<T>::c_str());
                return from_python<T>(obj);
            }
        };
        template <typename T>
        class PyObject_converter<std::vector<T>> {
            pyobj obj;
        public:
            explicit PyObject_converter(pyobj py_obj) : obj(py_obj) {};
            std::vector<T> value() {
                if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting pyobj to std::vector<%s>\n", mcutils::type_name<T>::c_str());
                return from_python_iterable<T>(obj);
            }
        };
        template <typename T>
        class PyObject_converter<T*> {
            pyobj obj;
        public:
            explicit PyObject_converter(pyobj py_obj) : obj(py_obj) {};
            T* value() {
                if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting pyobj to %s*\n", mcutils::type_name<T>::c_str());
                return from_python_buffer<T>(obj);
            }
        };
        template <>
        class PyObject_converter<PyObject*> {
            pyobj obj;
        public:
            explicit PyObject_converter(pyobj py_obj) : obj(py_obj) {};
            PyObject* value() {
                if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> converting pyobj to PyObject*\n");
                return obj.obj();
            }
        };
        template<typename T>
        T pyobj::convert() const {
            return PyObject_converter<T>(*this).value();
        }
        template<typename T>
        pyobj pyobj::cast(T val, bool is_new) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> casting %s to pyobj\n", mcutils::type_name<T>::c_str());
            auto obj = mcutils::python::as_python<T>(val);
            if (is_new) {obj.steal();}
            return obj;
        }
        template<typename T>
        pyobj pyobj::cast(T val) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> casting %s to pyobj\n", mcutils::type_name<T>::c_str());
            return mcutils::python::as_python<T>(val);
        }
        template<typename T>
        pyobj pyobj::cast(std::vector<T> val, bool is_new) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> casting std::vector<%s> to pyobj\n", mcutils::type_name<T>::c_str());
            auto obj = mcutils::python::as_python<T>(val);
            if (is_new) {obj.steal();}
            return obj;
        }
        template<typename T>
        pyobj pyobj::cast(std::vector<T> val) {
            if (pyadeeb::debug_print(DebugLevel::All)) py_printf("     --> casting std::vector<%s> to pyobj\n", mcutils::type_name<T>::c_str());
            return mcutils::python::as_python<T>(val);
        }
//        template<typename T>
//        pyobj pyobj::cast(T* val, bool is_new) {
//            auto obj = mcutils::python::as_python<T>(val);
//            if (is_new) {obj.steal();}
//            return obj;
//        }
//        template<typename T>
//        pyobj pyobj::cast(T val) {
//            return pyobj::cast<T>(val, false);
//        }


        /*
         * Attribute extractors
         *
         */
        pyobj get_python_attr_base(PyObject* obj, std::string& attr) {
            if (obj == NULL) {
                if (pyadeeb::debug_print(DebugLevel::Normal)) py_printf("ERROR: object is NULL! (can't get %s)\n", attr.c_str());
                std::string err = "requested attrib " + attr + " from NULL object";
                PyErr_SetString(PyExc_TypeError, err.c_str());
                throw std::runtime_error("no obj issue");
            }
            
            PyObject* ret = PyObject_GetAttrString(obj, attr.c_str());
            if (ret == NULL) {
                if (pyadeeb::debug_print(DebugLevel::Normal)) py_printf( "ERROR: failed to get attr %s\n", attr.c_str());
                if (get_py_err_msg().empty()) {
                    std::string err = "Requested attrib. \"" + attr + "\" but got NULL back...?";
                    PyErr_SetString(PyExc_AttributeError, err.c_str());
                }
                throw std::runtime_error("attribute error");
            }
            return pyobj(ret);
        }
        template<typename T>
        T pyobj::getattr(std::string& attr) {
            if (pyadeeb::debug_print(DebugLevel::Excessive)) py_printf("     --> getting attribute %s from object\n", attr.c_str());
            return get_python_attr_base(obj(), attr).convert<T>();
        }
        template<typename T>
        T pyobj::get_item(size_t idx) {
            return pyobj(PySequence_GetItem(obj(), idx), true).convert<T>();
        }
        template<typename T>
        T pyobj::get_key(const char* item) {
            return pyobj(PyDict_GetItemString(obj(), item)).convert<T>();
        }

        /*
         * Typename helper
         *
         *
         */
        std::string python_type_name(PyTypeObject* type) {
            if (type == NULL) return "NULL";
            return type->tp_name;
//            if (type == &PyType_Type) return "type";
//            if (type == &PyUnicode_Type) return "string";
//            if (type == &PyLong_Type) return "int";
//            if (type == &PyFloat_Type) return "float";
//            if (type == &PyList_Type) return "list";
//            if (type == &PyTuple_Type) return "tuple";
//            if (type == &PyDict_Type) return "dict";
//            if (type == &PyCapsule_Type) return "capsule";
//            _np_init();
//            if (type == &PyArray_Type) { // needs to go after the _np_init I think...
//                return "np.ndarray";
//            }
//            return std::to_string(reinterpret_cast<unsigned long>(type));
        }
    }

}

#endif //RYNLIB_PYALLUP_HPP
