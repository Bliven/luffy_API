
from django.shortcuts import render, HttpResponse

from API.repertory_api import search
import json
from django.forms.models import model_to_dict  # ^^^^^^


# Create your views here.
from django.http import JsonResponse
from rest_framework import views, serializers, fields
from rest_framework.response import Response
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

    def get(self, name, k):
        return self.conn.hget(name, k)





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

class OrderClear(views.APIView):
    def get(self, request, *args, **kwargs):
        ret = {"code": 1000, "msg": None}
        try:
            # user_tk=request.query_params.get("tk")
            user_obj = models.Account.objects.filter(pk=request.user.id).first()
            if user_obj:
                obj=rediser.get('goods_list', user_obj.id).decode("utf-8")     # 取 购物车 优惠券数据
                goods = json.loads(obj)
                ret["data"] = self.get_data(goods, request)
                rediser.set('OrderClear', request.user.id, ret["data"])
                # print(rediser.get('OrderClear', request.user.id, ).decode("utf-8"), '-----------------')
                # print(type(ret["data"]), '-----------------')  # str
        except Exception as e:
            print(e)
            ret["msg"]="没有该数据"
            ret["code"]=1001
        return Response(ret)

    # def post(self, request, *args, **kwargs):
    #     order = request.data
    #     order = [{'course_id': 1,
    #               'price_policy_id': 1,
    #               'coupon': {
    #                   'normal_coupon': 2,
    #                   'course_coupon': 3},
    #               'score': True}]


    def get_data(self, goods, request, *args, **kwargs):
        '''
        购物车过来合法数据之后，取出课程和相关优惠券
        :param goods:
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        # ------ 通用优惠券 ----------
        user_obj = models.Account.objects.get(id=1)  # ------------------------------TTTTTest
        # user_obj=request.user                      # -------------------------------------TTTTTTTTTTT
        all_coupon_rd_qset = user_obj.couponrecord_set.all().select_related('coupon')
        normal_coupon_l = []
        for cprd_obj in all_coupon_rd_qset:
            if cprd_obj.status == 0 and not cprd_obj.coupon.object_id:  # 取用户有的优惠券
                d = model_to_dict(cprd_obj.coupon)
                d['open_date'] = str(d.get('open_date'))
                d['close_date'] = str(d.get('close_date'))
                normal_coupon_l.append(d)
        user_info = [{'normal_coupon': {}}]
        for coupon_info in normal_coupon_l:
            user_info[0]['normal_coupon'][str(coupon_info.get('id'))] = coupon_info

        # ------ 贝里 ----------

        score_records = user_obj.transactionrecord_set.all()
        score = score_records[len(score_records) - 1].balance
        user_info[0]['score'] = score

        # ------ 课程优惠券以及其他 ----------

        def func_pp(self, obj):  # price_policy 查询使用
            price_p = obj.price_policy.all()
            try:
                for l in goods:
                    if l['course_id'] == obj.id:
                        plc_obj = price_p.get(id=l["policy_id"])
                        re = {'id': plc_obj.id, 'price': plc_obj.price, 'valid_period': plc_obj.valid_period}
                        return re
            except TypeError as e:
                print('price_policy 查询----', e)

        def func_coupon(self, obj):  # coupon 查询使用
            course_coupon = obj.coupon.all()
            course_cp_l = []
            try:
                for cp_obj in course_coupon.filter(id__in=all_coupon_rd_qset.values_list('id')):  # 取课程特定优惠券
                    d = model_to_dict(cp_obj)
                    d['open_date'] = str(d.get('open_date'))
                    d['close_date'] = str(d.get('close_date'))
                    course_cp_l.append(d)
            except TypeError as e:
                print('coupon 查询----', e)
            return course_cp_l

        res = []
        for course in goods:
            id = course.get('course_id')
            if id:
                res.append(id)

        data_list = models.Course.objects.filter(id__in=res)
        data = search.instance_serilize(instance='Course', data=data_list,
                                        fields=['id', 'name', 'course_img', 'price_policy', 'course_coupon', ],
                                        serializerMDF={'price_policy': func_pp, 'course_coupon': func_coupon,}
                                        )
        for course_info in data:
            try:
                cp_l = course_info.get('course_coupon')
                course_info['course_coupon'] = {}
                for cp in cp_l:
                    course_info['course_coupon'][str(cp.get('id'))] = cp
            except TypeError as e:
                print('返回数据data----', e)

        return json.dumps(user_info + data)


class OrderCompute(views.APIView):
    def get(self, request, *args, **kwargs):
        order_data = {
            "goods": [
                {
                    "course_id": 1,
                    "policy_id": 3,
                    "course_coupon": 5
                },
                # {
                #     "course_id": 2,
                #     "policy_id": 2,
                #     "course_coupon": 2
                # }
            ],
            "global_coupon": 3,
            "use_berry": True,
            "money": 555
        }
        ret = {"code": 1000, "msg": None, "total_price": None, "berry_pay": False}
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
            ret["msg"] = e
            ret["code"] = 1001
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
            ret["msg"] = e
            ret["code"] = 1001
            return Response(ret)

        "贝里"
        try:
            if order_data["use_berry"]:
                berry_balance = models.TransactionRecord.objects.get(account_id=request.user.id).balance

                if berry_balance > 100 * total_price:
                    ret["berry_pay"] = True
                else:
                    total_price -= berry_balance / 100
                    ret["total_price"] = total_price
        except Exception as e:
            ret["msg"] = e
            ret["code"] = 1001
            return Response(ret)

        return Response(ret)

    def course_coupon_compute(self, request, func_list, order_data):
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
            print("a", e)
        return total_price

    def ordinary_compute(self, coupon_obj, price):
        ''' 普通券计算 '''
        if price > coupon_obj.coupon.money_equivalent_value:
            end_price = price - coupon_obj.coupon.money_equivalent_value
        else:
            end_price = 0
        return end_price

    def fullcut_compue(self, coupon_obj, price):
        ''' 满减券计算 '''
        if price > coupon_obj.coupon.minimum_consume:
            end_price = price - coupon_obj.coupon.money_equivalent_value
        else:
            end_price = price
        return end_price

    def discount_compute(self, coupon_obj, price):
        ''' 折扣券计算 '''
        end_price = price * coupon_obj.coupon.off_percent / 100
        return end_price
