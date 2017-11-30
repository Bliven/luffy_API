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
    url(r'^api/(?P<version>\w+)/course/$', views.Course.as_view(), name='course'),
    url(r'^api/(?P<version>\w+)/course/(?P<pk>\d+)/$', views.Course.as_view(), name='course'),
    url(r'^api/(?P<version>\w+)/orderclear/$', views.OrderClear.as_view(), name='orderclear'),
    url(r'^api/(?P<version>\w+)/ordercompute/$', views.OrderCompute.as_view(), name='ordercompute'),
]

# [{'normal_coupon': {'1': {'id': 1, 'name': '测试通用券1', 'brief': '测试通用券1', 'coupon_type': 0, 'money_equivalent_value': 10,
#                           'off_percent': None, 'minimum_consume': 0, 'content_type': None, 'object_id': None,
#                           'quantity': 10000000, 'open_date': '2017-11-01', 'close_date': '2018-06-01',
#                           'valid_begin_date': None, 'valid_end_date': None, 'coupon_valid_days': None},
#                     '2': {'id': 2, 'name': '测试通用券2', 'brief': '测试通用券2', 'coupon_type': 1, 'money_equivalent_value': 10,
#                           'off_percent': None, 'minimum_consume': 100, 'content_type': None, 'object_id': None,
#                           'quantity': 1000000, 'open_date': '2017-11-01', 'close_date': '2018-07-06',
#                           'valid_begin_date': None, 'valid_end_date': None, 'coupon_valid_days': None}}, 'score': 100},
#
#
#
#
#  OrderedDict([('id', 1), ('name', '21天学会python'), ('course_img', '/src/assets/course-1.png'), ('price_policy', None), (
#  'course_coupon', {'3': {'id': 3, 'name': '课程测试券1', 'brief': '课程测试券1', 'coupon_type': 0, 'money_equivalent_value': 20,
#                          'off_percent': None, 'minimum_consume': 0, 'content_type': 9, 'object_id': 1, 'quantity': 10,
#                          'open_date': '2017-11-29', 'close_date': '2018-05-04', 'valid_begin_date': None,
#                          'valid_end_date': None, 'coupon_valid_days': None}})]),
#  OrderedDict(
#     [('id', 2), ('name', 'Django框架'), ('course_img', '/src/assets/course-2.png'), ('price_policy', None), (
#     'course_coupon', {
#         '4': {'id': 4, 'name': '课程测试券2', 'brief': '课程测试券2', 'coupon_type': 1, 'money_equivalent_value': 30,
#               'off_percent': None, 'minimum_consume': 80, 'content_type': 9, 'object_id': 2, 'quantity': 1,
#               'open_date': '2017-11-29', 'close_date': '2018-02-02', 'valid_begin_date': None, 'valid_end_date': None,
#               'coupon_valid_days': None}})])
#
#
#  ]
