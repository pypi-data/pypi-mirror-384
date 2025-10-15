from __future__ import annotations

import os
import h5py
import numpy as np
import numbers
import pandas as pd
import datetime
import time

from ..src import object_handler
import gc


def close_all_hdf5_file():
    """
    Close all hdf5 file opened in the current session
    """

    for obj in gc.get_objects():  # Browse through ALL objects
        if isinstance(obj, h5py.File):  # Just HDF5 files
            try:
                print(f"try closing {obj}")
                obj.close()
            except:
                pass  # Was already closed


def open_hdf5(path, read_only=False, replace=False, wait_time=0):
    """

    Open or create an HDF5 file.

    Parameters
    ----------

    path : str
        The file path.

    read_only : boolean
        If true the access to the hdf5 fil is in read-only mode. Multi process can read the same hdf5 file simulteneously. This is not possible when access mode are append 'a' or write 'w'.

    replace: Boolean
        If true, the existing hdf5file is erased

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Returns
    -------

    f :
        A h5py object.

    Examples
    --------

    >>> hdf5=pyhdf5_handler.open_hdf5("./my_hdf5.hdf5")
    >>> hdf5.keys()
    >>> hdf5.attrs.keys()

    """
    f = None
    wait = 0
    while wait <= wait_time:

        f = None
        exist_file = True

        try:

            if read_only:
                if os.path.isfile(path):
                    f = h5py.File(path, "r")

                else:
                    exist_file = False
                    raise ValueError(f"File {path} does not exist.")

            else:
                if replace:
                    f = h5py.File(path, "w")

                else:
                    if os.path.isfile(path):
                        f = h5py.File(path, "a")

                    else:
                        f = h5py.File(path, "w")
        except:
            pass

        if f is None:
            if not exist_file:
                print(f"File {path} does not exist.")
                return f
            else:
                print(f"The file {path} is unvailable, waiting {wait}/{wait_time}s")

            wait = wait + 1

            if wait_time > 0:
                time.sleep(1)

        else:
            break

    return f


def add_hdf5_sub_group(hdf5, subgroup=None):
    """
    Create a new subgroup in a HDF5 object

    Parameters
    ----------

    hdf5 : h5py.File
        An hdf5 object opened with open_hdf5()

    subgroup: str
        Path to a subgroub that must be created

    Returns
    -------

    hdf5 :
        the h5py object.

    Examples
    --------

    >>> hdf5=pyhdf5_handler.open_hdf5("./model_subgroup.hdf5", replace=True)
    >>> hdf5=pyhdf5_handler.add_hdf5_sub_group(hdf5, subgroup="mygroup")
    >>> hdf5.keys()
    >>> hdf5.attrs.keys()

    """
    if subgroup is not None:
        if subgroup == "":
            subgroup = "./"

        hdf5.require_group(subgroup)

    return hdf5


def _dump_object_to_hdf5_from_list_attribute(hdf5, instance, list_attr):
    """
    dump a object to a hdf5 file from a list of attributes

    Parameters
    ----------
    hdf5 : h5py.File
        an hdf5 object

    instance : object
        a custom python object.

    list_attr : list
        a list of attribute

    """
    if isinstance(list_attr, list):
        for attr in list_attr:
            if isinstance(attr, str):
                _dump_object_to_hdf5_from_str_attribute(hdf5, instance, attr)

            elif isinstance(attr, list):
                _dump_object_to_hdf5_from_list_attribute(hdf5, instance, attr)

            elif isinstance(attr, dict):
                _dump_object_to_hdf5_from_dict_attribute(hdf5, instance, attr)

            else:
                raise ValueError(
                    f"inconsistent {attr} in {list_attr}. {attr} must be a an instance of dict, list or str"
                )

    else:
        raise ValueError(f"{list_attr} must be a instance of list.")


def _dump_object_to_hdf5_from_dict_attribute(hdf5, instance, dict_attr):
    """
    dump a object to a hdf5 file from a dictionary of attributes

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object

    instance : object
        a custom python object.

    dict_attr : dict
        a dictionary of attribute

    """
    if isinstance(dict_attr, dict):
        for attr, value in dict_attr.items():
            hdf5 = add_hdf5_sub_group(hdf5, subgroup=attr)

            try:
                sub_instance = getattr(instance, attr)

            except:
                if isinstance(instance, dict):
                    sub_instance = instance[attr]
                else:
                    sub_instance = instance

            if isinstance(value, dict):
                _dump_object_to_hdf5_from_dict_attribute(hdf5[attr], sub_instance, value)

            elif isinstance(value, list):
                _dump_object_to_hdf5_from_list_attribute(hdf5[attr], sub_instance, value)

            elif isinstance(value, str):
                _dump_object_to_hdf5_from_str_attribute(hdf5[attr], sub_instance, value)

            else:

                raise ValueError(
                    f"inconsistent '{attr}' in '{dict_attr}'. Dict({attr}) must be a instance of dict, list or str"
                )

    else:
        raise ValueError(f"{dict_attr} must be a instance of dict.")


