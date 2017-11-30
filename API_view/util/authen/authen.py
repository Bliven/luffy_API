from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from API import models
from rest_framework.exceptions import AuthenticationFailed


#############认证相关###########
class MyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        tk = request.query_params.get('tk')
        token_obj = models.Token.objects.filter(token=tk).first()
        if token_obj:
            return (token_obj.user, token_obj)
        else:
            raise exceptions.AuthenticationFailed("用户认证失败")


    def authenticate_header(self, request):
        pass
        # return 'Basic realm=api'

