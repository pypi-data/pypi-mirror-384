
cdef extern from "cmake_lib.h":
    object my_func(object)


def echo(obj):
    return my_func(obj)