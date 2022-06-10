from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, ValidationError, validator
from yaml import YAMLError

from easyca.exceptions.configuration_exceptions import ConfigurationContentError, \
    ConfigurationFileNotFoundException, \
    ConfigurationFormatError, ConfigurationVersionError

SUPPORTED_VERSIONS = ["v2.0.0"]


class ConfigurationCertificate(BaseModel):
    cn: str
    san: Optional[str]


class Configuration(BaseModel):
    version: str
    certs: List[ConfigurationCertificate]

    @validator('version')
    def check_version(cls, version):
        if version not in SUPPORTED_VERSIONS:
            raise ConfigurationVersionError(message=f"The configuration version is not supported. "
                                                    f"Supported configuration versions are "
                                                    f"{SUPPORTED_VERSIONS}")
        return version

    @classmethod
    def parse(cls, file: Path):
        """
        Parse a config file into this configuration object model
        :param file: Path of the configuration file to parse
        :return: The Configuration object model
        """
        if not file.is_file():
            raise ConfigurationFileNotFoundException(f"Configuration file not found '{file}'")

        with open(file, "r") as f:
            try:
                return cls.parse_obj(yaml.safe_load(f.read()))
            except YAMLError as e:
                raise ConfigurationFormatError(f"Unexpected configuration format. Expected YAML "
                                               f"for file '{file}'", e.args)
            except ValidationError as e:
                raise ConfigurationContentError(f"Invalid configuration in file '{file}'", e.args)
