"""
.. include:: ../README.md
"""

from .src.hdf5_handler import close_all_hdf5_file, open_hdf5, add_hdf5_sub_group, hdf5_dataset_creator, save_dict_to_hdf5, save_dict_to_hdf5file, save_object_to_hdf5file, read_hdf5file_as_dict, read_hdf5_as_dict, hdf5_read_dataset, get_hdf5file_attribute, get_hdf5file_dataset, get_hdf5file_item, get_hdf5_item, search_in_hdf5file, search_in_hdf5, hdf5file_view, hdf5file_ls, hdf5_ls, hdf5_view

from .src.object_handler import generate_dict_structure, generate_object_structure, read_object_as_dict
