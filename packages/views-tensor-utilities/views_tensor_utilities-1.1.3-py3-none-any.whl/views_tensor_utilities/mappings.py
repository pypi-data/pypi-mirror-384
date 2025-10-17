import numpy as np
import pandas as pd
from . import defaults
from . import objects


class TimeUnits():

    """
    TimeUnits

    Class which generates and holds a set of time indices and two dictionaries to quickly transform
    between them.

    A factory method to build instances from pandas dataframes or multindexes is included

    """

    def __init__(self, times, index_to_time, time_to_index):
        self.times = times
        self.index_to_time = index_to_time
        self.time_to_index = time_to_index

    @classmethod
    def from_pandas(cls, pandas_object):

        index = get_index(pandas_object)

        # get unique times

        times = np.array(list({idx[0] for idx in index.values}))
        times = list(np.sort(times))

        # make dicts to transform between times and the index of a time in the list

        time_to_index = {}
        index_to_time = {}
        for i, time in enumerate(times):
            time_to_index[time] = i
            index_to_time[i] = time

        time_units = cls(times=times, time_to_index=time_to_index, index_to_time=index_to_time)

        return time_units


class SpaceUnits():
    """
    SpaceUnits

    Class which generates and holds a set of space indices and two dictionaries to quickly transform
    between them.

    A factory method to build instances from pandas dataframes or multindexes is included

    """

    def __init__(self, spaces, index_to_space, space_to_index):
        self.spaces = spaces
        self.index_to_space = index_to_space
        self.space_to_index = space_to_index

    @classmethod
    def from_pandas(cls, pandas_object):

        index = get_index(pandas_object)

        spaces = np.array(list({idx[1] for idx in index.values}))

        spaces = np.sort(spaces)

        space_to_index = {}
        index_to_space = {}

        for i, space_id in enumerate(spaces):
            space_to_index[space_id] = i
            index_to_space[i] = space_id

        space_units = cls(spaces=spaces, space_to_index=space_to_index, index_to_space=index_to_space)

        return space_units


class LonglatUnits():
    """
    LonglatUnits

    Class which generates and holds a set of space indices, a set of matching longitude-latitude
    tuples and dictionaries to quickly transform between them.

    A factory method to build instances from pandas dataframes or multindexes is included

    """

    def __init__(self,
                 pgids,
                 pgid_to_longlat,
                 longlat_to_pgid,
                 pgid_to_index,
                 index_to_pgid,
                 longrange,
                 latrange,
                 gridsize,
                 power):

        self.pgids = pgids
        self.pgid_to_longlat = pgid_to_longlat
        self.longlat_to_pgid = longlat_to_pgid
        self.pgid_to_index = pgid_to_index
        self.index_to_pgid = index_to_pgid
        self.longrange = longrange
        self.latrange = latrange
        self.gridsize = gridsize
        self.power = power

    @classmethod
    def from_pandas(cls, pandas_object):
        """
        from_pandas

        Factory method which builds class instances from pandas dataframes or multiindexes

        """

        index = get_index(pandas_object)

        pgids = np.array(list({idx[1] for idx in index.values}))
        pgids = np.sort(pgids)

        # convert pgids to longitudes and latitudes

        longitudes = pgids % defaults.pg_stride
        latitudes = pgids // defaults.pg_stride

        latmin = np.min(latitudes)
        latmax = np.max(latitudes)
        longmin = np.min(longitudes)
        longmax = np.max(longitudes)

        latrange = latmax - latmin
        longrange = longmax - longmin

        # shift to a set of indices that starts at [0,0]

        latitudes -= latmin
        longitudes -= longmin

        # find smallest possible square grid with side 2^ncells which will fit the pgids

#        latmin = np.min(latitudes)
        latmax = np.max(latitudes)
