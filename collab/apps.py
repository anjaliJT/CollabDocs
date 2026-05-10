from django.apps import AppConfig


class CollabConfig(AppConfig):
    name = 'collab'

    def ready(self):
        from . import signals  # noqa: F401
