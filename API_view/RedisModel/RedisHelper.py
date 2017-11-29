#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "half apple"
# Date: 2017/11/29

import redis


class RedisHelper(object):
    def __init__(self):
        import redis

        pool = redis.ConnectionPool(host='65.49.195.128', port=6379)
        conn = redis.Redis(connection_pool=pool)
        self.conn = conn

    def set(self, name, k, v):
        self.conn.hset(name, k, v)

    def delete(self, name, k):
        self.conn.hdel(name, k)

    def get(self,name, k):
        return self.conn.hget(name, k)


rediser= RedisHelper()

