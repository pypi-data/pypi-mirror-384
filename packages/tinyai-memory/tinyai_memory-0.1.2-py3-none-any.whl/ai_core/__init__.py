from .tinyai import TinyAIMemory  # or your main class
from .apps import AiCoreConfig

__all__ = ["TinyAIMemory", "AiCoreConfig"]

# Optional: allow standalone use
def setup(sqlite_path: str = "tinyai.db", auto_migrate: bool = True):
    """Allow running without a Django project (uses local SQLite)."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "ai_core",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": sqlite_path,
                }
            },
            USE_TZ=True,
            TIME_ZONE="UTC",
            SECRET_KEY="tinyai-standalone",
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )

    import django
    django.setup()

    if auto_migrate:
        from django.core.management import call_command
        call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)
