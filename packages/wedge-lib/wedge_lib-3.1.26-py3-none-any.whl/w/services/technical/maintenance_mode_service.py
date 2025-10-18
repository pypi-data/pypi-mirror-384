from django.conf import settings

from w.services.technical.filesystem_service import FilesystemService


class MaintenanceModeService:
    maintenance_file = ".maintenance"

    @staticmethod
    def is_on() -> bool:
        return FilesystemService.is_file_exists(
            f"{settings.BASE_DIR}/{MaintenanceModeService.maintenance_file}"
        )

    @staticmethod
    def enable() -> None:
        if not MaintenanceModeService.is_on():
            FilesystemService.write_file(
                f"{settings.BASE_DIR}/{MaintenanceModeService.maintenance_file}", ""
            )

    @staticmethod
    def disable() -> None:
        if MaintenanceModeService.is_on():
            FilesystemService.remove(
                f"{settings.BASE_DIR}/{MaintenanceModeService.maintenance_file}"
            )
