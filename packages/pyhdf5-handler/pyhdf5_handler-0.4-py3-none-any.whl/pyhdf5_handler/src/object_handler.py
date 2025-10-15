
from __future__ import annotations

import numpy as np
import numbers
import pandas as pd
import datetime


def _isinstance_pandas(value):
    pandas_classes = [getattr(pd, item) for item in dir(pd) if isinstance(getattr(pd, item), type)]
    for cls in pandas_classes:
        if isinstance(value, cls):
            return True
    return False

def _isinstance_numpy(value):
    numpy_classes = [getattr(np, item) for item in dir(np) if isinstance(getattr(np, item), type)]
    for cls in numpy_classes:
        if isinstance(value, cls):
            return True
    return False

def _isinstance_datetime(value):
    datetime_classes = [getattr(datetime, item) for item in dir(datetime) if isinstance(getattr(datetime, item), type)]
    for cls in datetime_classes:
        if isinstance(value, cls):
            return True
    return False

def generate_dict_structure(dictionary,recursion_counter=0,recursion_limit=100,include_method=True):
    """
    
    this function create a full dictionnary containing all the structure of an dictionnary in order to save it to an hdf5

    Parameters
    ----------
    
    instance : python dictionary
        a custom dictionary.
    recursion_limit : int
        max recursion limit to dig inside `instance`
    recursion_counter: int
        current recursion value
    include_method: bool
        Include methods/functions in the object structure, if False, only data will be included.

    Returns
    -------
    
    list or dict :
        A list or dictionary matching the structure of the python object.
    
    """
    key_data={}
    key_list = list()
    recursion_counter=0
    for attr,value in dictionary.items():
        
        try:
            if isinstance(value,dict):
                
                subkey_data=generate_dict_structure(value)
                if len(subkey_data)>0:
                    key_data.update({attr:subkey_data})
            
            elif isinstance(value, (list, tuple, numbers.Number, str)):
                key_list.append(attr)
            
            elif _isinstance_pandas(value):
                key_list.append(attr)
                
            elif _isinstance_datetime(value):
                key_list.append(attr)
                
            elif _isinstance_numpy(value):
                key_list.append(attr)
            
            elif type(value) == "method":
                if include_method:
                    key_list.append(attr)
                else:
                    next(attr)
            
            else:
                
                recursion_counter = recursion_counter+1
                
                if recursion_counter > recursion_limit:
                    print(f"recursion counter exceed the limit of {recursion_limit}... return")
                    return
                
                subkey_data = generate_object_structure(value,recursion_counter=recursion_counter,recursion_limit=recursion_limit,include_method=include_method)
                if len(subkey_data) > 0:
                    key_data.update({attr: subkey_data})

        except:
            pass
    
    for attr, value in key_data.items():
        key_list.append({attr: value})
    
    return key_list


def generate_object_structure(instance,recursion_counter=0,recursion_limit=100,include_method=True):
    """
    
    this function create a full dictionnary containing all the structure of an object in order to save it to an hdf5

    Parameters
    ----------
    
    instance : object
        a custom python object.
    recursion_limit : int
        max recursion limit to dig inside `instance`
    recursion_counter: int
        current recursion value
    include_method: bool
        Include methods/functions in the object structure, if False, only data will be included.

    Returns
    -------
    
    list or dict :
        A list or dictionary matching the structure of the python object.
    
    """
    key_data = {}
    key_list = list()
    return_list = False
    recursion_counter = 0
    for attr in dir(instance):
        
        if not attr.startswith("_") and not attr in ["from_handle", "copy"]:
            
            try:
                value = getattr(instance, attr)
                
                if isinstance(value, (list, tuple)):
                    key_list.append(attr)
                    return_list = True
                
                elif _isinstance_numpy(value):
                    key_list.append(attr)
                    return_list = True
                
                elif isinstance(value, dict):
                    
                    depp_key_data=generate_dict_structure(value)
                    if len(depp_key_data) > 0:
                        key_data.update({attr: depp_key_data})

                elif isinstance(value, numbers.Number):
                    key_list.append(attr)
                    return_list = True

                elif isinstance(value, str):
                    key_list.append(attr)
                    return_list = True

                elif "<class 'method" in str(type(value)):
                    if include_method:
                        key_list.append(attr)
                        return_list = True
                    else:
                        next(attr)
                
                elif _isinstance_pandas(value):
                    key_list.append(attr)
                    return_list = True
                
                elif _isinstance_datetime(value):
                    key_list.append(attr)
                    return_list = True
                    
                else:
                    
                    recursion_counter = recursion_counter+1
                    
                    if recursion_counter > recursion_limit:
                        print(f"recursion counter exceed the limit of {recursion_limit}... return")
                        return
                    
                    depp_key_data = generate_object_structure(value, recursion_counter=recursion_counter,recursion_limit=recursion_limit,include_method=include_method)

                    if len(depp_key_data) > 0:
                        key_data.update({attr: depp_key_data})

            except:
                # raise ValueError("unable to parse attr", attr)
                # ~ print("unable to parse attr", attr, "skip it...")
                pass

    if return_list:
        for attr, value in key_data.items():
            key_list.append({attr: value})

        return key_list

    else:
        return key_data


def read_object_as_dict(instance, recursion_counter=0,recursion_limit=100):
    """
    
    create a dictionary from a custom python object

    Parameters
    ----------
    
    instance : object
        an custom python object
    recursion_limit : int
        max recursion limit to dig inside `instance`
    recursion_counter: int
        current recursion value

    Return
    ------
    
    key_data: dict
        an dictionary containing all keys and atributes of the object
    
    """
    key_data = {}
    recursion_counter = 0
    for attr in dir(instance):
        #print(attr)
        if not attr.startswith("_") and not attr in ["from_handle", "copy"]:
            try:
                value = getattr(instance, attr)
                
                if isinstance(value, (list, tuple)):
                    
                    if isinstance(value, list):
                        value = np.array(value).astype('U')

                    if value.dtype == "object" or value.dtype.char == "U":
                        value = value.astype("U")
                    
                    key_data.update({attr: value})
                
                elif isinstance(value, dict):
                    key_data.update({attr: value})
                
                elif isinstance(value, numbers.Number):
                    key_data.update({attr: value})

                elif isinstance(value, str):
                    key_data.update({attr: value})

                elif type(value) == "method":
                    next(attr)
                
                elif _isinstance_pandas(value):
                    if value.dtype == "object" or value.dtype.char == "U":
                        value = value.astype("U")
                    key_data.update({attr: value})
                
                elif _isinstance_datetime(value):
                    if value.dtype == "object" or value.dtype.char == "U":
                        value = value.astype("U")
                    key_data.update({attr: value})
                
                elif _isinstance_numpy(value):
                    if value.dtype == "object" or value.dtype.char == "U":
                        value = value.astype("U")
                    key_data.update({attr: value})

                else:
                    
                    recursion_counter = recursion_counter+1
                    
                    if recursion_counter > recursion_limit:
                        print(f"recursion counter exceed the limit of {recursion_limit}... return")
                        return
                    
                    depp_key_data = read_object_as_dict(
                        value, recursion_counter=recursion_counter,recursion_limit=recursion_limit)
                    
                    if len(depp_key_data) > 0:
                        key_data.update({attr: depp_key_data})

            except:
                pass

    return key_data
