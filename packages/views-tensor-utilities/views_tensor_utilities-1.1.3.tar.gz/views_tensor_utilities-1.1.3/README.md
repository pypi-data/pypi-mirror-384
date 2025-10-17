# views_tensor_utilities

This package is a set of tools to allow users to transfer data in standard VIEWS format between pandas DataFrames and 
numpy arrays (referred to as tensors).

## VIEWS dataframes

VIEWS dataframes contain one or more features of panel data indexed by a two-column pandas MultiIndex. The first index 
column is a time unit (e.g. month, year) and the second is a spatial unit (most commonly country or priogrid cell). 
Missing data is, by convention, represented by NaNs.

Months currently range from 1 (Jan 1980) to 852 (December 2050). There is no month 0. Countries and priogrid cells
are denoted by non-consecutive integers. 

A crucial difference between the country and priogrid spatial units is that the identities of priogrid cells are fixed 
in time. Only cells covering landmasses are included, but these cells are always the same, so all valid cells exist for 
all time units, but **this is not the case for countries** - countries sometimes cease
to exist, or come into existence during the temporal range of a dataset. In a VIEWS dataframe, this is trivially 
represented by omitting the relevant (time-unit, space-unit) units of analysis.

Pandas dataframes are able to store numerical and string data in the same panel, with the numerical data in principle
consisting of arbitrary different data-types, e.g. float32, float64, int64.

Pandas dataframes are able to store strings giving names to the index columns and feature columns.

## VIEWS tensors

VIEWS tensors come in two forms. For the purposes of regression models, 3-dimensional tensors are used, with the 
dimensions being (time-unit, space-unit, feature). For neural-net-based models and visualisation, 4-dimensional 
tensors with dimensions (longitude-unit, latitude-unit, time-unit, feature) are used. The latter can only be 
generated from data with priogrid as its spatial unit. The integer identifying a priogrid cell can be trivially
converted into a unique (longitude, latitude) coordinate.

Tensor indices are contiguous sets of integers starting from 0. Non-existent units of analysis cannot be omitted
from tensors.

Ordinary numpy arrays cannot be used to store mixed numeric and string data.

Ordinary numpy arrays do not store names for their axes or axis values.

## Representing VIEWS dataframes as tensors

The _views_tensor_utilities_ package represents dataframes by wrappers around pure numpy arrays, accompanied by 
minimal metadata to capture essential information from the dataframe which cannot be stored in these arrays, 
such that it is possible to reconstruct the original dataframe (possibly with some reordering of the columns). 
In particular, the tokens used to represent missing data (from units of analysis that do exist, but for which no
value is recorded) and non-existent units of analysis are recorded.
Each ViewsNumpy object holds a tensor containing **only** numerical data (float or int) or **only** string data, 
the column names from the original dataframe corresponding to the data stored in the tensor, the original types 
of the data columns and the values of the tokens used to represent missing data and non-existent units of analysis.

## The ViewsDataframe class

This class holds

- a pandas dataframe
- the index of the pandas dataframe
- a list of dataframe columns
- a list of dtypes corresponding to the df columns
- a list of dataframes formed by splitting the original dataframe according to a chosen split_strategy
- a transformer function, selected according to whether the input dataframe is strideable

The methods belonging to this class are

- __check_dtypes: check datatypes in input df can be handled correctly

- __set_default_types: set required types based on cast strategy

- __cast: do casting as required

- __split: split the input df into multiple dfs according to split strategy

- __split_by_type: split the input df by the dtypes of its columns

- __split_by_column: split the input df into one df per column

- __get_split_dftypes: generate list recording the types of all the split dfs

- to_numpy_time_space: splits dataframe data into numeric and string parts and casts to numpy time-space-feature 
  tensors. The tensors are returned as ViewsTensor objects inside a ViewsTensorContainer object.

- to_numpy_longlat: uses to_numpy_time_space to cast input data to time-space-feature tensors, then casts these to 
  longitude-latitude-time-feature tensors. Cannot be used for data which is not simply tensorisable - an error will 
  be thrown if this is attempted. The tensors are returned as ViewsTensor objects inside a ViewsTensorContainer object.


### The ViewsTensorContainer class

An entire dataframe is represented by the ViewsTensorContainer class. This holds 
- a list of ViewsNumpy objects 
- the index of the original dataframe

The methods belonging to this class are

- _to_pandas_: guard method which checks whether the container tensors are 3D (which can be converted back to a 
  datafame) or 4D (which currently cannot) and respectively executes the conversion or returns an error
- _space_time_to_panel_: method which converts the containers tensors to dataframes, combines them into a single
  dataframe and returns it
- get_numeric_views_tensors: convenience method which retrieves the numeric tensor components as a list of ViewsNumpy 
  objects (see below).
- get_numeric_numpy_tensors: convenience method which retrieves the numeric tensor components as a list of numpy 
  arrays