def _dump_object_to_hdf5_from_str_attribute(hdf5, instance, str_attr):
    """
    dump a object to a hdf5 file from a string attribute

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object

    instance : object
        a custom python object.

    str_attr : str
        a string attribute

    """

    if isinstance(str_attr, str):

        try:
            value = getattr(instance, str_attr)

        except:
            if isinstance(instance, dict):
                value = instance[str_attr]
            else:
                value = instance

        try:

            attribute_name = str(str_attr)
            for character in "/ ":
                attribute_name = attribute_name.replace(character, "_")

            if isinstance(value, dict):

                # print("---> dictionary: ", str_attr, value)

                hdf5 = add_hdf5_sub_group(hdf5, subgroup=attribute_name)
                save_dict_to_hdf5(hdf5[attribute_name], value)

            else:

                hdf5_dataset_creator(hdf5, attribute_name, value)

        except:
            raise ValueError(
                f"Unable to dump attribute {str_attr} with value {value} from {instance}"
            )

    else:
        raise ValueError(f"{str_attr} must be a instance of str.")


def _dump_object_to_hdf5_from_iteratable(hdf5, instance, iteratable=None):
    """
       dump a object to a hdf5 file from a iteratable object list or dict

       Parameters
       ----------

       hdf5 : h5py.File
           an hdf5 object
       instance : object
           a custom python object.
       iteratable : list | dict
           a list or a dict of attribute

       Examples
       --------

       >>> setup, mesh = smash.load_dataset("cance")
       >>> model = smash.Model(setup, mesh)
       >>> model.run(inplace=True)
       >>>
       >>> hdf5=pyhdf5_handler.open_hdf5("./model.hdf5", replace=True)
       >>> hdf5=pyhdf5_handler.add_hdf5_sub_group(hdf5, subgroup="model1")
    pyhdf5_handler._dump_object_to_hdf5_from_iteratable(hdf5["model1"], model)

    """
    if isinstance(iteratable, list):
        _dump_object_to_hdf5_from_list_attribute(hdf5, instance, iteratable)

    elif isinstance(iteratable, dict):
        _dump_object_to_hdf5_from_dict_attribute(hdf5, instance, iteratable)

    else:
        raise ValueError(f"{iteratable} must be a instance of list or dict.")


def _hdf5_handle_str(name, value):

    dataset = {
        "name": name,
        "attr_value": str(type(value)),
        "dataset_value": value,
        "shape": 1,
        "dtype": h5py.string_dtype(encoding="utf-8"),
    }

    return dataset


def _hdf5_handle_numbers(name: str, value: numbers.Number):

    arr = np.array([value])
    dataset = {
        "name": name,
        "attr_value": str(type(value)),
        "dataset_value": arr,
        "shape": arr.shape,
        "dtype": arr.dtype,
    }

    return dataset


def _hdf5_handle_none(name: str, value: None):

    dataset = {
        "name": name,
        "attr_value": "_None_",
        "dataset_value": "_None_",
        "shape": 1,
        "dtype": h5py.string_dtype(encoding="utf-8"),
    }

    return dataset


def _hdf5_handle_timestamp(
    name: str, value: pd.Timestamp | np.datetime64 | datetime.date
):

    dtype = type(value)

    if isinstance(value, (np.datetime64)):
        value = value.tolist()

    dataset = {
        "name": name,
        "attr_value": str(dtype),
        "dataset_value": value.strftime("%Y-%m-%d %H:%M"),
        "shape": 1,
        "dtype": h5py.string_dtype(encoding="utf-8"),
    }

    return dataset


def _hdf5_handle_DatetimeIndex(name: str, value: pd.DatetimeIndex):

    dataset = _hdf5_handle_array(name, value)

    return dataset


def _hdf5_handle_list(name: str, value: list | tuple):

    arr = np.array(value)

    dataset = _hdf5_handle_array(name, arr)

    return dataset


def _hdf5_handle_array(name: str, value: np.ndarray):

    dtype_attr = type(value)
    dtype = value.dtype

    if value.dtype.char == "M":

        ListDate = value.tolist()
        ListDateStr = list()
        for date in ListDate:
            ListDateStr.append(date.strftime("%Y-%m-%d %H:%M"))
        value = np.array(ListDateStr)
        value = value.astype("O")
        dtype = h5py.string_dtype(encoding="utf-8")

    elif value.dtype == "object":

        value = value.astype("S")
        dtype = h5py.string_dtype(encoding="utf-8")

    elif value.dtype.char == "U":
        value = value.astype("S")
        dtype = h5py.string_dtype(encoding="utf-8")

    dataset = {
        "name": name,
        "attr_value": str(dtype_attr),
        "dataset_value": value,
        "shape": value.shape,
        "dtype": dtype,
    }

    return dataset


