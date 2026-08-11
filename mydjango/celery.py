import os

from celery import Celery


def _patch_redis_protocol():
    try:
        import redis.connection as redis_connection
    except Exception:
        return

    def _wrap_init(original_init):
        if getattr(original_init, "_mydjango_protocol_patched", False):
            return original_init

        def patched_init(self, *args, **kwargs):
            kwargs.setdefault("protocol", 2)
            kwargs.setdefault("maint_notifications_config", None)
            return original_init(self, *args, **kwargs)

        patched_init._mydjango_protocol_patched = True
        return patched_init

    redis_connection.Connection.__init__ = _wrap_init(redis_connection.Connection.__init__)

    for pool_name in ("ConnectionPool", "BlockingConnectionPool"):
        pool_cls = getattr(redis_connection, pool_name, None)
        if pool_cls is None:
            continue
        pool_init = getattr(pool_cls, "__init__", None)
        if pool_init is None or getattr(pool_init, "_mydjango_protocol_patched", False):
            continue

        def make_pool_init(original_init):
            def patched_init(self, *args, **kwargs):
                kwargs.setdefault("protocol", 2)
                kwargs.setdefault("maint_notifications_config", None)
                return original_init(self, *args, **kwargs)

            patched_init._mydjango_protocol_patched = True
            return patched_init

        pool_cls.__init__ = make_pool_init(pool_init)

    try:
        import redis
        redis.Connection.__init__ = redis_connection.Connection.__init__
    except Exception:
        return


_patch_redis_protocol()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mydjango.settings")
app = Celery("mydjango")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