#        longmin = np.min(longitudes)
        longmax = np.max(longitudes)

        maxsize = np.max((longrange, latrange))
        power = 1 + int(np.log2(maxsize))

        gridsize = 2 ** power

        # centre the pgids

        inudgelong = int((gridsize - longmax) / 2)
        inudgelat = int((gridsize - latmax) / 2)

        longitudes += inudgelong
        latitudes += inudgelat

        # make dicts to transform between pgids and (long,lat) coordinate

        pgid_to_longlat = {}
        longlat_to_pgid = {}

        pgid_to_index = {}
        index_to_pgid = {}

        for i, pgid in enumerate(pgids):
            pgid_to_longlat[pgid] = (longitudes[i], latitudes[i])
            longlat_to_pgid[(longitudes[i], latitudes[i])] = pgid
            pgid_to_index[pgid] = i
            index_to_pgid[i] = pgid

        longlat_units = cls(pgids=pgids,
                            pgid_to_longlat=pgid_to_longlat,
                            longlat_to_pgid=longlat_to_pgid,
                            pgid_to_index=pgid_to_index,
                            index_to_pgid=index_to_pgid,
                            longrange=longrange,
                            latrange=latrange,
                            gridsize=gridsize,
                            power=power)

        return longlat_units


class TimeSpaceIndices():
    """
    TimeSpaceUnits

    Class which generates and holds a set of time and space indices and a list of tuples,
    derived from a pandas df or multiindex.

    A factory method to build instances from pandas dataframes or multindexes is included

    """

    def __init__(self, time_indices, space_indices, index_tuples, ntime, nspace, nrow):
        self.time_indices = time_indices
        self.space_indices = space_indices
        self.index_tuples = index_tuples
        self.ntime = ntime
        self.nspace = nspace
        self.nrow = nrow

    @classmethod
    def from_pandas(cls, pandas_object):
        """
        from_pandas

        Factory method which builds class instances from pandas dataframes or multiindexes

        """

        index = get_index(pandas_object)

        time_indices = index.levels[0].to_list()
        space_indices = index.levels[1].to_list()

        index_tuples = index.to_list()

        time_space_indices = cls(time_indices=time_indices, space_indices=space_indices,
                                 index_tuples=index_tuples, ntime=len(time_indices),
                                 nspace=len(space_indices), nrow=len(index_tuples))

        return time_space_indices


def is_strideable(pandas_object):

    """
    is_strideable

    Function which accepts a pandas df or multindex and determines if data indexed with that index
    can be strided.

    """

    time_space = TimeSpaceIndices.from_pandas(pandas_object)

    if time_space.nrow == time_space.ntime * time_space.nspace:
        return True
    else:
        return False


def get_index(pandas_object):

    """
    get_index

    Given either a df or a df index, return the index

    :param pandas_object:
    :return: index

    """

    if isinstance(pandas_object, pd.DataFrame):
        index = pandas_object.index
    elif isinstance(pandas_object, pd.MultiIndex):
        index = pandas_object
    else:
        raise RuntimeError(f'Input is not a df or a df index')

    return index


def __check_df_data_types(df):
    """
    check_df_data_types

    Check that there is only one data type in the input dataframe, and that it is in the set of allowed
    data types
    """

    dtypes_set = set(df.dtypes)

    if len(dtypes_set) != 1:
        raise RuntimeError(f'df with multiple dtypes passed: {list(df.dtypes)}')

    dtype = list(dtypes_set)[0]

    if dtype not in defaults.allowed_dtypes:
        raise RuntimeError(f'dtype {dtype} not in allowed dtypes: {defaults.allowed_dtypes}')

    return dtype


def __check_default_dtypes():
    """
    check_default_dtypes

    Check that the default datatypes defined in defaults can be handled by the rest of the package

    """

    if defaults.default_float_type not in defaults.allowed_dtypes:
        raise RuntimeError(f'default dtype {defaults.default_float_type} '
                           f'not in allowed dtypes: {defaults.allowed_dtypes}')

    if defaults.default_int_type not in defaults.allowed_dtypes:
        raise RuntimeError(f'default dtype {defaults.default_int_type} '
                           f'not in allowed dtypes: {defaults.allowed_dtypes}')

    if defaults.default_string_type not in defaults.allowed_dtypes:
        raise RuntimeError(f'default dtype {defaults.default_string_type} '
                           f'not in allowed dtypes: {defaults.allowed_dtypes}')


