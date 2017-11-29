"""luffy_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from API_view import views
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/(?P<version>\w+)/auth/$', views.AuthView.as_view(), name='auth'),
    url(r'^(?P<version>\w+)/cr/$', views.Create_password.as_view(), name='yyyy'),
    url(r'^api/(?P<version>\w+)/course/$', views.Course.as_view(), name='course'),
    url(r'^api/(?P<version>\w+)/course/(?P<pk>\d+)/$', views.Course.as_view(), name='course'),

    url(r'^api/(?P<version>\w+)/shopping_cart/$', views.ShoppingCart.as_view(), name='shopping_cart'),

    url(r'^api/(?P<version>\w+)/orderclear/$', views.OrderClear.as_view(), name='orderclear'),
]
