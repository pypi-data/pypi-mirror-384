from dataclasses import dataclass

from deployman.connectors.base import Connector
from deployman.connectors.ssh import SSHConnector
from deployman.models import Target


@dataclass
class ConnectorFactory:

    @staticmethod
    def create(target: Target) -> Connector:
        if target.connector == "ssh":

            return SSHConnector(target)
        raise ValueError(f"Unsupported connector type: {target.connector}")