def __check_cast_to_dtypes(dtype):
    """
    check_cast_to_dtypes

    Check that the requested datatypes can be handled by the rest of the package

    """

    if dtype not in defaults.allowed_dtypes:
        raise RuntimeError(f'requested dtype {dtype} not in allowed dtypes: {defaults.allowed_dtypes}')


def get_dne(df):
    """
    get_dne

    Obtain correct does-not-exist token based on data type of input dataframe
    """

    dtype = __check_df_data_types(df)

    if dtype in defaults.allowed_float_types:
        return defaults.float_dne
    elif dtype in defaults.allowed_int_types:
        return defaults.int_dne
    else:
        max_str_length = 1
        for column in df.columns:
            if df[column].dtype in defaults.allowed_string_types:
                try:
                    max_str_length = np.max([max_str_length, len(max(np.ndarray.flatten(df[column].values), key=len))])
                except:
                    pass

        return max_str_length*defaults.string_dne


def __get_tensor_dne(tensor):

    dtype = tensor.dtype

    if dtype in defaults.allowed_float_types:
        return defaults.float_dne
    elif dtype in defaults.allowed_int_types:
        return defaults.int_dne
    else:
        max_str_length = len(max(np.ndarray.flatten(tensor), key=len))
        return max_str_length * defaults.string_dne


def get_missing(df):
    """
    get_missing

    Obtain correct missing token based on data type of input dataframe
    """

    dtype = __check_df_data_types(df)

    if dtype in defaults.allowed_float_types:
        return defaults.float_missing
    elif dtype in defaults.allowed_int_types:
        return defaults.int_missing
    else:
        return defaults.string_missing


def __get_dtype(df):
    """
    get_dtype

    Obtain correct output datatype based on data type of input dataframe
    """

    dtype = __check_df_data_types(df)
    __check_default_dtypes()

    if dtype in defaults.allowed_float_types:
        return dtype
    elif dtype in defaults.allowed_int_types:
        return dtype
    else:
        return dtype


def df_to_numpy_time_space_strided(df, override_dne=None, override_missing=None):

    """
    df_to_numpy_time_space_strided

    Convert panel dataframe to numpy time-space-feature tensor using stride-tricks

    """

    dtype = __get_dtype(df)

    if override_dne is None:
        dne = get_dne(df)
    else:
        dne = override_dne

    for column in df.columns:
        if dne in df[column].values:
            raise RuntimeError(f'does-not-exist token {dne} found in input column {column}')

    # get shape of dataframe

    dim0, dim1 = df.index.levshape

    dim2 = df.shape[1]

    # check that df can in principle be tensorised

    if dim0 * dim1 != df.shape[0]:
        raise Exception("df cannot be cast to a tensor - dim0 * dim1 != df.shape[0]",
                        dim0, dim1, df.shape[0])

    flat = df.to_numpy().astype(dtype)

    # get strides (in bytes) of flat array
    flat_strides = flat.strides

    offset2 = flat_strides[1]

    offset1 = flat_strides[0]

    # compute stride in bytes along dimension 0
    offset0 = dim1 * offset1

    # get memory view or copy as a numpy array
    tensor_time_space = np.lib.stride_tricks.as_strided(flat, shape=(dim0, dim1, dim2),
                                                        strides=(offset0, offset1, offset2))

    if override_missing is not None:
        tensor_time_space = np.where(np.isnan(tensor_time_space), override_missing, tensor_time_space)

    return tensor_time_space


