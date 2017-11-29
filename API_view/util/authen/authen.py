#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "half apple"
# Date: 2017/11/21
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from API import models



#############认证相关###########
class MyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        tk = request.query_params.get('tk')
        # print(tk)
        token_obj = models.Token.objects.filter(token=tk).first()
        # print(token_obj,'token_objtoken_objtoken_objtoken_obj')
        if token_obj:
            return (token_obj.user, token_obj)
        else:
            return (None,None)

    def authenticate_header(self, request):
        pass
        # return 'Basic realm=api'

