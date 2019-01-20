from __future__ import print_function, unicode_literals

import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from redis import ConnectionPool as RedisConnectionPool
from redis import Redis

from redis.connection import UnixDomainSocketConnection, Connection
from redis.connection import DefaultParser


CONNECTION_KWARGS = {
    'url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
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

        location = kwargs.get('url', None)
        if not location:
            raise ImproperlyConfigured("no `location` key on connection kwargs")

        params = {
            'url': location,
            'connection_class': Connection,
        }

        if location.startswith("unix:"):
            params['connection_class'] = UnixDomainSocketConnection
            params['path'] = location[5:]

        cls.pools[pool_key] = RedisConnectionPool.from_url(**params)
        return cls.pools[pool_key]


def redis_connect():
    pool = ConnectionPoolManager.connection_pool(**CONNECTION_KWARGS)
    return Redis(connection_pool=pool)