def _hdf5_handle_ndarray(hdf5: h5py.File, name: str, value: np.ndarray):

    hdf5 = add_hdf5_sub_group(hdf5, subgroup=name)
    _dump_ndarray_to_hdf5(hdf5[name], value)


def _hdf5_create_dataset(hdf5: h5py.File, dataset: dict):

    if dataset["name"] in hdf5.keys():
        del hdf5[dataset["name"]]

    hdf5.create_dataset(
        dataset["name"],
        shape=dataset["shape"],
        dtype=dataset["dtype"],
        data=dataset["dataset_value"],
        compression="gzip",
        chunks=True,
    )

    if "_" + dataset["name"] in list(hdf5.attrs.keys()):
        del hdf5.attrs["_" + dataset["name"]]

    hdf5.attrs["_" + dataset["name"]] = dataset["attr_value"]


def hdf5_dataset_creator(hdf5: h5py.File, name: str, value):
    """
    Write any value in an hdf5 object

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object

    name : str
        name of the dataset

    value : any
        value to write in the hdf5

    """
    # save ndarray datast
    if isinstance(value, str):
        dataset = _hdf5_handle_str(name, value)

    elif isinstance(value, numbers.Number):
        dataset = _hdf5_handle_numbers(name, value)

    elif value is None:
        dataset = _hdf5_handle_none(name, value)

    elif isinstance(value, (pd.Timestamp, np.datetime64, datetime.date)):
        dataset = _hdf5_handle_timestamp(name, value)

    elif isinstance(value, pd.DatetimeIndex):
        dataset = _hdf5_handle_DatetimeIndex(name, value)

    elif isinstance(value, list):
        dataset = _hdf5_handle_list(name, value)

    elif isinstance(value, tuple):
        dataset = _hdf5_handle_list(name, value)

    elif isinstance(value, np.ndarray):

        if len(value.dtype) > 0 and len(value.dtype.names) > 0:
            _hdf5_handle_ndarray(hdf5, name, value)
            return
        else:
            dataset = _hdf5_handle_array(name, value)

    else:

        hdf5 = add_hdf5_sub_group(hdf5, subgroup=name)

        newdict = object_handler.read_object_as_dict(value)

        save_dict_to_hdf5(hdf5[name], newdict)

    _hdf5_create_dataset(hdf5, dataset)


def _dump_ndarray_to_hdf5(hdf5, value):
    """
    dump a ndarray data structure to an hdf5 file: this functions create a group ndarray_ds and store each component of the ndarray as a dataset. Plus it add 2 datasets which store the dtypes (ndarray_dtype) and labels (ndarray_indexes).

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object

    value : ndarray
        an ndarray data structure with different datatype

    """
    # save ndarray datastructure

    hdf5 = add_hdf5_sub_group(hdf5, subgroup="ndarray_ds")
    hdf5_data = hdf5["ndarray_ds"]

    for item in value.dtype.names:

        hdf5_dataset_creator(hdf5=hdf5_data, name=item, value=value[item])

    index = np.array(value.dtype.descr)[:, 0]
    dtype = np.array(value.dtype.descr)[:, 1]
    index = index.astype("O")
    dtype = dtype.astype("O")
    data_type = h5py.string_dtype(encoding="utf-8")

    if "ndarray_dtype" in hdf5_data.keys():
        del hdf5_data["ndarray_dtype"]

    hdf5_data.create_dataset(
        "ndarray_dtype",
        shape=dtype.shape,
        dtype=data_type,
        data=dtype,
        compression="gzip",
        chunks=True,
    )

    if "ndarray_indexes" in hdf5_data.keys():
        del hdf5_data["ndarray_indexes"]

    hdf5_data.create_dataset(
        "ndarray_indexes",
        shape=index.shape,
        dtype=data_type,
        data=index,
        compression="gzip",
        chunks=True,
    )


def _read_ndarray_datastructure(hdf5):
    """
    read a ndarray data structure from hdf5 file

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object at the roots of the ndarray datastructure

    Return
    ------

    ndarray : the ndarray

    """

    if "ndarray_ds" in list(hdf5.keys()):

        decoded_item = list()
        for it in hdf5["ndarray_ds/ndarray_dtype"][:]:
            decoded_item.append(it.decode())
        list_dtypes = decoded_item

        decoded_item = list()
        for it in hdf5["ndarray_ds/ndarray_indexes"][:]:
            decoded_item.append(it.decode())
        list_indexes = decoded_item

        len_data = len(hdf5[f"ndarray_ds/{list_indexes[0]}"][:])

        list_datatype = list()
        for i in range(len(list_indexes)):
            list_datatype.append((list_indexes[i], list_dtypes[i]))

        datatype = np.dtype(list_datatype)

        ndarray = np.zeros(len_data, dtype=datatype)

        for i in range(len(list_indexes)):

            expected_type = list_dtypes[i]

            values = hdf5_read_dataset(
                hdf5[f"ndarray_ds/{list_indexes[i]}"], expected_type
            )

            ndarray[list_indexes[i]] = values

        return ndarray


