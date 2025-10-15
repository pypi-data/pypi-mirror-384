"""Configuration for the pytest test suite."""

from os import environ

from bear_dereth import METADATA

environ[f"{METADATA.env_variable}"] = "test"
