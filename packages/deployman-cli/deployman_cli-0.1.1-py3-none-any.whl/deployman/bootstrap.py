from kink import di

from deployman.services.backup_service import BackupService
from deployman.services.deploy_service import DeployService
from deployman.services.targets_service import TargetsService


def bootstrap():
    di[TargetsService] = TargetsService()
    di[DeployService] = DeployService()
    di[BackupService] = BackupService()