def save_dict_to_hdf5(hdf5, dictionary):
    """

    dump a dictionary to an hdf5 file

    Parameters
    ----------

    hdf5 : h5py.File
        an hdf5 object

    dictionary : dict
        a custom python dictionary

    """
    if isinstance(dictionary, dict):
        for attr, value in dictionary.items():
            # print("looping:",attr,value)
            try:

                attribute_name = str(attr)
                for character in "/ ":
                    attribute_name = attribute_name.replace(character, "_")

                if isinstance(value, dict):
                    # print("---> dictionary: ",attr, value)

                    hdf5 = add_hdf5_sub_group(hdf5, subgroup=attribute_name)
                    save_dict_to_hdf5(hdf5[attribute_name], value)

                else:

                    hdf5_dataset_creator(hdf5, attribute_name, value)

            except:

                raise ValueError(
                    f"Unable to save attribute {str(attr)} with value {value}"
                )

    else:

        raise ValueError(f"{dictionary} must be a instance of dict.")


def save_dict_to_hdf5file(
    path_to_hdf5, dictionary=None, location="./", replace=False, wait_time=0
):
    """

    dump a dictionary to an hdf5 file

    Parameters
    ----------

    path_to_hdf5 : str
        path to the hdf5 file

    dictionary : dict | None
        a dictionary containing the data to be saved

    location : str
        path location or subgroup where to write data in the hdf5 file

    replace : Boolean
        replace an existing hdf5 file. Default is False

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Examples
    --------

    >>> dict={"a":1,"b":2}
    >>> pyhdf5_handler.save_dict_to_hdf5("saved_dictionary.hdf5",dict)

    """
    if isinstance(dictionary, dict):
        hdf5 = open_hdf5(path_to_hdf5, replace=replace, wait_time=wait_time)

        if hdf5 is None:
            return

        hdf5 = add_hdf5_sub_group(hdf5, subgroup=location)
        save_dict_to_hdf5(hdf5[location], dictionary)

    else:
        raise ValueError(f"The input {dictionary} must be a instance of dict.")

    hdf5.close()


def save_object_to_hdf5(
    hdf5,
    instance,
    keys_data=None,
    location="./",
    sub_data=None,
    replace=False,
    wait_time=0,
):
    """

    dump an object to an hdf5 file

    Parameters
    ----------

    hdf5 : instance of h5py
        An opened hdf5 file

    instance : object
        A custom python object to be saved into an hdf5

    keys_data : list | dict
        optional, a list or a dictionary of the attribute to be saved

    location : str
        path location or subgroup where to write data in the hdf5 file

    sub_data : dict | None
        optional, a extra dictionary containing extra-data to be saved along the object

    replace : Boolean
        replace an existing hdf5 file. Default is False

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    """

    if keys_data is None:
        keys_data = object_handler.generate_object_structure(
            instance, include_method=False
        )

    if hdf5 is None:
        return None

    hdf5 = add_hdf5_sub_group(hdf5, subgroup=location)

    _dump_object_to_hdf5_from_iteratable(hdf5[location], instance, keys_data)

    if isinstance(sub_data, dict):
        save_dict_to_hdf5(hdf5[location], sub_data)

    hdf5.close()


def save_object_to_hdf5file(
    path_to_hdf5,
    instance,
    keys_data=None,
    location="./",
    sub_data=None,
    replace=False,
    wait_time=0,
):
    """

    dump an object to an hdf5 file

    Parameters
    ----------

    path_to_hdf5 : str
        path to the hdf5 file

    instance : object
        A custom python object to be saved into an hdf5

    keys_data : list | dict
        optional, a list or a dictionary of the attribute to be saved

    location : str
        path location or subgroup where to write data in the hdf5 file

    sub_data : dict | None
        optional, a extra dictionary containing extra-data to be saved along the object

    replace : Boolean
        replace an existing hdf5 file. Default is False

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    """

    hdf5 = open_hdf5(path_to_hdf5, replace=replace, wait_time=wait_time)

    save_object_to_hdf5(
        hdf5,
        instance,
        keys_data=keys_data,
        location=location,
        sub_data=sub_data,
        replace=replace,
        wait_time=wait_time,
    )


