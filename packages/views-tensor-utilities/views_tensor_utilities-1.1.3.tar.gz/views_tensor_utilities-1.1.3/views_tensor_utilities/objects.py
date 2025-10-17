import pandas as pd
import numpy as np
from . import defaults
from . import mappings


class ViewsDataframe():

    """
    ViewsDataframe

    Wrapper class for pandas dataframe which splits the input dataframe into numerical and string component
    dataframes and exposes methods to transform the panel data in the component dataframes into either

    - 3D time-space-feature numpy tensors for regression-type models

    - 4D longitude-latitude-time-feature numpy tensors for neural-net-type models, or visualisation

    Imported data may be cast to different data-types as required in order to optimise resources used while
    processing. How casting is done is set by a cast strategy which may be

    - to_64: all float data will be cast to np.float64, all int data will be cast to np.int64
    - to_32: all float data will be cast to np.float32, all int data will be cast to np.int32
    - none: all data retains its original dtype (only possible of data is split into individual columns)

    The dataframe may be split according to datatype using one of three split strategies:

    - float_string: all numeric data will be cast to floats with the float type controlled by the cast_strategy,
      numeric data will be separated from string data, so that a maximum of two tensors are created
    - float_int_string: separate tensors are created to hold int and float data, with the int and float types
      being controlled by the cast strategy, and a separate tensor created for string data, so that a maximum of
      three tensors is created
    - maximal: all columns of the input df are stored in separate tensors. If the cast strategy is none, these
      retain the types of the input columns, otherwise numerical data will be cast to the int or float types
      controlled by the cast strategy

    Two alternative transformation df-->tensor methods are employed:

    - for trivially tensorisable data (where for every feature, every space unit is present at
      every time unit, e.g. pgm data) numpy stride-tricks is used, which is very fast as it uses
      pointer manipulation. Missing data is represented by the default missing values defined in
      defaults.

    - for data which cannot be simply tensorised (because not all space units are present in every
      time unit, e.g. cm data) an empty tensor initialised with default does-not-exist tokens defined
      in defaults is built with dimensions (total number of time units) x (total number of space units)
      x (total number of features). Data from the dataframe is filled in, using the dataframe index
      transformed to tuples. This is slow, but acceptable for cm-level data. Units of analysis not
      present in the input data retain the does-not-exist token. The transformer throws an error
      message if the does-not-exist token is actually present in the data.

    Methods:
        __check_dtypes: check datatypes in input df can be handled correctly

        __set_default_types: set required types based on cast strategy

        __cast: do casting as required

        __split: split the input df into multiple dfs according to split strategy

        __split_by_type: split the input df by the dtypes of its columns

        __split_by_column: split the input df into one df per column

        __get_split_dftypes: generate list recording the types of all the split dfs

        to_numpy_time_space: splits dataframe data into numeric and string parts and casts to
                             numpy time-space-feature feature tensors. The tensors are returned as
                             ViewsTensor objects inside a ViewsTensorContainer object.

        to_numpy_longlat: uses to_numpy_time_space to cast input data to time-space-feature
                          tensors, then casts these to longitude-latitude-time-feature tensors.
                          Cannot be used for data which is not simply tensorisable - an error
                          will be thrown if this is attempted. The tensors are returned as
                          ViewsTensor objects inside a ViewsTensorContainer object.

    """

    def __init__(self, df, split_strategy, cast_strategy,
                 override_float_dne=None, override_float_missing=None,
                 override_int_dne=None, override_int_missing=None,
                 override_string_dne=None, override_string_missing=None,):

        self.df = df
        self.index = df.index
        self.columns = df.columns
        self.dtypes = df.dtypes
        self.split_strategy = split_strategy
        self.cast_strategy = cast_strategy

        self.override_float_dne = override_float_dne
        self.override_float_missing = override_float_missing
        self.override_int_dne = override_int_dne
        self.override_int_missing = override_int_missing
        self.override_string_dne = override_string_dne
        self.override_string_missing = override_string_missing

        self.split_dfs = []
        self.split_df_dtypes = []

        self.wanted_float_type = None
        self.wanted_int_type = None

        if mappings.is_strideable(self.index):
            self.transformer = mappings.df_to_numpy_time_space_strided
        else:
            self.transformer = mappings.df_to_numpy_time_space_unstrided

        self.__split()
        self.__get_split_df_dtypes()

        self.df = None

    def __check_data_types(self):

        """
        Check that all dtypes in the input df are in the allowed types

        """

        dtypes_set = set(self.df.dtypes)

        for dtype in dtypes_set:
            if dtype not in defaults.allowed_dtypes:
                raise RuntimeError(f'Input dtype {dtype} not in set of allowed dtypes')


    def __set_default_types(self):

        """
        Set required dtypes based on cast strategy
        """

        if self.cast_strategy == 'to_64':
            self.wanted_float_type = np.float64
            self.wanted_int_type = np.int64
        elif self.cast_strategy == 'to_32':
            self.wanted_float_type = np.float32
            self.wanted_int_type = np.int32
        elif self.cast_strategy == 'none':
            if self.split_strategy != 'maximal':
                raise RuntimeError(f'Can only have cast_strategy of none if split_strategy is maximal')
            return
        else:
            raise RuntimeError(f'Unknown cast strategy {self.cast_strategy}')

    def __cast(self):
        """
        __cast

        Cast columns in loaded df according to cast_strategy:

        'to_64' - cast all floats and ints to 64-bit

        'to_32' - cast all floats and ints to 32-bit

        'none' - leave types as they are

        """

        self.__check_data_types()

        self.__set_default_types()

        if self.cast_strategy == 'none':
            return

        for dtype in defaults.allowed_float_types:

            cols = list(self.df.select_dtypes(include=dtype))

            for col in cols:
                if self.df[col].dtypes != self.wanted_float_type:

                    self.df[col] = self.df[col].astype(self.wanted_float_type)

        for dtype in defaults.allowed_int_types:

            cols = list(self.df.select_dtypes(include=dtype))

            for col in cols:
                if self.df[col].dtypes != self.wanted_int_type:

                    self.df[col] = self.df[col].astype(self.wanted_int_type)

        return

    def __split(self):
        """
        __split

        Protected method which splits input data into numeric and string parts as a list of
        dataframes, according to the chosen split strategyÖ

        float-string: all numeric data is cast to float form, creating two tensors - float and string

        float-int-string: float and int data are separated into two tensors, with string data in a third

        maximal: every column is stored in its own tensor

        An error is thrown if the split fails to capture all the columns in the
        input dataframe.

        """

        self.__cast()

        match self.split_strategy:
            case 'float_string':
                splits = ['number', 'object']
                targets = [self.wanted_float_type, defaults.default_string_type]
                self.__split_by_type(splits, targets)
            case 'float_int_string':
                splits = [float, int, 'object']
                targets = [self.wanted_float_type, self.wanted_int_type, defaults.default_string_type]
                self.__split_by_type(splits, targets)
            case 'maximal':
                self.__split_by_column()
            case _:
                raise RuntimeError(f'unrecognized split strategy {self.split_strategy}')

    def __split_by_type(self, splits, targets):

        """
        __split_by_type

        Protected method which splits input data into parts as a list of dataframes. An error is
        thrown if the split fails to capture all the columns in the input dataframe.

        The input dataframe is then destroyed.
        """

        nsplit_columns = 0

        for split, target in zip(splits, targets):
            split_df = self.df.select_dtypes(include=split)
            try:
                split_df = split_df.astype(target)
            except:
                raise RuntimeError(f'failed to cast {split} to {target}')

            self.split_dfs.append(split_df)

            nsplit_columns += len(self.split_dfs[-1].columns)

        if nsplit_columns != len(self.df.columns):
            raise RuntimeError(f'Failed to correctly split df by dtype into {splits}')

    def __split_by_column(self):

        for column in self.df.columns:
            split_df = pd.DataFrame(self.df[column])
            self.split_dfs.append(split_df)

    def __get_split_df_dtypes(self):

        for split_df in self.split_dfs:
            split_dtypes = []
            for split_column in split_df.columns:
                for icol in range(len(self.df.columns)):
                    if split_column == list(self.df.columns)[icol]:
                        split_dtypes.append(list(self.dtypes)[icol])

            self.split_df_dtypes.append(split_dtypes)

    def to_numpy_time_space(self, broadcast_index=False):
        """
        to_numpy_time_space

        Method which splits input dataframe into numeric and string dataframes then casts the
        dataframes to time-space-feature tensors.

        broadcast_index=True causes the index of the original df to be saved in all the individual
        ViewsTensor objects

        Returns: ViewsTensorContainer object containing ViewsTensor objects

        """

        tensors = []

        for split_df, split_dtypes in zip(self.split_dfs, self.split_df_dtypes):

            if len(split_df.columns) > 0:

                dne = mappings.get_dne(split_df)
                missing = mappings.get_missing(split_df)

                default_dtype = list(set(split_df.dtypes))[0]

                if default_dtype in defaults.allowed_float_types:
                    override_dne = self.override_float_dne
                    override_missing = self.override_float_missing
                elif default_dtype in defaults.allowed_int_types:
                    override_dne = self.override_int_dne
                    override_missing = self.override_int_missing
                elif default_dtype in defaults.allowed_string_types:
                    override_dne = self.override_string_dne
                    override_missing = self.override_string_missing
                else:
                    override_dne = override_missing = None

                try:

                    tensor_time_space = self.transformer(split_df, override_dne, override_missing)

                except:
                    raise RuntimeError('failed to cast at least one df segment to tensor')

                vnt = ViewsNumpy(tensor_time_space, split_df.columns, split_dtypes, dne, missing)

                if broadcast_index:
                    vnt.index = split_df.index

                tensors.append(vnt)

        return ViewsTensorContainer(tensors, self.index)

    def to_numpy_longlat(self):

        """
        to_numpy_longlat

        Method which first casts input data to a ViewsTensorContainer object containing
        time-space-feature tensors as ViewsTensor objects.

        The tensors in the ViewsTensor objects are then cast to longitude-latitude-time-
        feature tensors and the ViewsTensorContainer object is returned.

        Cannot be used on non-simply-tensorisable dataframes.

        Returns: ViewsTensorContainer object containing ViewsTensor objects


        """

        if not(mappings.is_strideable(self.index)):
            raise RuntimeError(f'Unable to cast to long-lat - ntime x nspace != nobservations')

        tensor_container = self.to_numpy_time_space()

        for views_tensor in tensor_container.ViewsTensors:

            tensor_time_space = views_tensor.tensor

            views_tensor.tensor = mappings.numpy_time_space_to_longlat(tensor_time_space, self.index)

        return tensor_container

    def to_pytorch_time_space(self):
        pass

    def to_pytorch_lat_long_time(self):
        pass