def df_to_numpy_time_space_unstrided(df, override_dne=None, override_missing=None):
    """
    df_to_numpy_time_space_unstrided

    Convert panel dataframe to numpy time-space-feature tensor without using stride-tricks
    (for panels which are not simply-tensorisable)

    """

    dtype = __get_dtype(df)

    if override_dne is None:
        dne = get_dne(df)
    else:
        dne = override_dne

    time_space = TimeSpaceIndices.from_pandas(df)

    nfeature = len(df.columns)

    for column in df.columns:
        if dne in df[column].values:
            raise RuntimeError(f'does-not-exist token {dne} found in input column {column}')

    if dtype in defaults.allowed_float_types+defaults.allowed_int_types:
        tensor_time_space = np.full((time_space.ntime, time_space.nspace, nfeature), dne, dtype=dtype)
    else:
        tensor_time_space = np.full((time_space.ntime, time_space.nspace, nfeature), dne)

    for irow in range(time_space.nrow):
        idx = time_space.index_tuples[irow]
        itime = time_space.time_indices.index(idx[0])
        ispace = time_space.space_indices.index(idx[1])
        tensor_time_space[itime, ispace, :] = df.values[irow]

    if override_missing is not None:
        tensor_time_space = np.where(np.isnan(tensor_time_space), override_missing, tensor_time_space)

    return tensor_time_space


def numpy_time_space_to_longlat(tensor_time_space, pandas_object, override_dne=None, override_missing=None):
    """
    numpy time_space_to_longlat

    Convert numpy time-space-feature tensor to a longitude-latitude-time-space tensor using
    stride-tricks
    """

    dtype = tensor_time_space.dtype

    if override_dne is None:
        dne = __get_tensor_dne(tensor_time_space)
    else:
        dne = override_dne

    time_units = TimeUnits.from_pandas(pandas_object)
    longlat_units = LonglatUnits.from_pandas(pandas_object)

    # convert 3d tensor into longitude x latitude x time x feature tensor

    tensor_longlat = np.full((longlat_units.gridsize,
                             longlat_units.gridsize,
                             len(time_units.times),
                             tensor_time_space.shape[-1]),
                             dne,
                             dtype=dtype)

    for pgid in longlat_units.pgids:

        pgindex = longlat_units.pgid_to_index[pgid]
        for time in time_units.times:
            tindex = time_units.time_to_index[time]
            ilong = longlat_units.pgid_to_longlat[pgid][0]
            ilat = longlat_units.pgid_to_longlat[pgid][1]

            tensor_longlat[ilong, ilat, tindex, :] = tensor_time_space[tindex, pgindex, :]

    if override_missing is not None:
        tensor_longlat = np.where(np.isnan(tensor_longlat), override_missing, tensor_time_space)

    return tensor_longlat


def time_space_to_panel_unstrided(tensor, index, columns):

    """
    time_space_to_panel_unstrided

    Convert numpy time-space-feature tensor to dataframe without using stride-tricks
    """

    dne = __get_tensor_dne(tensor)

    time_space = TimeSpaceIndices.from_pandas(index)

    nfeature = tensor.shape[-1]

    data = np.full((time_space.nrow, nfeature), dne)

    for irow, row in enumerate(time_space.index_tuples):
        idx = time_space.index_tuples[irow]
        itime = time_space.time_indices.index(idx[0])
        ispace = time_space.space_indices.index(idx[1])
        data[irow, :] = tensor[itime, ispace, :]

    return pd.DataFrame(data=data, index=index, columns=columns)


def time_space_to_panel_strided(tensor, index, columns):
    """
    time_space_to_panel_strided

    Convert numpy time-space-feature tensor to dataframe using stride-tricks
    """

    time_space = TimeSpaceIndices.from_pandas(index)

    nfeature = tensor.shape[-1]

    tensor_strides = tensor.strides

    offset2 = tensor_strides[2]

    offset1 = tensor_strides[1]

    flat = np.lib.stride_tricks.as_strided(tensor, shape=(time_space.ntime * time_space.nspace, nfeature),
                                           strides=(offset1, offset2))

    return pd.DataFrame(flat, index=index, columns=columns)


