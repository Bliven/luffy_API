#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "half apple"
# Date: 2017/11/22

from rest_framework.throttling import SimpleRateThrottle

class MyAnonRateThrottle(SimpleRateThrottle):

    scope = "luffy_anon"

    def allow_request(self, request, view):

        if request.user:
            return True

        self.key = self.get_cache_key(request, view)
        self.history = self.cache.get(self.key, [])

        self.now = self.timer()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()

        return self.throttle_success()

    def get_cache_key(self, request, view):
        return "throttle_%(scope)s_%(ident)s" %{
            'scope': self.scope,
            'ident': self.get_ident(request)
        }


class MyUserRateThrottle(SimpleRateThrottle):
    scope = "luffy_user"

    def allow_request(self, request, view):
        if not request.user:
            return True

        self.key = request.user.user
        print(self.key)
        self.history = self.cache.get(self.key, [])

        self.now = self.timer()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()

        return self.throttle_success()