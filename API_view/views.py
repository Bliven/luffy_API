from django.shortcuts import render

# Create your views here.
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from rest_framework import views, serializers, fields
from django.core.exceptions import ObjectDoesNotExist
from API import models


def gen_token(username):
    """
    获取生成token随机字符串！
    :param username:
    :return:
    """
    import time
    import hashlib
    ctime = str(time.time())
    hash = hashlib.md5(username.encode("utf-8"))
    hash.update(ctime.encode("utf-8"))
    return hash.hexdigest()


class AuthView(views.APIView):
    """
    用户认证类，已经在中间件解决CORS跨域问题！
    """

    def post(self, request, *args, **kwargs):
        """
        获取用户提供的 用户和密码，如果用户名和密码正确，则生成token，并且返回给客户端，下次登录时携带token。
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = {"code": 1000, "msg": None, "user": None}
        user = request.data.get("user")
        pwd = request.data.get("pwd")
        # password = make_password(pwd)
        user_obj = models.UserInfo.objects.filter(user=user).first()
        check_pwd = check_password(pwd, user_obj.pwd)
        if check_pwd:
            tk = gen_token(user)
            models.Token.objects.get_or_create(user=user_obj, defaults={"token": tk})
            ret["code"] = 1001
            ret["user"] = user
            ret["token"] = tk
        else:
            ret["msg"] = "用户名或密码错误！"
        response = JsonResponse(ret)
        return response


class LeverChield(fields.CharField):
    """
    定制leve字段，将本身是选择id的内容转换成文字：难度：中级。
    """

    def to_representation(self, value):
        return models.Course.level_choices[value][1]


class CoursesSerializer(serializers.Serializer):
    """
    定制课程序列化类
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    brief = serializers.CharField()
    level = LeverChield()
    course_img = serializers.CharField()  # 前端显示的图片路径用于课程列表显示不同的图片！


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    定制课程详情类，序列化操作！
    """
    name = serializers.CharField(source="course.name")
    course_id = serializers.IntegerField()
    course_brief = serializers.CharField(source="course.brief")
    recommend_courses_list = serializers.SerializerMethodField()
    course_level = serializers.CharField(source="course.get_level_display")
    teachers = serializers.ListField(child=serializers.CharField(), source="teachers.all")
    price_policy_list = serializers.SerializerMethodField()

    def get_price_policy_list(self, obj):
        ret = []
        price_policy_list = obj.course.price_policy.all()
        for item in price_policy_list:
            ret.append({"id": item.id, "valid_period": item.get_valid_period_display(), "price": item.price})
        return ret

    class Meta:
        model = models.CourseDetail
        fields = "__all__"

    def get_recommend_courses_list(self, obj):
        ret = []
        course_list = obj.recommend_courses.all()
        for item in course_list:
            ret.append({"id": item.id, "name": item.name})
        return ret


class Course(views.APIView):
    def get(self, request, *args, **kwargs):
        course_data = {"code": 1000, "msg": None, "data": None}
        try:
            pk = kwargs.get("pk")
            print("____pk", pk)
            if pk:
                course_detail = models.CourseDetail.objects.get(course_id=pk)
                course_list = CourseDetailSerializer(instance=course_detail, many=False)
                print("-----", course_list.data)
            else:
                course = models.Course.objects.exclude(course_type=2)
                course_list = CoursesSerializer(instance=course, many=True)
                print("___________data", course_data)
            course_data["data"] = course_list.data
            print("________course_data", course_data)
        except ObjectDoesNotExist as e:
            course_data["code"] = 1001
            course_data["msg"] = "查找课程不存在！"
        except Exception as e:
            course_data["code"] = 1002
            course_data["msg"] = "查询课程失败！"
        print("______course_data",course_data)
        return JsonResponse(course_data)


class Create_password(views.APIView):
    def post(self, request, *args, **kwargs):
        user = request.data.get("user")
        pwd = request.data.get("course_id")
        email = request.data.get("pricePolicy_id")
        password = make_password(pwd)
        models.UserInfo.objects.create(user=user, pwd=password, email=email)
        return JsonResponse("OK", safe=False)

    def get(self, request, *args, **kwargs):
        pass


#######################购物车相关##############

shopping_cart = {}


class PricePolicySerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="get_valid_period_display")
    class Meta:
        model = models.PricePolicy
        fields = ['id', 'price', 'name']



class ShoppingCart(views.APIView):
    def get(self, request, *args, **kwargs):

        pass
    def post(self, request, *args, **kwargs):
        ret = {"code": 1000, "msg": None}
        user = request.POST.get('user')
        course_id = request.POST.get('course_id')
        pricepolicy_id = request.POST.get('pricepolicy_id')
        print(course_id, user, pricepolicy_id)
        # try:
        pricepolicy_obj = models.PricePolicy.objects.filter(pk=pricepolicy_id).first()
        course_obj=models.Course.objects.filter(pk=course_id).first()
        if pricepolicy_obj.content_object == course_obj:
            """
            判断课程是否有这个价格
            """
            pricepolicy_list = course_obj.price_policy.all()
            pricepolicy_list = PricePolicySerializer(instance=pricepolicy_list, many=True)

            shopping_cart[user] = {course_obj.pk:{

                'name':course_obj.name,
                'img':course_obj.course_img,
                'pricepolicy_id': pricepolicy_id,
                'policy_list': pricepolicy_list.data
                }
            }
            ret['msg'] = '添加成功'


        else:
            ret['code'] = 1001
            ret['msg'] = '没有这个价格'
        # except Exception as e:
        #     ret['code'] = 1001
        #     print(e)
        #     ret['code'] = '错误'
        print(shopping_cart)
        response = JsonResponse(ret)
        return response



    def delete(self, request, *args, **kwargs):

        pass
    def put(self, request, *args, **kwargs):

        pass