from django.apps import AppConfig

class SmeappConfig(AppConfig):
    name = 'smeApp'

    def ready(self):
        import smeApp.signals
