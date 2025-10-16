from NEMO_osticket.apps import OsTicketConfig


OSTICKET_DB_NAME = "osticket"


class OsTicketDatabaseRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == OsTicketConfig.name:
            return OSTICKET_DB_NAME
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == OsTicketConfig.name:
            return OSTICKET_DB_NAME
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == OsTicketConfig.name:
            return False
        return db == "default"
