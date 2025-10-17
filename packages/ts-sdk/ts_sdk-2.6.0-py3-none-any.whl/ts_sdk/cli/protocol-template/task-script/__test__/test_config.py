import json
import os
import sys
from importlib import import_module

import jsonschema
import yaml
from pytest import fixture

import ts_sdk.schemas as s


@fixture
def config():
    with open("./config.json") as f:
        return json.load(f)


@fixture
def protocol():
    with open("../protocol/protocol.yml") as f:
        return yaml.safe_load(f)


def test_config_schema(config):
    jsonschema.validate(config, s.config)


def test_funcs(config):
    for fn in config["functions"]:
        qname = fn["function"]
        mod, func = qname.split(".")
        assert hasattr(import_module(mod), func), f"unable to find function {qname}"
        assert func == fn["slug"]


def test_protocol_schema(protocol):
    jsonschema.validate(protocol, s.protocolV3)