def merge_views_tensors_to_views_tensor(list_of_views_tensors, cast_to=None, cast_to_dne=None, cast_to_missing=None):

    """
    merge_views_tensors_to_views_tensor

    Merge list of views tensors by type to produce a single views tensor

    :param list_of_views_tensors: list of ViewsTensor objects
    :param cast_to: dtype to cast ViewsTensor.tensor to
    :param cast_to_dne: dne token to use in casted tensor
    :param cast_to_missing: missing tokent o use in casted tensor
    :return: single views tensor
    """

    for itensor in range(len(list_of_views_tensors)):
        tensor_i_index_list = list_of_views_tensors[itensor].index.tolist()
        for jtensor in range(itensor, len(list_of_views_tensors)):
            if list_of_views_tensors[jtensor].index.tolist() != tensor_i_index_list:
                raise RuntimeError(f'cannot merge tensors whose indexes differ')

    dtype_list = [vt.tensor.dtype for vt in list_of_views_tensors]

    dtype_set = set(dtype_list)

    if len(dtype_set) != 1:
        if cast_to is None:
            raise RuntimeError(f'cannot merge tensors with different dtypes: {dtype_set}')
        else:
            casted_tensors = []
            for vt in list_of_views_tensors:
                if vt.tensor.dtype is np.dtype(cast_to):
                    casted_tensors.append(vt)
                else:
                    try:
                        from_dne = vt.dne
                        from_missing = vt.missing

                        casted_tensor = np.empty_like(vt.tensor, dtype=cast_to)

                        if np.isnan(from_dne):
                           dne_mask = np.isnan(vt.tensor)
                        else:
                           dne_mask = vt.tensor == from_dne

                        if np.isnan(from_missing):
                            missing_mask = np.isnan(vt.tensor)
                        else:
                            missing_mask = vt.tensor == from_missing

                        values_mask = np.logical_not(np.logical_or(dne_mask, missing_mask))

                        casted_tensor[values_mask] = vt.tensor[values_mask]
                        casted_tensor[dne_mask] = cast_to_dne
                        casted_tensor[missing_mask] = cast_to_missing

                        casted_views_tensor = objects.ViewsNumpy(casted_tensor, vt.columns, vt.dtypes, cast_to_dne,
                                                                 cast_to_missing)

                        casted_tensors.append(casted_views_tensor)
                    except:
                        raise RuntimeError(f'tensor with type {vt.tensor.dtype}, dne {from_dne} could not be cast to '
                                           f'{cast_to}')

    else:
        casted_tensors = list_of_views_tensors

    list_of_views_tensors = casted_tensors

    dne_list = [vt.dne for vt in list_of_views_tensors]

    dne_set = set(dne_list)

    if len(dne_set) != 1:
        if not np.isnan(dne_list).all():
            raise RuntimeError(f'cannot merge tensors with different dnes: {dne_set}')

    missing_list = [vt.missing for vt in list_of_views_tensors]

    missing_set = set(missing_list)

    if len(missing_set) != 1:
        if not np.isnan(missing_list).all():
            raise RuntimeError(f'cannot merge tensors with different missingness tokens: {missing_set}')

    merged_columns = []
    merged_index = list_of_views_tensors[0].index
    merged_dtypes = []
    merged_dne = dne_list[0]
    merged_missing = missing_list[0]

    for vt in list_of_views_tensors:
        merged_columns.extend(vt.columns)
        merged_dtypes.extend(vt.dtypes)

    merged_tensor = np.concatenate([vt.tensor for vt in list_of_views_tensors], axis=2)

    views_tensor = objects.ViewsNumpy(merged_tensor, merged_columns, merged_dtypes, merged_dne, merged_missing)
    views_tensor.index = merged_index

    return views_tensor
