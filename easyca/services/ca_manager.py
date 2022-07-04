import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from easyca.environment import EnvironmentLoader
from easyca.exceptions.ca_exceptions import CANotFound, RootCANotFound, SigningCANotFound
from easyca.exceptions.certificate_exception import CertificateExists, CertificateNotFound, \
    PrivateKeyNotFound
from easyca.logger import EasyCALogger
from easyca.models.configuration import Configuration, ConfigurationCertificate
from easyca.utils.file_utils import list_dirs, list_files
from easyca.utils.subprocess_utils import execute
from easyca.workspace import WorkspaceLoader

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


class CAManager(object):

    def __init__(self, name: str):
        self.name = name
        self.environment = EnvironmentLoader.get_environment()
        self.ca_dir = Path(self.environment.get_workspace()) / name
        self.ca_root_dir = self.ca_dir / "root"
        self.ca_intermediate_dir = self.ca_dir / "intermediate"
        resources_dir = self.environment.get_resources_dir()
        self.ca_root_config = Path(resources_dir) / "ca_root.cnf"
        self.ca_intermediate_config = Path(resources_dir) / "ca_intermediate.cnf"
        self.ca_node_config = Path(resources_dir) / "node.cnf"

    def init_directory(self):
        os.makedirs(self.ca_dir)

    def generate_root_ca(self, debug: bool = False):
        logger.debug(f"Generate the CA '{self.name}'")
        script = self.environment.get_scripts_dir() + "/root.sh"
        if Path(self.ca_dir).exists():
            logger.warning(f"Skip '{self.name}' root CA generation : already exists")
        else:
            os.makedirs(self.ca_root_dir)
            execute([script,
                     "--dir", str(self.ca_root_dir),
                     "--name", self.name,
                     "--config", str(self.ca_root_config)],
                    stream_stdout=debug)

    def generate_intermediate_ca(self, debug: bool = False):
        logger.debug(f"Generate the signing CA")
        script = self.environment.get_scripts_dir() + "/certificates.sh"
        os.makedirs(self.ca_intermediate_dir)
        execute([script,
                 "--dir", str(self.ca_intermediate_dir),
                 "--name", self.name,
                 "--config", str(self.ca_intermediate_config),
                 "--issuer", str(self.ca_root_dir),
                 "--cn", "intermediate"],
                stream_stdout=debug)

    def generate_certificates(self, config_file: Path, debug: bool = False):
        if config_file:
            configuration = Configuration.parse(config_file)
        else:
            cn = "default"
            san = "127.0.0.1"
            cert_config = ConfigurationCertificate(cn=cn, san=san)
            version = f"v{EnvironmentLoader.get_environment().get_version()}"
            configuration = Configuration(version=version, certs=[cert_config])

        logger.debug(f"Use the CA {self.name}")
        logger.debug(f"Generate certificates")
        script = self.environment.get_scripts_dir() + "/certificates.sh"
        for cert in configuration.certs:
            try:
                os.makedirs(self.ca_dir / cert.cn)
                logger.info(f"Create certificate cn={cert.cn}")
                execute([script,
                         "--name", self.name,
                         "--dir", str(self.ca_dir / cert.cn),
                         "--config", str(self.ca_node_config),
                         "--issuer", str(self.ca_intermediate_dir),
                         "--cn", str(cert.cn),
                         "--san", str(cert.san),
                         "--node"],
                        stream_stdout=debug)
            except FileExistsError:
                logger.warning(f"Skip cn='{cert.cn}': certificate already exists")

    @staticmethod
    def list_cas() -> "List[Path]":
        workspace = WorkspaceLoader.get_workspace().get_path()
        return list_dirs(workspace)

    @staticmethod
    def delete_cas(names: List[str]):
        for name in names:
            logger.debug(f"Delete CA '{name}'")
            shutil.rmtree(os.path.join(WorkspaceLoader.get_workspace().get_path(), name))

    @staticmethod
    def delete_certs(ca: str, names: List[str]):
        for name in names:
            logger.debug(f"Delete CA '{name}'")
            shutil.rmtree(os.path.join(WorkspaceLoader.get_workspace().get_path(), ca, name))

    @staticmethod
    def get_current() -> str:
        workspace = WorkspaceLoader.get_workspace()
        metadata = workspace.get_metadata()
        return metadata["current"]

    @staticmethod
    def set_current(ca_name: str):
        workspace = WorkspaceLoader.get_workspace()
        metadata = workspace.get_metadata()
        metadata["current"] = ca_name
        workspace.set_metadata(metadata)

    @staticmethod
    def delete_certs(ca: str, names: List[str]):
        for name in names:
            shutil.rmtree(os.path.join(WorkspaceLoader.get_workspace().get_path(), ca, name))

    def check_ca(self):
        """
        verify the health of the CA
        """
        # check folder
        if not self.ca_dir.exists():
            raise CANotFound
        # check root ca folder and certs
        if not self.ca_root_dir.exists():
            raise RootCANotFound
        self.check_certs("root")
        # check signing ca folder and certs
        if not self.ca_intermediate_dir.exists():
            raise SigningCANotFound
        self.check_certs("intermediate")

    def check_certs(self, name: str):
        """
        Check if the certificate and the private key exist for a given certificate name
        """
        certs = self.list_certs_names(filter_certs=[name]).get(name)
        if f"{self.name}_{name}.crt" not in certs:
            raise CertificateNotFound
        elif f"{self.name}_{name}.p8" not in certs:
            raise PrivateKeyNotFound

    def list_certs(self, exclude_ca=False, filter_certs: Optional[List[str]] = None) -> "Dict":
        ca_certs = {}
        exclude_cas = ["root", "intermediate"] if exclude_ca else [""]
        certs_dirs = [self.ca_dir / cert_dir for cert_dir
                      in list_dirs(self.ca_dir, exclude=exclude_cas, include=filter_certs)]
        for cert_dir in certs_dirs:
            certs = [cert_dir / "certs" / file for file in list_files(Path(cert_dir) / "certs")]
            keys = [cert_dir / "private" / file for file in list_files(Path(cert_dir) / "private")]
            ca_certs[cert_dir] = certs + keys

        return ca_certs

    def list_certs_names(self, exclude_ca=False, filter_certs: Optional[List[str]] = None) \
            -> "Dict":
        result = {}
        ca_certs_paths = self.list_certs(exclude_ca=exclude_ca, filter_certs=filter_certs)
        for cert_dir in ca_certs_paths.keys():
            result[str(Path(cert_dir).name)] = [str(Path(cert).name) for cert
                                                in ca_certs_paths[cert_dir]]

        return result

    def export_certs(self, output_dir: Path, names: Optional[List[str]] = None):
        certs_dict = self.list_certs(exclude_ca=True)
        target_dir = output_dir / self.name
        os.makedirs(target_dir, exist_ok=True)
        ca_cert = self.ca_dir / "intermediate/certs/ca.crt"
        shutil.copyfile(ca_cert, target_dir / str(Path(ca_cert).name))
        for cert_dir, certs_paths in certs_dict.items():
            cert_dirname = str(Path(cert_dir).name)
            target_dir = output_dir / self.name / cert_dirname
            os.makedirs(target_dir, exist_ok=True)
            # copy keys and certs
            for cert_path in certs_paths:
                shutil.copyfile(cert_path, target_dir / str(Path(cert_path).name))


