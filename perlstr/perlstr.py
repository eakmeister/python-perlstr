import ctypes
import inspect
import re

callfunc = ctypes.CFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.c_void_p)

class PyTypeObject(ctypes.Structure):
    pass

PyTypeObject._fields_ = (
        ("ob_refcnt", ctypes.c_int),
        ("ob_type", ctypes.c_void_p),
        ("ob_size", ctypes.c_int),
        ("tp_name", ctypes.c_char_p),
        ("tp_basicsize", ctypes.c_ssize_t),
        ("tp_itemsize", ctypes.c_ssize_t),
        ("tp_dealloc", ctypes.c_void_p),
        ("tp_print", ctypes.c_void_p),
        ("tp_getattr", ctypes.c_void_p),
        ("tp_setattr", ctypes.c_void_p),
        ("tp_reserved", ctypes.c_void_p),
        ("tp_repr", ctypes.c_void_p),
        ("tp_as_number", ctypes.c_void_p),
        ("tp_as_sequence", ctypes.c_void_p),
        ("tp_as_wrapping", ctypes.c_void_p),
        ("tp_hash", ctypes.c_void_p),
        ("tp_call", callfunc),
    )

class PyObject(ctypes.Structure):
    _fields_ = [
        ('ob_refcnt', ctypes.c_ssize_t),
        ('ob_type', ctypes.POINTER(PyTypeObject)),
    ]

class DollarToken(object):
    pass

def findany(s, regex):
    index = 0

    while index < len(s):
        if not re.match(regex, s[index]):
            return index
        
        index += 1

    return len(s)

@callfunc
def call(self, *args, **kwargs):
    current_frame = inspect.currentframe()
    caller = inspect.getouterframes(current_frame)[1]
    local_vars = caller[0].f_locals

    tokens = []
    index = 0

    curr_str = ''
    while index < len(self):
        if self[index] == '$':
            if curr_str != '':
                tokens.append(curr_str)

            tokens.append(DollarToken())
            curr_str = ''
        elif self[index] == '\\':
            if index + 1 >= len(self) or self[index + 1] == '\\':
                curr_str += '\\'
            elif self[index + 1] == '$':
                curr_str += '$'
                
            index += 1
        else:
            curr_str += self[index]

        index += 1

    if curr_str != '':
        tokens.append(curr_str)

    result = ''

    index = 0
    while index < len(tokens):
        if isinstance(tokens[index], DollarToken):
            var_index = findany(tokens[index + 1], '[a-zA-Z0-9-_]')
            var_name = tokens[index + 1][:var_index]
            tokens[index + 1] = tokens[index + 1][var_index:]

            try:
                result += str(local_vars[var_name])
            except KeyError:
                pass
        else:
            result += tokens[index]

        index += 1

    return result

# Make string callable. Why? Why not.
str_ptr = PyObject.from_address(id(''))
str_type_ptr = str_ptr.ob_type.contents
str_type_ptr.tp_call = call
