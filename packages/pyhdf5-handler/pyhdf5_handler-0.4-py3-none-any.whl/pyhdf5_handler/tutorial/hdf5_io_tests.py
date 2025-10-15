if __name__ == "__main__":
    import numpy as np
    import pyhdf5_handler
    import datetime
    import pandas as pd

    # open an hdf5 database, test.hdf5.
    hdf5 = pyhdf5_handler.open_hdf5("./test.hdf5")

    # Create a group in the hdf5
    hdf5 = pyhdf5_handler.add_hdf5_sub_group(hdf5, subgroup="my_group")
    hdf5["my_group"]

    # save any data in the hdf5 database
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "str", "str")
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "numbers", 1.0)
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "none", None)
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5, "timestamp_numpy", np.datetime64("2019-09-22T17:38:30")
    )
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5, "timestamp_datetime", datetime.datetime.fromisoformat("2019-09-22T17:38:30")
    )
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5, "timestamp_pandas", pd.Timestamp("2019-09-22T17:38:30")
    )
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "list_num", [1.0, 2.0])
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "list_str", ["a", "b"])
    pyhdf5_handler.hdf5_dataset_creator(hdf5, "list_mixte", [1.0, "a"])
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5,
        "list_date_numpy",
        [np.datetime64("2019-09-22 17:38:30"), np.datetime64("2019-09-22 18:38:30")],
    )
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5,
        "list_date_datetime",
        [
            datetime.datetime.fromisoformat("2019-09-22 17:38:30"),
            datetime.datetime.fromisoformat("2019-09-22T18:38:30"),
        ],
    )
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5,
        "list_date_pandas",
        [pd.Timestamp("2019-09-22 17:38:30"), pd.Timestamp("2019-09-22 17:38:30")],
    )
    pyhdf5_handler.hdf5_dataset_creator(
        hdf5, "list_date_range_pandas", pd.date_range(start="1/1/2018", end="1/08/2018")
    )

    # write a python dictionary in the hdf5 database
    dictionary = {
        "dict": {
            "int": 1,
            "float": 2.0,
            "none": None,
            "timestamp": pd.Timestamp("2019-09-22 17:38:30"),
            "list": [1, 2, 3, 4],
            "array": np.array([1, 2, 3, 4]),
            "date_range": pd.date_range(start="1/1/2018", end="1/08/2018"),
            "list_mixte": [1.0, np.datetime64("2019-09-22 17:38:30")],
        }
    }

    hdf5.attrs["attribute"] = "myattribute"

    pyhdf5_handler.save_dict_to_hdf5(hdf5, dictionary)

    # handle structured ndarray
    data = [("Alice", 25, 55.0), ("Bob", 32, 60.5)]
    dtypes = [("name", "U10"), ("age", "i4"), ("weight", "f4")]
    people = np.array(data, dtype=dtypes)

    pyhdf5_handler.hdf5_dataset_creator(hdf5, "structured_array", people)

    # viewing data stored in the hdf5 (recursive)
    pyhdf5_handler.hdf5_view(hdf5)
    pyhdf5_handler.hdf5file_view("./test.hdf5")

    # viwing element stored in the hdf5 (at the current level)
    pyhdf5_handler.hdf5_ls(hdf5)

    # read an hdf5 and import it as a python dictionary
    data = pyhdf5_handler.read_hdf5_as_dict(hdf5, read_attrs=True)

    # read a specific item
    pyhdf5_handler.hdf5_read_dataset(item=hdf5["str"], expected_type=hdf5.attrs["_str"])
    pyhdf5_handler.hdf5_read_dataset(
        item=hdf5["list_date_numpy"], expected_type=hdf5.attrs["_list_date_numpy"]
    )

    # close the hdf5
    hdf5.close()

    # handle file directly
    pyhdf5_handler.hdf5file_ls("./test.hdf5")
    pyhdf5_handler.hdf5file_ls("./test.hdf5", location="structured_array")

    data = pyhdf5_handler.read_hdf5file_as_dict("./test.hdf5", read_attrs=False)

    pyhdf5_handler.save_dict_to_hdf5file("./test.hdf5", data)

    res = pyhdf5_handler.search_in_hdf5file(
        "./test.hdf5", key="date_range", location="./", wait_time=0
    )

    res = pyhdf5_handler.search_in_hdf5file(
        "./test.hdf5", key="structured_array", location="./", wait_time=0
    )

    pyhdf5_handler.get_hdf5file_item(
        path_to_hdf5="./test.hdf5",
        location="./",
        item="structured_array",
        search_attrs=False,
    )

    pyhdf5_handler.get_hdf5file_item(
        path_to_hdf5="./test.hdf5", location="./", item="list_mixte", search_attrs=False
    )

    pyhdf5_handler.get_hdf5file_item(
        path_to_hdf5="./test.hdf5", location="./", item="attribute", search_attrs=True
    )

    pyhdf5_handler.get_hdf5file_attribute(
        path_to_hdf5="./test.hdf5", location="./", attribute="_list_num", wait_time=0
    )

    pyhdf5_handler.get_hdf5file_attribute(
        path_to_hdf5="./test.hdf5",
        location="./structured_array/ndarray_ds",
        attribute="_name",
        wait_time=0,
    )

    pyhdf5_handler.get_hdf5file_dataset(
        path_to_hdf5="./test.hdf5", location="./dict", dataset="list_mixte"
    )
