# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for the entity Dataitem
"""

import digitalhub as dh
from digitalhub.entities.dataitem._base.entity import Dataitem


class TestDataitemCRUD:
    def create_test_dicts(self):
        names = ["test1", "test2", "test3", "test4"]
        uuids = [
            "d150bcca-bb64-451d-8455-dff862254b95",
            "31acdd2d-0c41-428c-b68b-1b133da9e97b",
            "b4a3dfdc-b917-44c4-9a29-613dcf734244",
            "2618d9c4-cd61-440f-aebb-7e5761709f3b",
        ]
        paths = [
            "./data/test.csv",
            "s3://bucket/key.csv",
            "sql://database/schema/table",
            "https://url.com/file.csv",
        ]
        kind = ["dataitem", "dataitem", "dataitem", "dataitem"]

        dicts = []
        for i in range(len(names)):
            dicts.append({"name": names[i], "uuid": uuids[i], "path": paths[i], "kind": kind[i]})

        return dicts

    def test_create_delete(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)
        # Create and delete dataitems
        for i in dicts:
            d = dh.new_dataitem(p.name, **i)
            dh.delete_dataitem(d.key)
            d = dh.new_dataitem(p.name, **i)
            dh.delete_dataitem(d.name, project=p.name, entity_id=d.id)
            d = p.new_dataitem(**i)
            p.delete_dataitem(d.key)

        assert dh.list_dataitems(p.name) == []
        dh.delete_project("test", local=True, clean_context=True)

    def test_list(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        assert dh.list_dataitems(p.name) == []

        for i in dicts:
            dh.new_dataitem(p.name, **i)

        # List dataitems
        l_obj = dh.list_dataitems(p.name)
        assert isinstance(l_obj, list)
        assert len(l_obj) == 4
        for i in l_obj:
            assert isinstance(i, Dataitem)

        # delete listed objects
        for obj in l_obj:
            dh.delete_dataitem(obj.key)

        assert len(dh.list_dataitems(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)

    def test_get(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        for i in dicts:
            o1 = dh.new_dataitem(p.name, **i)
            assert isinstance(o1, Dataitem)

            # Get by name and id
            o2 = dh.get_dataitem(o1.name, project=p.name, entity_id=o1.id)
            assert isinstance(o2, Dataitem)
            assert o1.id == o2.id

            # Get by key
            o3 = dh.get_dataitem(o1.key)
            assert isinstance(o3, Dataitem)
            assert o1.id == o3.id

        # delete listed objects
        l_obj = dh.list_dataitems(p.name)
        for obj in l_obj:
            dh.delete_dataitem(obj.key)

        assert len(dh.list_dataitems(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)