class ViewsTensorContainer():

    """
    ViewsTensorContainer

    Wrapper class used to represent a multi-column pandas dataframe. The dataframe's data is represented
    by

    - a list of ViewsTensor objects each of which has a single datatyoe

    - the original index of the input dataframe (required if the dataframe needs to be reconstructed)

    Methods:

        get_numeric_views_tensors: extract a list of numeric (flot or int) ViewsTensors

        get_numeric_numpy_tensors: extract a list of numeric (flot or int) numpy arrays

        get_float_xxx_tensors: as above, but returns float tensors only

        get_int_xxx_tensors: as above, but returns int tensors only

        get_string_xxx_tensors: as above, but returns string tensors only

        from_views_numpy_list: creates a new ViewsTensorContainer from a list of ViewsTensor objects, merging on dtype
        where possible

        to_pandas: if tensor container contains 3D tensors, casts split tensors back to dataframes
        and recombines to a single dataframe. If 4D tensors are wrapped, returns an error.
        The cast_back flag can be set to True to cast all columsn back to their original dtypes from the inoput df.

        space_time_to_panel: performs the transformation of 3D tensors back to dataframes

    """

    def __init__(self, tensors, index):
        self.ViewsTensors = tensors
        self.index = index

        if mappings.is_strideable(self.index):
            self.transformer = mappings.time_space_to_panel_strided
        else:
            self.transformer = mappings.time_space_to_panel_unstrided

    @classmethod
    def from_views_numpy_list(cls, list_of_views_tensors):

        for itensor in range(len(list_of_views_tensors)):
            tensor_i_index_list = list_of_views_tensors[itensor].index.tolist()
            for jtensor in range(itensor, len(list_of_views_tensors)):
                if list_of_views_tensors[jtensor].index.tolist() != tensor_i_index_list:
                    raise RuntimeError(f'cannot merge tensors whose indexes differ')

        index = list_of_views_tensors[0].index

        dtype_set = set([vt.tensor.dtype for vt in list_of_views_tensors])

        merged_views_tensors = []

        for dtype in dtype_set:
            tensor_group = []
            group_columns = []
            group_dtypes = []
            group_dne = None
            group_missing = None
            for vt in list_of_views_tensors:
                if vt.tensor.dtype == dtype:
                    tensor_group.append(vt.tensor)
                    group_columns.extend(vt.columns)
                    group_dtypes.extend(vt.dtypes)
                    group_dne = vt.dne
                    group_missing = vt.missing

