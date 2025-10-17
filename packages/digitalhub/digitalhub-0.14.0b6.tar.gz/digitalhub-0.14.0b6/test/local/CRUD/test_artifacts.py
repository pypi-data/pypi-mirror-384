# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for the entity Artifact
"""

import digitalhub as dh
from digitalhub.entities.artifact._base.entity import Artifact


class TestArtifactCRUD:
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
        kind = ["artifact", "artifact", "artifact", "artifact"]

        dicts = []
        for i in range(len(names)):
            dicts.append({"name": names[i], "uuid": uuids[i], "path": paths[i], "kind": kind[i]})

        return dicts

    def test_create_delete(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)
        # Create and delete artifacts
        for i in dicts:
            d = dh.new_artifact(p.name, **i)
            dh.delete_artifact(d.key)
            d = dh.new_artifact(p.name, **i)
            dh.delete_artifact(d.name, project=p.name, entity_id=d.id)
            d = p.new_artifact(**i)
            p.delete_artifact(d.key)

        assert dh.list_artifacts(p.name) == []
        dh.delete_project("test", local=True, clean_context=True)

    def test_list(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        assert dh.list_artifacts(p.name) == []

        for i in dicts:
            dh.new_artifact(p.name, **i)

        # List artifacts
        l_obj = dh.list_artifacts(p.name)
        assert isinstance(l_obj, list)
        assert len(l_obj) == 4
        for i in l_obj:
            assert isinstance(i, Artifact)

        # delete listed objects
        for obj in l_obj:
            dh.delete_artifact(obj.key)

        assert len(dh.list_artifacts(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)

    def test_get(self):
        dicts = self.create_test_dicts()
        p = dh.get_or_create_project("test", local=True)

        for i in dicts:
            o1 = dh.new_artifact(p.name, **i)
            assert isinstance(o1, Artifact)

            # Get by name and id
            o2 = dh.get_artifact(o1.name, project=p.name, entity_id=o1.id)
            assert isinstance(o2, Artifact)
            assert o1.id == o2.id

            # Get by key
            o3 = dh.get_artifact(o1.key)
            assert isinstance(o3, Artifact)
            assert o1.id == o3.id

        # delete listed objects
        l_obj = dh.list_artifacts(p.name)
        for obj in l_obj:
            dh.delete_artifact(obj.key)

        assert len(dh.list_artifacts(p.name)) == 0

        dh.delete_project("test", clean_context=True, local=True)
