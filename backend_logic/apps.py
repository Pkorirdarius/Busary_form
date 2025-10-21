from django.apps import AppConfig


class BackendLogicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend_logic'
    verbose_name = 'Bursary Applications'

    def ready(self):
        """
        Import signals when Django starts
        This ensures signal handlers are registered
        """
        import backend_logic.signals  # noqa