def read_hdf5file_as_dict(
    path_to_hdf5, location="./", wait_time=0, read_attrs=True, read_dataset_attrs=False
):
    """

    Open, read and close an hdf5 file

    Parameters
    ----------

    path_to_hdf5 : str
        path to the hdf5 file

    location: str
        place in the hdf5 from which we start reading the file

    read_attrs : bool
        read and import attributes in the dicitonnary.

    read_dataset_attrs : bool
        read and import special attributes linked to any dataset and created by pyhdf5_handler. These attributes only store the original dataype of the data stored in the dataset.

    Return
    --------

    dictionary : dict, a dictionary of all keys and attribute included in the hdf5 file

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Examples
    --------

    read an hdf5 file
    dictionary=hdf5_handler.read_hdf5file_as_dict(hdf5["model1"])
    """

    hdf5 = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5 is None:
        return None

    dictionary = read_hdf5_as_dict(
        hdf5[location], read_attrs=read_attrs, read_dataset_attrs=read_dataset_attrs
    )

    hdf5.close()

    return dictionary


def read_hdf5_as_dict(hdf5, read_attrs=True, read_dataset_attrs=False):
    """
    Load an hdf5 file

    Parameters
    ----------

    hdf5 : h5py.File
        an instance of hdf5, open with the function open_hdf5()

    read_attrs : bool
        read and import attributes in the dicitonnary.

    read_dataset_attrs : bool
        read and import special attributes linked to any dataset and created by pyhdf5_handler. These attributes only store the original dataype of the data stored in the dataset.

    Return
    --------

    dictionary : dict, a dictionary of all keys and attribute included in the hdf5 file

    Examples
    --------

    read only a part of an hdf5 file
    >>> hdf5=hdf5_handler.open_hdf5("./multi_model.hdf5")
    >>> dictionary=hdf5_handler.read_hdf5_as_dict(hdf5["model1"])
    >>> dictionary.keys()

    """

    if not isinstance(hdf5, (h5py.File, h5py.Group, h5py.Dataset, h5py.Datatype)):
        print("Error: input arg is not an instance of hdf5.File()")
        return {}

    dictionary = {}

    for key, item in hdf5.items():

        if str(type(item)).find("group") != -1:

            if key == "ndarray_ds":

                # dictionary.update({key: _read_ndarray_datastructure(hdf5)})
                return _read_ndarray_datastructure(hdf5)

            else:

                dictionary.update({key: read_hdf5_as_dict(item)})

        if str(type(item)).find("dataset") != -1:

            if "_" + key in hdf5.attrs.keys():
                expected_type = hdf5.attrs["_" + key]
                values = hdf5_read_dataset(item, expected_type)

            else:

                values = item[:]

            dictionary.update({key: values})

    list_attribute = []
    if read_attrs or read_dataset_attrs:
        tmp_list_attribute = list(hdf5.attrs.keys())
        hdf5_item_matching_attributes = ["_" + element for element in list(hdf5.keys())]

    if read_attrs:

        list_attribute.extend(
            list(
                filter(
                    lambda l: l not in hdf5_item_matching_attributes, tmp_list_attribute
                )
            )
        )

    if read_dataset_attrs:

        list_attribute.extend(
            list(filter(lambda l: l in hdf5_item_matching_attributes, tmp_list_attribute))
        )

    for key in list_attribute:
        dictionary.update({key: hdf5.attrs[key]})

    return dictionary


def hdf5_read_dataset(item, expected_type=None):
    """
    Read a dataset stored in an hdf5 database

    Parameters
    ----------

    item : h5py.File
        an hdf5 dataset/item

    expected_type: str
        the expected dtype as string str(type())

    Return
    --------

    value : the value read from the hdf5, any type matching the expected type


    """

    if expected_type == str(type("str")):

        values = item[0].decode()

    elif expected_type == str(type(1.0)):

        values = item[0]

    elif expected_type == "_None_":

        values = None

    elif expected_type in (str(pd.Timestamp), str(np.datetime64), str(datetime.datetime)):

        if expected_type == str(pd.Timestamp):
            values = pd.Timestamp(item[0].decode())

        elif expected_type == str(np.datetime64):
            values = np.datetime64(item[0].decode())

        elif expected_type == str(datetime.datetime):
            values = datetime.datetime.fromisoformat(item[0].decode())

        else:
            values = item[0].decode()

    else:

        if item[:].dtype.char == "S":

            values = item[:].astype("U")

        elif item[:].dtype.char == "O":

            # decode list if required
            decoded_item = list()
            for it in item[:]:

                decoded_item.append(it.decode())

            values = decoded_item

        else:
            values = item[:]

    return values


def get_hdf5file_attribute(
    path_to_hdf5=str(), location="./", attribute=None, wait_time=0
):
    """
    Get the value of an attribute in the hdf5file

    Parameters
    ----------

    path_to_hdf5 : str
        the path to the hdf5file

    location : str
        path inside the hdf5 where the attribute is stored

    attribute: str
        attribute name

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Return
    --------

    return_attribute : the value of the attribute

    Examples
    --------

    get an attribute
    >>> attribute=hdf5_handler.get_hdf5_attribute("./multi_model.hdf5",attribute=my_attribute_name)

    """

    hdf5_base = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5_base is None:
        return None

    hdf5 = hdf5_base[location]

    return_attribute = hdf5.attrs[attribute]

    hdf5_base.close()

    return return_attribute


