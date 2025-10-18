import django

from w.django.w_command import WCommand
from w.services.technical.maintenance_mode_service import MaintenanceModeService


class AbstractMaintenanceModeCommand(WCommand):
    args = "<on|off>"
    help = (
        "run python manage.py maintenance_mode %s "
        "to change maintenance-mode state" % args
    )

    def add_arguments(self, parser):
        parser.add_argument("state")

    def handle(self, *args, **options):
        if django.VERSION < (1, 8):
            if len(args) != 1:
                raise self.error(msg=f"Expected 1 argument: {self.args}")

            state = args[0]
        else:
            state = options["state"]

        state = state.lower()

        if state in ["on", "yes", "true", "1"]:
            MaintenanceModeService.enable()
            self.success(msg="maintenance_mode : on")
        elif state in ["off", "no", "false", "0"]:
            MaintenanceModeService.disable()
            self.success(msg="maintenance_mode : off")
        else:
            raise self.error(f"Invalid argument: '{state}' expected {self.args}")
