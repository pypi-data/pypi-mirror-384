#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 09:38:05 2025

@author: maxime
"""

if __name__ == "__main__":

    import smash
    import pyhdf5_handler

    setup, mesh = smash.factory.load_dataset("Lez")

    setup.update({"start_time": "2014-01-01 00:00", "end_time": "2014-02-02 00:00"})

    model = smash.Model(setup, mesh)

    model.forward_run()

    # save dict :
    pyhdf5_handler.save_dict_to_hdf5file(
        "./test.hdf5",
        {
            "smash_rr_initial_states": {
                "keys": model.rr_initial_states.keys,
                "values": model.rr_initial_states.values,
            }
        },
    )

    test = pyhdf5_handler.read_hdf5file_as_dict(
        "./test.hdf5", location="smash_rr_initial_states"
    )

    # save part of object model:
    pyhdf5_handler.save_object_to_hdf5file(
        "./test.hdf5",
        model.rr_initial_states,
        location="./smash_object_rr_initial_states",
    )

    test = pyhdf5_handler.read_hdf5file_as_dict(
        "./test.hdf5", location="smash_object_rr_initial_states"
    )

    # save full model object
    pyhdf5_handler.save_object_to_hdf5file(
        "./test.hdf5", model, location="./full_smash_object"
    )

    test = pyhdf5_handler.read_hdf5file_as_dict(
        "./test.hdf5", location="full_smash_object"
    )