- get_float_views_tensors: convenience method which retrieves the float tensor components as a list of ViewsNumpy 
  objects
- get_float_numpy_tensors: convenience method which retrieves the float tensor components as a list of numpy arrays
- get_int_views_tensors: convenience method which retrieves the integer tensor components as a list of ViewsNumpy 
  objects
- get_int_numpy_tensors: convenience method which retrieves the integer tensor components as a list of numpy arrays
- get_string_views tensors: convenience method which retrieves the string tensor components as a list of ViewsNumpy 
  objects
- get_string_views tensors: convenience method which retrieves the string tensor components as a list of numpy arrays

### The ViewsNumpy class

This is a simple wrapper for a single numpy tensor containing numeric or string data. It holds
- a numpy array representing a 3D time-space-feature tensor or a 4d longitude-latitude-time-feature tensor
- a list of columns names corresponding to the indices of the tensor's last (i.e. 3rd or 4th) dimension
- a list of dtypes giving the original types of the columns stored in the tensor
- a value for the does-not-exist token used to denote units-of-analysis that do not exist
- a value for the missing token denoting legal units-of-analysis with undefined values

This class has no methods.

# Examples

## Converting a VIEWS dataframe into tensors

This is done by instantiating the ViewsDataframe class. A split strategy and a cast strategy must also be supplied. 
To create a container that groups all numeric columns into one 64-bit float tensor and all string columns into a
second tensor, one would do

```
views_dataframe = objects.ViewsDataframe(df, split_strategy='float_string', cast_strategy='to_64)
```
The command
```
tensor_container=views_dataframe.to_numpy_time_space()
```
generates a tensor container containing one or more ViewsNumpy objects wrapping the numeric and/or string
portions of the dataframe's data. 

## Splitting

Instantiating the ViewsTensorContainer object splits the input dataframe into several smaller dataframes based on the
specified cast strategy. 'float_int_string' sorts all the columns in the input df into three classes. 'float_string'
lumps float and int columns together into a single float tensor, leaving string columns in a separate tensor. 
'maximal' creates one dataframe for every column in the input df.

## Data types

The _views_tensor_utilities_ package currently supports the following data types: np.float64, np.float32, np.int64, 
np.int32, np.str_, 'object'

Numeric data can be cast to different types if required by setting the cast strategy. 'to_64' casts all floats ints to 
64-bit, 'to_32' casts them all to 32-bit, 'none' does not do any casting, and can only be used if the split strategy 
is 'maximal', so that every column may retain its original type.

## Missingness token

The default missingness tokens are defined by defaults.fmissing (for numerical data, set to np.nan) and 
defaults.smissing (for string data, set to 'null').

The default missingness token for numerical data can be overridden when instantiating the ViewsDataframe class 
using the 'override_xxx_missing' keywords in the call to the constructor, e.g.
```
views_dataframe = objects.ViewsDataframe(df, split_strategy='float_string', cast_strategy='to_64, 
override_float_missing=-1e20, override_int_missing=-1)
```
This has no effect on string data.

This functionality was included for reasons of flexibility but **its use is STRONGLY DISCOURAGED**, particularly in
the context of the views_data_service. In particular **many of the transforms in the views-transformation-library 
will cease to work correctly if the missingness token is anything other than np.nan**.

## Does-not-exist token

Some VIEWS units of analysis, e.g. country-month, have values that do not exist, e.g. the Soviet Union in January 
2024 . Such units of analysis cannot be omitted from tensors. They also must not be confused with units of analysis
which do exist but have no data, which are marked with the missingness token. These units of analysis are marked
with a 'does-not-exist' token, defined for numeric and string data by defaults.fdne and defaults.sdne.

The default does-not-exist token for numerical data can be overridden when instantiating the ViewsDataframe class 
using the 'override_dne' keyword in the call to the constructor, e.g.
```
views_dataframe = objects.ViewsDataframe(df, split_strategy='float_string', cast_strategy='to_64, 
override_float_dne=-1e20, override_int_dne=-1)
```
This has no effect on string data.

Note that integer numpy arrays CANNOT store the value np.nan, so this cannot be used as a missingness token or a dne
token in int arrays.

## Accessing the tensors in a ViewsTensorContainer

The tensors wrapped in a container can be accessed by 
```
tensor=tensor_container.ViewsTensors[0].tensor
```
Alternatively, the convenience methods can be used
```
tensor=tensor_container.get_numeric_tensors()
```
or
```
tensor=tensor_container.get_string_tensors()
```

## Converting a ViewsTensorContainer into a pandas DataFrame

This is done by calling the container's to_pandas method:

```
df=tensor_container.to_pandas()
```
Note that the columns in the regenerated dataframe will likely not be in the same order as in the original
dataframe.
If required, the optional 'cast_back' flag can be set to True to cast all columns back to their original dtypes from 
the input df.