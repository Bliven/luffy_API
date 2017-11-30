from django.shortcuts import render, HttpResponse

# Create your views here.
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from rest_framework import views, serializers, fields
from django.core.exceptions import ObjectDoesNotExist
from API import models
from API_view.util.authen.authen import MyAuthentication
from API_view.RedisModel.RedisHelper import rediser
import json


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
    authentication_classes = []
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
        user_obj = models.Account.objects.filter(username=user, password=pwd).first()
        if user_obj:
            tk = gen_token(user)
            models.Token.objects.update_or_create(user=user_obj, defaults={"token": tk})
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
        print("______course_data", course_data)
        return JsonResponse(course_data)




#######################购物车相关##############




class PricePolicySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_valid_period_display")

    class Meta:
        model = models.PricePolicy
        fields = ['id', 'price', 'name']

def goods_list(user_cart_list):
    """
    将
    :param user_cart_list: 
    :return: 
    """
    l = []
    for item in user_cart_list:
        dic = {'course_id':item, 'policy_id': user_cart_list[item]['pricepolicy_id']}
        l.append(dic)
    return l


def policydict(pric_list):
    dict = {}
    for item in pric_list:

        dict[item['id']] = {'id': item['id'], 'price': item['price'], 'name': item['name']}


        # dict[item['id']]=list(item)
    print(dict)
    return dict


class ShoppingCart(views.APIView):
    # authentication_classes = [MyAuthentication, ]

    def get(self, request, *args, **kwargs):
        """
        访问购物车页面，从redis取出用户在购物车所有商品信息。
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        user_id = request.user.id
        print(user_id)
        print(type(user_id))

        user_cart_list = rediser.get('shopping_list', user_id)

        if user_cart_list:
            user_cart_list = json.loads(user_cart_list.decode('utf-8'))

            return JsonResponse(user_cart_list,safe=False)
        else:
            return HttpResponse('为空')

    def post(self, request, *args, **kwargs):
        """
        当在商品页面选择添加购物车时候,获取商品id以及价格策略id
        
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        ret = {"code": 1000, "msg": None}
        user_id = request.user.id
        course_id = request.data.get('course_id')
        pricepolicy_id = request.data.get('pricepolicy_id')

        # try:
        pricepolicy_obj = models.PricePolicy.objects.filter(pk=pricepolicy_id).first()
        course_obj = models.Course.objects.filter(pk=course_id).first()
        if pricepolicy_obj and course_obj and pricepolicy_obj.content_object == course_obj:
            """
            判断课程是否有这个价格策略
            """
            pricepolicy_list = course_obj.price_policy.all()
            pricepolicy_list = PricePolicySerializer(instance=pricepolicy_list, many=True)

            dic = {'name': course_obj.name,
                    'img': course_obj.course_img,
                    'pricepolicy_id': pricepolicy_id,
                    'price':pricepolicy_obj.price,
                    'policy_dic': policydict(pricepolicy_list.data)
             }

            user_cart_dict = rediser.get('shopping_list', user_id)
            if user_cart_dict:
                user_cart_dict = json.loads(user_cart_dict.decode('utf-8'))
                user_cart_dict[course_id] = dic
            else:
                user_cart_dict = {
                    course_id: dic
                }
            rediser.set('shopping_list', request.user.id, json.dumps(user_cart_dict))
            rediser.set('goods_list', request.user.id, json.dumps(goods_list(user_cart_dict)))
            ret['msg'] = '添加成功'
        else:
            ret['code'] = 1001
            ret['msg'] = '没有这个价格'
        response = JsonResponse(ret)
        return response

    def delete(self, request, *args, **kwargs):
        """
        从购物车删除某一条课程或者多条课程或者全部课程(清空)
        {'kind':'only','id':'1'}
        {'kind':'many','id':['1','2']}
        {'kind':'all',}
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        ret = {"code": 1000, "msg": None}
        user_id = request.user.id
        kind = request.data.get('kind')
        id = request.data.get('id')
        user_cart_dict = rediser.get('shopping_list', user_id)
        user_cart_dict = json.loads(user_cart_dict.decode('utf-8'))
        if kind == 'only':
            user_cart_dict.pop(id)
        elif kind == 'many':
            for item in id:
                user_cart_dict.pop(item)
        elif kind == 'both':
            rediser.delete('shopping_list', str(user_id))
            rediser.delete('goods_list', str(user_id))
        else:
            ret['code'] = 1001
            ret['msg'] = '购物车删除失败!,参数错误'
            return JsonResponse(ret)
        rediser.set('shopping_list', user_id, json.dumps(user_cart_dict))
        rediser.set('goods_list', user_id, json.dumps(goods_list(user_cart_dict)))
        ret['msg'] = '删除成功'

        return JsonResponse(ret)

    def put(self, request, *args, **kwargs):
        """
        购物车修改,传入要修改的课程id,和价格策略id
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """

        ret = {"code": 1000, "msg": None}
        user_id = request.user.id
        course_id = request.data.get('course_id')
        pricepolicy_id = request.data.get('pricepolicy_id')
        pricepolicy_obj = models.PricePolicy.objects.filter(pk=pricepolicy_id).first()
        course_obj = models.Course.objects.filter(pk=course_id).first()
        if pricepolicy_obj and course_obj and pricepolicy_obj.content_object == course_obj:
            """
            判断课程是否有这个价格策略
            """
            user_cart_dict = rediser.get('shopping_list', user_id)
            user_cart_dict = json.loads(user_cart_dict.decode('utf-8'))
            if user_cart_dict.get(course_id):
                user_cart_dict[course_id]['pricepolicy_id'] = pricepolicy_id
                rediser.set('shopping_list', user_id, json.dumps(user_cart_dict))
                rediser.set('goods_list', user_id, json.dumps(goods_list(user_cart_dict)))
                ret['msg'] = '修改成功'

            else:
                ret['msg'] = '购物车里并没有这个商品'
                ret['code'] = 1002
        else:
            ret['code'] = 1001
            ret['msg'] = '没有这个价格策略'
        response = JsonResponse(ret)
        return response
