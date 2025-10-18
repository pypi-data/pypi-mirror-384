#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "cmake_lib.h"

static PyObject *
spam_echo(PyObject *self, PyObject *args)
{
    PyObject *arg;

    if (!PyArg_ParseTuple(args, "O", &arg))
        return NULL;

    return my_func(arg);
}

static PyMethodDef SpamMethods[] = {
    {"echo",  spam_echo, METH_VARARGS,
     "Returns the arguments."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef spammodule = {
    PyModuleDef_HEAD_INIT,
    "_native",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    SpamMethods
};

PyMODINIT_FUNC
PyInit__native(void)
{
    return PyModule_Create(&spammodule);
}