#                    check dne and missing

            merged_tensor = np.concatenate(tensor_group, axis=2)
            merged_views_tensors.append(ViewsNumpy(merged_tensor,
                                                   group_columns,
                                                   group_dtypes,
                                                   group_dne,
                                                   group_missing))

        tensor_container = cls(tensors=merged_views_tensors, index=index)

        return tensor_container

    def to_pandas(self, cast_back=False):

        """
        to_pandas

        Call space_time_to_panel if wrapped tensors are 3D, throws an error otherwise


        """

        if len(self.ViewsTensors[0].tensor.shape) != 3:
            raise RuntimeError(f'Not possible to cast ViewsTensorContainer to pandas unless D=3')
        else:
            return self.time_space_to_panel(cast_back)

    def time_space_to_panel(self, cast_back):

        """
        space_time_to_panel

        Casts all wrapped tensors to dataframes and combines to a single dataframe, which is returned

        """

        if len(self.ViewsTensors[0].tensor.shape) != 3:
            raise RuntimeError(f'Not possible to cast ViewsTensorContainer to pandas unless D=3')

        split_dfs = []
        for views_tensor in self.ViewsTensors:
            split_df = self.transformer(views_tensor.tensor, self.index, views_tensor.columns)

            if cast_back:
                for icolumn, column in enumerate(split_df.columns):
                    split_df[column] = split_df[column].astype(views_tensor.dtypes[icolumn])

            split_dfs.append(split_df)

        return pd.concat(split_dfs, axis=1)

    def __get_views_tensors_by_type(self, types):
        views_tensors = []
        for views_tensor in self.ViewsTensors:
            tensor = views_tensor.tensor
            if tensor.dtype in types:
                views_tensors.append(views_tensor)

        return views_tensors

    def __get_numpy_tensors_by_type(self, types):
        numpy_tensors = []
        for views_tensor in self.ViewsTensors:
            tensor = views_tensor.tensor
            if tensor.dtype in types:
                numpy_tensors.append(tensor)

        return numpy_tensors

    def get_numeric_views_tensors(self):
        """
        get_numeric_views_tensors

        Get all numeric (float and int) views tensors.

        """

        return self.__get_views_tensors_by_type(defaults.allowed_float_types+defaults.allowed_int_types)

    def get_numeric_numpy_tensors(self):
        """
        get_numeric_numpy_tensors

        Get all numeric (float and int) numpy tensors.

        """

        return self.__get_numpy_tensors_by_type(defaults.allowed_float_types+defaults.allowed_int_types)

    def get_float_views_tensors(self):
        """
        get_float_views_tensors

        Get all float views tensors.

        """

        return self.__get_views_tensors_by_type(defaults.allowed_float_types)

    def get_float_numpy_tensors(self):
        """
        get_float_numpy_tensors

        Get all float numpy tensors.

        """

        return self.__get_numpy_tensors_by_type(defaults.allowed_float_types)

    def get_int_views_tensors(self):
        """
        get_int_views_tensors

        Get all int views tensors.

        """

        return self.__get_views_tensors_by_type(defaults.allowed_int_types)

    def get_int_numpy_tensors(self):
        """
        get_int_numpy_tensors

        Get all int numpy tensors.

        """

        return self.__get_numpy_tensors_by_type(defaults.allowed_int_types)

    def get_string_views_tensors(self):
        """
        get_string_views_tensors

        Get all string views tensors.

        """
        return self.__get_views_tensors_by_type(defaults.allowed_string_types)

    def get_string_numpy_tensors(self):
        """
        get_string_numpy_tensors

        Get all string numpy tensors.

        """
        return self.__get_numpy_tensors_by_type(defaults.allowed_string_types)


class ViewsNumpy():

    """
    ViewsNumpy

    Wrapper class for a single numpy tensor. Contains

    - a single tensor
    - a list of columns detailing what the features stored in the tensor's last (i.e. 3rd or 4th
      dimension) represent
    - a list containing the columns' original dtypes, allowing them to be cast back if required
    - a dne token indicating what value in the tensor represents units-of-analysis which do not exist
      (e.g. countries that do not exist in a particular month)
    - a missing token indicating what value in then tensor represents units-of-analysis which do
      exist but have no defined value
    - (optionally) the index of the dataframe from which the tensor was built

    """

    def __init__(self, tensor, columns, dtypes, dne, missing):

        if isinstance(columns, pd.core.indexes.base.Index): columns = list(columns)
        if type(columns) is not list:columns = [columns,]
        if type(dtypes) is not list:dtypes = [dtypes, ]

        self.tensor = tensor
        self.columns = columns
        self.dtypes = dtypes
        self.dne = dne
        self.missing = missing
        self.index = None


class ViewsPytorch():

    def __init__(self):
        pass
