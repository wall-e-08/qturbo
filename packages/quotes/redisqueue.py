from __future__ import print_function, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from redis import ConnectionPool as RedisConnectionPool
from redis import Redis

from redis.connection import UnixDomainSocketConnection, Connection
from redis.connection import DefaultParser


HOST = getattr(settings, "REDIS_HOST", 'localhost')
PORT = getattr(settings, 'REDIS_PORT', 6379)
DB = getattr(settings, "REDIS_DB", 1)

CONNECTION_KWARGS = {
    'location': '{0}:{1}'.format(HOST, PORT),
    'db': 0,
}


class ConnectionPoolManager(object):
    pools = {}

    @classmethod
    def key_for_kwargs(cls, kwargs):
        return ":".join([str(v) for v in kwargs.values()])

    @classmethod
    def connection_pool(cls, **kwargs):
        pool_key = cls.key_for_kwargs(kwargs)
        if pool_key in cls.pools:
            return cls.pools[pool_key]

        location = kwargs.get('location', None)
        if not location:
            raise ImproperlyConfigured("no `location` key on connection kwargs")

        params = {
            'connection_class': Connection,
            'db': kwargs.get('db', 0),
            'password': kwargs.get('password', None),
        }

        if location.startswith("unix:"):
            params['connection_class'] = UnixDomainSocketConnection
            params['path'] = location[5:]
        else:
            try:
                params['host'], params['port'] = location.split(":")
                params['port'] = int(params['port'])

            except ValueError:
                raise ImproperlyConfigured("Invalid `location` key syntax on connection kwargs")

        cls.pools[pool_key] = RedisConnectionPool(**params)
        return cls.pools[pool_key]


def redis_connect():
    pool = ConnectionPoolManager.connection_pool(**CONNECTION_KWARGS)
    return Redis(connection_pool=pool)
