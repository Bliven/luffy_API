from django.shortcuts import render

from django.http import JsonResponse
from rest_framework import views, serializers, fields
from rest_framework.response import Response
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
        user_obj = models.Account.objects.filter(username=user,password=pwd).first()
        if user_obj:
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


class OrderClear(views.APIView):

    def get(self,request,*args,**kwargs):
        import json
        ret={"code":1000,"msg":None}
        try:
            # user_tk=request.query_params.get("tk")
            print(request.user.id)
            user_obj = models.Account.objects.filter(pk=request.user.id).first()
            if user_obj:
                obj=rediser.get("shopping_cart",request.user.id).decode("utf-8")
                ret["data"]=json.loads(obj)
        except Exception as e:
            ret["msg"]="没有该数据"
            ret["code"]=1001
        return Response(ret)

    def verify(self,data):
        ret={"code"}
        for i in data:
            obj = models.Course.objects.filter(id=i["course_id"]).first()
            if obj:
                if obj.price_policy.get(id=i["policy_id"]):

                    return True

    def get_data(self):
        pass

class OrderCompute(views.APIView):
    def get(self,request,*args,**kwargs):
        order_data={
            "goods":[
                {
                    "course_id": 1,
                    "policy_id": 3,
                    "course_coupon":5
                },
                # {
                #     "course_id": 2,
                #     "policy_id": 2,
                #     "course_coupon": 2
                # }
            ],
            "global_coupon":3,
            "use_berry": True,
            "money": 555
        }
        ret={"code":1000,"msg":None,"total_price":None,"berry_pay":False}
        func_list = ["ordinary_compute", "fullcut_compue", "discount_compute"]


        # 总价，最终的总价格
        total_price = 0

        try:
            for good_data in order_data["goods"]:
                '''每个视频绑定的课程优惠券的处理'''
                course_obj = models.Course.objects.get(id=good_data["course_id"])
                if good_data["course_coupon"]:
                    course_coupon_obj = models.CouponRecord.objects.get(number=good_data["course_coupon"],
                                                                        account_id=request.user.id)
                    course_price = course_obj.price_policy.get(id=good_data["policy_id"]).price
                    if course_coupon_obj and course_coupon_obj.coupon.object_id:
                        if hasattr(self, func_list[course_coupon_obj.coupon.coupon_type]):
                            compute_func = getattr(self, func_list[course_coupon_obj.coupon.coupon_type])
                            total_price += compute_func(course_coupon_obj, course_price)
        except Exception as e:
            ret["msg"]=e
            ret["code"]=1001
            return Response(ret)

        # "全局优惠券计算"
        try:
            if order_data["global_coupon"]:
                course_coupon_obj = models.CouponRecord.objects.get(number=order_data["global_coupon"],
                                                                    account_id=request.user.id)
                # print(course_coupon_obj.coupon.name)
                if course_coupon_obj and not course_coupon_obj.coupon.object_id:
                    if hasattr(self, func_list[course_coupon_obj.coupon.coupon_type]):
                        compute_func = getattr(self, func_list[course_coupon_obj.coupon.coupon_type])
                        total_price = compute_func(course_coupon_obj, total_price)
        except Exception as e:
            ret["msg"]=e
            ret["code"] = 1001
            return Response(ret)

        "贝里"
        try:
            if order_data["use_berry"]:
                berry_balance=models.TransactionRecord.objects.get(account_id=request.user.id).balance

                if berry_balance > 100 * total_price:
                    ret["berry_pay"]=True
                else:
                    total_price-=berry_balance/100
                    ret["total_price"]=total_price
        except Exception as e:
            ret["msg"]=e
            ret["code"] = 1001
            return Response(ret)

        return Response(ret)

    def course_coupon_compute(self,request,func_list,order_data):
        total_price=0
        try:
            for good_data in order_data["goods"]:
                '''每个视频绑定的课程优惠券的处理'''
                course_obj=models.Course.objects.get(id=good_data["course_id"])
                if good_data["course_coupon"]:
                    course_coupon_obj=models.CouponRecord.objects.get(number=good_data["course_coupon"],
                                                                      account_id=request.user.id)
                    course_price = course_obj.price_policy.get(id=good_data["policy_id"]).price
                    if course_coupon_obj and course_coupon_obj.coupon.object_id:
                        if hasattr(self, func_list[course_coupon_obj.coupon.coupon_type]):
                            compute_func=getattr(self, func_list[course_coupon_obj.coupon.coupon_type])
                            total_price+=compute_func(course_coupon_obj,course_price)
        except Exception as e:
            print("a",e)
        return total_price



    def ordinary_compute(self,coupon_obj,price):
        ''' 普通券计算 '''
        if price > coupon_obj.coupon.money_equivalent_value:
            end_price=price-coupon_obj.coupon.money_equivalent_value
        else:
            end_price=0
        return end_price

    def fullcut_compue(self,coupon_obj,price):
        ''' 满减券计算 '''
        if price > coupon_obj.coupon.minimum_consume:
            end_price=price-coupon_obj.coupon.money_equivalent_value
        else:
            end_price=price
        return end_price
    def discount_compute(self,coupon_obj,price):
        ''' 折扣券计算 '''
        end_price=price*coupon_obj.coupon.off_percent/100
        return end_price