def get_hdf5file_dataset(path_to_hdf5=str(), location="./", dataset=None, wait_time=0):
    """
    Get the value of an attribute in the hdf5file

    Parameters
    ----------

    path_to_hdf5 : str
        the path to the hdf5file

    location : str
        path inside the hdf5 where the attribute is stored

    dataset: str
        dataset name

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Return
    --------

    return_dataset : the value of the attribute

    Examples
    --------

    get a dataset
    >>> dataset=hdf5_handler.get_hdf5_dataset("./multi_model.hdf5",dataset=my_dataset_name)

    """

    hdf5_base = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5_base is None:
        return None

    hdf5 = hdf5_base[location]

    if "_" + dataset in hdf5.attrs.keys():
        expected_type = hdf5.attrs["_" + dataset]
        return_dataset = hdf5_read_dataset(hdf5[dataset], expected_type)

    else:
        return_dataset = hdf5[dataset][:]

    hdf5_base.close()

    return return_dataset


def get_hdf5file_item(
    path_to_hdf5=str(), location="./", item=None, wait_time=0, search_attrs=False
):
    """

    Get a custom item in an hdf5file

    Parameters
    ----------

    path_to_hdf5 : str
        the path to the hdf5file

    location : str
        path inside the hdf5 where the attribute is stored. If item is None, item is set to basename(location)

    item: str
        item name

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    search_attrs: bool
        Default is False. If True, the function will also search in the item in the attribute first.

    Return
    --------

    return : custom value. can be an hdf5 object (group), an numpy array, a string, a float, an int ...

    Examples
    --------

    get the dataset 'dataset'
    >>> dataset=hdf5_handler.get_hdf5_item("./multi_model.hdf5",location="path/in/hdf5/dataset")

    """

    hdf5 = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5 is None:
        return None

    hdf5_item = get_hdf5_item(
        hdf5_instance=hdf5, location=location, item=item, search_attrs=search_attrs
    )

    hdf5.close()

    return hdf5_item


def get_hdf5_item(hdf5_instance=None, location="./", item=None, search_attrs=False):
    """

    Get a custom item in an hdf5file

    Parameters
    ----------

    hdf5_instance : h5py.File
        an instance of an hdf5

    location : str
        path inside the hdf5 where the attribute is stored. If item is None, item is set to basename(location)

    item: str
        item name

    search_attrs: bool
        Default is False. If True, the function will search in the item in the attribute first.

    Return
    ------

    return : custom value. can be an hdf5 object (group), an numpy array, a string, a float, an int ...

    Examples
    --------

    get the dataset 'dataset'
    >>> dataset=hdf5_handler.get_hdf5_item("./multi_model.hdf5",location="path/in/hdf5/dataset")

    """

    if item is None and isinstance(location, str):
        head, tail = os.path.split(location)
        if len(tail) > 0:
            item = tail
        location = head

    if not isinstance(item, str):
        print(f"Bad search item:{item}")
        return None

        return None

    # print(f"Getting item '{item}' at location '{location}'")
    hdf5 = hdf5_instance[location]

    # first search in the attribute
    if search_attrs:
        list_attribute = hdf5.attrs.keys()
        if item in list_attribute:
            return hdf5.attrs[item]

    # then search in groups and dataset
    list_keys = hdf5.keys()
    if item in list_keys:

        hdf5_item = hdf5[item]

        # print("Got Item ", hdf5_item)

        if str(type(hdf5_item)).find("group") != -1:

            if item == "ndarray_ds":

                return _read_ndarray_datastructure(hdf5)

            else:

                returned_dict = read_hdf5_as_dict(hdf5_item)

                return returned_dict

        elif str(type(hdf5_item)).find("dataset") != -1:

            if "_" + item in hdf5.attrs.keys():
                expected_type = hdf5.attrs["_" + item]
                values = hdf5_read_dataset(hdf5_item, expected_type)
            else:
                values = hdf5_item[:]

            return values

        else:

            return hdf5_item

    else:

        return None


def search_in_hdf5file(
    path_to_hdf5, key=None, location="./", wait_time=0, search_attrs=False
):
    """

    Search key in an hdf5 and return a list of [locations, datatype, key name, values]. Value and key are returned only if the key is an attribute or a dataset (None otherwise)

    Parameters
    ----------

    path_to_hdf5 : str
        the path to the hdf5file

    key: str
        key to search in the hdf5file

    location : str
        path inside the hdf5 where to start the research

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    search_attrs : Bool
        Default false, search in the attributes

    Return
    ------

    return_dataset : the value of the attribute

    Examples
    --------

    search in a hdf5file
    >>> matchkey=hdf5_handler.search_in_hdf5file(hdf5filename, key='Nom_du_BV',location="./")

    """
    if key is None:
        print("Nothing to search, use key=")
        return []

    hdf5 = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5 is None:
        return None

    results = search_in_hdf5(hdf5, key, location=location, search_attrs=search_attrs)

    hdf5.close()

    return results


