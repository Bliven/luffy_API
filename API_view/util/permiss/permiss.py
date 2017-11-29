#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "half apple"
# Date: 2017/11/21


from rest_framework.permissions import BasePermission
from app01 import views


class MyPermission(BasePermission):
    message = '无权限'
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        print(request.user)
        if request.user == None and isinstance(view, views.OrderView) and request._request.method == "GET":
            return False

        return True

    # def has_object_permission(self, request, view, obj):
    #     """
    #     Return `True` if permission is granted, `False` otherwise.
    #     """
    #     return True