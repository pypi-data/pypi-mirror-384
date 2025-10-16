from django.apps import AppConfig
from django.conf import settings

# Add our custom database router to redirect to the proper database
if (
    hasattr(settings, "DATABASE_ROUTERS")
    and "NEMO_osticket.routers.OsTicketDatabaseRouter" not in settings.DATABASE_ROUTERS
):
    settings.DATABASE_ROUTERS.append("NEMO_osticket.routers.OsTicketDatabaseRouter")
else:
    setattr(settings, "DATABASE_ROUTERS", ["NEMO_osticket.routers.OsTicketDatabaseRouter"])


class OsTicketConfig(AppConfig):
    name = "NEMO_osticket"
    verbose_name = "osTicket"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """
        This code will be run when Django starts.
        """