def search_in_hdf5(hdf5_base, key=None, location="./", search_attrs=False):
    """

    Search key in an hdf5 and return a list of [locations, datatype, key name, values]. Value and key are returned only if the key is an attribute or a dataset (None otherwise)

    Parameters
    ----------

    hdf5_base : h5py.File
        opened instance of the hdf5

    key: str
        key to search in the hdf5file

    location : str
        path inside the hdf5 where to start the research

    search_attrs : Bool
        Default false, search in the attributes

    Return
    ------

    return_dataset : the value of the attribute

    Examples
    --------

    search in a hdf5
    >>> hdf5=hdf5_handler.open_hdf5(hdf5_file)
    >>> matchkey=hdf5_handler.search_in_hdf5(hdf5, key='Nom_du_BV',location="./")
    >>> hdf5.close()

    """
    if key is None:
        print("Nothing to search, use key=")
        return []

    result = []

    hdf5 = hdf5_base[location]

    if search_attrs:
        list_attribute = hdf5.attrs.keys()

        if key in list_attribute:
            result.append(
                {
                    "path": location,
                    "key": key,
                    "datatype": "attribute",
                    "value": hdf5.attrs[key],
                }
            )

    for hdf5_key, item in hdf5.items():

        if str(type(item)).find("group") != -1:

            sub_location = os.path.join(location, hdf5_key)

            # print(hdf5_key,sub_location,list(hdf5.keys()))

            if hdf5_key == key:

                if "ndarray_ds" in item.keys():

                    result.append(
                        {
                            "path": sub_location,
                            "key": None,
                            "datatype": "ndarray",
                            "value": _read_ndarray_datastructure(item),
                        }
                    )

                else:

                    result.append(
                        {
                            "path": sub_location,
                            "key": None,
                            "datatype": "group",
                            "value": None,
                        }
                    )

            res = search_in_hdf5(hdf5_base, key, sub_location)

            if len(res) > 0:
                for element in res:
                    result.append(element)

        if str(type(item)).find("dataset") != -1:

            if hdf5_key == key:

                if item[:].dtype.char == "S":

                    values = item[:].astype("U")

                elif item[:].dtype.char == "O":

                    # decode list if required
                    decoded_item = list()
                    for it in item[:]:
                        decoded_item.append(it.decode())

                    values = decoded_item

                else:

                    values = item[:]

                result.append(
                    {"path": location, "key": key, "datatype": "dataset", "value": values}
                )

    return result


def hdf5file_view(
    path_to_hdf5,
    location="./",
    max_depth=None,
    level_base=">",
    level_sep="--",
    depth=None,
    wait_time=0,
    list_attrs=True,
    list_dataset_attrs=False,
    return_view=False,
):
    """

    Search key in an hdf5 and return a list of [locations, datatype, key name, values]. Value and key are returned only if the key is an attribute or a dataset (None otherwise)

    Parameters
    ----------


    path_to_hdf5 : str
        Path to an hdf5 database

    location : str
        path inside the hdf5 where to start the research

    max_depth: str
        Max deph of the search in the hdf5

    level_base: str
        string used as separator at the lower level (default '>')

    level_sep: str
        string used as separator at higher level (default '--')

    depth: int
        current depth level

    list_attrs: bool
        default is True, list the attributes

    list_dataset_attrs: bool
        default is False, list the special attributes defined for each dataset by pyhdf5_handler

    return_view: bool
        retrun the object view in a dictionnary (do not print at screen)

    wait_time: int
        If the hdf5 is unavailable, the function will try to access serveral time and will wait wait_time seconds maximum. If this time is elapsed, the file won't be opened and the funciton will return None. This parameter is usefull if several program or threads need to read/write simultaneously in the same hdf5 database.

    Return
    --------

    dictionnary : optional, the view of the hdf5

    Examples
    --------

    search in a hdf5file
    >>> matchkey=hdf5_handler.search_in_hdf5file(hdf5filename, key='Nom_du_BV',location="./")

    """

    hdf5 = open_hdf5(path_to_hdf5, read_only=True, wait_time=wait_time)

    if hdf5 is None:
        return None

    results = hdf5_view(
        hdf5,
        location=location,
        max_depth=max_depth,
        level_base=level_base,
        level_sep=level_sep,
        depth=depth,
        list_attrs=list_attrs,
        list_dataset_attrs=list_dataset_attrs,
        return_view=return_view,
    )

    hdf5.close()

    return results


