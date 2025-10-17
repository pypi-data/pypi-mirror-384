import numpy as np

pg_stride = 720

default_float_type = np.float32
float_missing = np.float32(np.nan)
float_dne = -np.inf

default_int_type = np.int32
int_missing = -2147483648
int_dne = -2147483647

default_string_type = np.str_
string_missing = 'null'
string_dne = '-'

allowed_float_types = [np.float32, np.float64]
allowed_int_types = [np.int32, np.int64]
allowed_string_types = [np.str_, 'object']
allowed_dtypes = allowed_float_types + allowed_int_types + allowed_string_types
