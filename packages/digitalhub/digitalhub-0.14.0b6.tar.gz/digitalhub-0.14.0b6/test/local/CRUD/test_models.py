# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for the entity Models
"""

import digitalhub as dh
from digitalhub.entities.model._base.entity import Model


class TestModelCRUD:
    def create_test_dicts(self):
        names = ["test1", "test2", "test3", "test4"]
        uuids = [
            "d150bcca-bb64-451d-8455-dff862254b95",
            "31acdd2d-0c41-428c-b68b-1b133da9e97b",
            "b4a3dfdc-b917-44c4-9a29-613dcf734244",
            "2618d9c4-cd61-440f-aebb-7e5761709f3b",
        ]
        paths = [
            "./data/my_random_forest_model.pkl",
            "s3://bucket/model.pkl",
            "sql://database/schema/linear_regression_model.joblib",
            "https://url.com/bert_base_uncased.pt",
        ]
        kind = ["model", "model", "model", "model"]

        dicts = []
        for i in range(len(names)):
            dicts.append({"name": names[i], "uuid": uuids[i], "path": paths[i], "kind": kind[i]})

        return dicts

    def test_create_delete(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)
        # Create and delete models
        for i in dicts:
            d = dh.new_model(p.name, **i)
            dh.delete_model(d.key)
            d = dh.new_model(p.name, **i)
            dh.delete_model(d.name, project=p.name, entity_id=d.id)
            d = p.new_model(**i)
            p.delete_model(d.key)
        assert dh.list_models(p.name) == []
        dh.delete_project("test", local=True, clean_context=True)

    def test_list(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        assert dh.list_models(p.name) == []

        for i in dicts:
            dh.new_model(p.name, **i)

        # List models
        l_obj = dh.list_models(p.name)
        assert isinstance(l_obj, list)
        assert len(l_obj) == 4
        for i in l_obj:
            assert isinstance(i, Model)

        # delete listed objects
        for obj in l_obj:
            dh.delete_model(obj.key)

        assert len(dh.list_models(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)

    def test_get(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        for i in dicts:
            o1 = dh.new_model(p.name, **i)
            assert isinstance(o1, Model)

            # Get by name and id
            o2 = dh.get_model(o1.name, project=p.name, entity_id=o1.id)
            assert isinstance(o2, Model)
            assert o1.id == o2.id

            # Get by key
            o3 = dh.get_model(o1.key)
            assert isinstance(o3, Model)
            assert o1.id == o3.id

        # delete listed objects
        l_obj = dh.list_models(p.name)
        for obj in l_obj:
            dh.delete_model(obj.key)

        assert len(dh.list_models(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)