def hdf5file_ls(path_to_hdf5, location="./"):
    """
    List dataset in an hdf5file.

    Parameters
    ----------

    path_to_hdf5 : str
        path to a hdf5file

    location: str
        path inside the hdf5 where to start the research

    Example
    -------

    >>> hdf5file_ls(test.hdf5)

    """

    hdf5 = open_hdf5(path_to_hdf5, read_only=True)

    hdf5_view(
        hdf5,
        location=location,
        max_depth=0,
        level_base=">",
        level_sep="--",
        list_attrs=False,
        return_view=False,
    )


def hdf5_ls(hdf5):
    """
    List dataset in an hdf5 instance.

    Parameters
    ----------

    hdf5 : h5py.File
        hdf5 instance

    location: str
        path inside the hdf5 where to start the research

    Example
    -------

    >>> hdf5 = open_hdf5(path_to_hdf5, read_only=True)
    >>> hdf5_ls(hdf5)

    """

    hdf5_view(
        hdf5,
        location="./",
        max_depth=0,
        level_base=">",
        level_sep="--",
        list_attrs=False,
        return_view=False,
    )


def hdf5_view(
    hdf5_obj,
    location="./",
    max_depth=None,
    level_base=">",
    level_sep="--",
    depth=None,
    list_attrs=True,
    list_dataset_attrs=False,
    return_view=False,
):
    """
    List recursively all dataset (and attributes) in an hdf5 object.

    Parameters
    ----------

    hdf5_obj : h5py.File
        opened instance of the hdf5

    location : str
        path inside the hdf5 where to start the research

    max_depth: str
        Max deph of the search in the hdf5

    level_base: str
        string used as separator at the lower level (default '>')

    level_sep: str
        string used as separator at higher level (default '--')

    depth: int
        current level depth

    list_attrs: bool
        default is True, list the attributes

    list_dataset_attrs: bool
        default is False, list the special attributes defined for each dataset by pyhdf5_handler

    return_view: bool
        retrun the object view in a dictionnary

    Return
    --------

    dictionnary : optional, the view of the hdf5

    Examples
    --------

    search in a hdf5
    >>> hdf5=hdf5_handler.open_hdf5(hdf5_file)
    >>> matchkey=hdf5_handler.search_in_hdf5(hdf5, key='Nom_du_BV',location="./")
    >>> hdf5.close()

    """

    result = []

    if max_depth is not None:

        if depth is not None:
            depth = depth + 1
        else:
            depth = 0

        if depth > max_depth:
            return result

    hdf5 = hdf5_obj[location]

    list_attribute = []
    if list_attrs or list_dataset_attrs:
        tmp_list_attribute = list(hdf5.attrs.keys())
        list_keys_matching_attributes = ["_" + element for element in list(hdf5.keys())]

    if list_attrs:

        list_attribute.extend(
            list(
                filter(
                    lambda l: l not in list_keys_matching_attributes, tmp_list_attribute
                )
            )
        )

    if list_dataset_attrs:

        list_attribute.extend(
            list(filter(lambda l: l in list_keys_matching_attributes, tmp_list_attribute))
        )

    for key in list_attribute:
        values = hdf5.attrs[key]
        sub_location = os.path.join(location, key)
        if isinstance(
            values, (int, float, np.int64, np.float64, np.int32, np.float32, np.bool)
        ):
            result.append(
                f"{level_base}| {sub_location}, attribute, type={type(hdf5.attrs[key])}, value={values}"
            )
        elif isinstance(values, (str)) and len(values) < 20:
            result.append(
                f"{level_base}| {sub_location}, attribute, type={type(hdf5.attrs[key])}, len={len(values)}, value={values}"
            )
        else:
            result.append(
                f"{level_base}| {sub_location}, attribute, type={type(hdf5.attrs[key])}, len={len(values)}, value={values[0:20]}..."
            )

    for hdf5_key, item in hdf5.items():

        if str(type(item)).find("group") != -1:

            sub_location = os.path.join(location, hdf5_key)

            if "ndarray_ds" in item.keys():
                result.append(f"{level_base}| {sub_location}, ndarray")
            else:
                result.append(f"{level_base}| {sub_location}, group")

            res = hdf5_view(
                hdf5_obj,
                sub_location,
                max_depth=max_depth,
                level_base=level_base + level_sep,
                depth=depth,
                return_view=True,
            )

            # if len(res)>0:
            for key, item in enumerate(res):
                result.append(item)

        if str(type(item)).find("dataset") != -1:

            if item[:].dtype.char == "S":
                values = item[:].astype("U")
            else:
                values = item[:]

            sub_location = os.path.join(location, hdf5_key)

            result.append(
                f"{level_base}| {sub_location}, dataset, type={type(values)}, shape={values.shape}"
            )

    if return_view:
        return result
    else:
        for res in result:
            print(res)
