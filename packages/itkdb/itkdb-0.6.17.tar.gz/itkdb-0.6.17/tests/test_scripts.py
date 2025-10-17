from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import betamax
import getInventory
import pytest

import itkdb

sys.path.append(os.path.realpath(os.path.dirname(__file__) + "/.."))  # noqa: PTH120


@pytest.mark.parametrize(
    "param",
    [
        ("listInstitutions", "INST"),
        ("listComponentTypes", None),
        ("listInventory", None),
        ("trashUnassembled", None),
    ],
    ids=["listInstitutions", "listComponentTypes", "listInventory", "trashUnassembled"],
)
def test_getInventory(auth_client, param):
    command, institution = param
    args = SimpleNamespace(
        command=command,
        componentType=None,
        includeTrashed=False,
        institution=institution,
        project="S",
        savePath=None,
        useCurrentLocation=False,
    )
    with betamax.Betamax(
        auth_client, cassette_library_dir=itkdb.settings.ITKDB_CASSETTE_LIBRARY_DIR
    ) as recorder:
        recorder.use_cassette(
            f"test_scripts.test_getInventory.{command:s}", record="once"
        )
        inventory = getInventory.Inventory(args, auth_client)
        assert inventory.main()
