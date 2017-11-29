from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from . import models

"""
这个文件主要整合了序列化的操作——五种 主要方法

class ModelUserSerializer(serializers.ModelSerializer):
    # 五种 主要方法
    # 1-- 循环所有queryset # 太low没写
    # 2-- choices
    #   role = serializers.CharField(source='get_role_display')  # 可以点点点找多级
    # 3-- ManyToMany  role = serializers.CharField(source='[字段].all')  # 可以多对多
    # 4--
    # class MyCharField(serializers.CharField):
    #     def get_attribute(self, instance):  # 返回单一字段
    #         return instance.get_some_field_display()
    #     def to_representation(self, instance):
    #        return instance.get_some_field_display()

    # 5-- SerializerMethodField
    # from rest_framework.fields import SerializerMethodField
    # some_field = SerializerMethodField()
    # def get_some_field(self,obj):
    #     return obj.get_some_field_display() # 这里 obj 是一个model 对象 # 这里是选项名的显示方法


    class Meta:
        model = models.Account
        fields = ['id','role']
"""
"""
参数以及使用方法：

可以传入 data = queryset 或者不传 查询.all()

get 和 filter 就是提供和 object.get , object.filter 一样的功能
search.get( 数据库名(字符串),索索条件 )
search.filter( 数据库名(字符串),索索条件 )

search.instance_serilize(
        instance = [数据库名(字符串)]，
        fields = 默认是‘__all__’，传入列表，
        extra_fields = [自定义字段(字符串)]，extra_fields_info = [字段的查询条件]，
            # 这两个参数接收列表，两个列表元素一一对应
            # 如果是自己定义了 CharField 字段，将字段实例化好之后传进来
                e.g.：class MyCharField(serializers.CharField):
                        def to_representation(self, instance):
                            return '77777'
                      info=MyCharField()
                extra_fields_info = info
            # extra_fields = [‘role’,role2] , extra_fields_info = ['get_role_display','get_role_display2']
            # 这两句代替类似的操作：
            # role = serializers.CharField(source='get_role_display')
            # role2 = serializers.CharField(source='get_role_display2')

        serializerMDF = { field名：函数，field名2：函数2 }
            # 等同于操作：
            # from rest_framework.fields import SerializerMethodField
            # some_field = SerializerMethodField()
            # def get_some_field(self,obj): # 这里的函数是传入的函数
            #     return obj.get_some_field_display() #
        )

"""
"""
使用案例：

from rest_framework import serializers
class MyCharField(serializers.CharField):
    def to_representation(self, instance):
       return '77777'
info=MyCharField()

def func(*args,**kwargs):
    return '66666'
data_l =models.Account.objects.all()

data = search.instance_serilize(
        'Account',data=data_l,fields=['username','id','role','uid','mobile','xxxx'],
        extra_fields=['role','uid'],extra_fields_info=['uid',info],
        serializerMDF={'mobile':func,'xxxx':func}
        )
返回结果——  OrderedDict([('username', 'alex'), ('id', 1), ('role', '534b44a19bf18d20b71ecc4eb77c572f'), ('uid', '77777'), ('mobile', '66666'), ('xxxx', '66666')])

等同于：

class ModelUserSerializer(serializers.ModelSerializer):

    from rest_framework import serializers
    class MyCharField(serializers.CharField):
        def to_representation(self, instance):
           return '77777'

    role = serializers.CharField(source='uid')
    uid = serializers.MyCharField()

    # SerializerMethodField
    from rest_framework.fields import SerializerMethodField
    mobile = SerializerMethodField()
    def get_mobile(self,obj):
        return '66666'
    xxxx = SerializerMethodField()
    def get_xxxx(self,obj):
        return '66666'

    class Meta:
        model = models.Account
        fields = ['username','id','role','uid','mobile']

返回结果——  OrderedDict([('username', 'alex'), ('id', 1), ('role', '534b44a19bf18d20b71ecc4eb77c572f'), ('uid', '学员'), ('mobile', '66666'), ('xxxx', '66666')])
"""

class Search(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
          orig = super(Search, cls)
          cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def get(self,instance,*args,**kwargs):
        if hasattr(models,instance):
            md_obj = getattr(models,instance)
            try:
                return md_obj.objects.get(*args,**kwargs)
            except Exception as e:
                print(e)
                return None

    def filter(self,instance,*args,**kwargs):
        if hasattr(models,instance):
            md_obj = getattr(models,instance)
            return md_obj.objects.filter(*args,**kwargs)

    @staticmethod
    def __gen_serilizer(instance,fields="__all__",extra_fields=None,extra_fields_info=None,serializerMDF=None):
        """
        动态生成序列化类
        :param instance:
        :param args:
        :return:
        """
        _meta = type('Meta', (object,), {'model': instance, "fields": fields,})

        md_dict = {
            'Meta': _meta
        }
        if extra_fields and len(extra_fields_info)==len(extra_fields):
            for i in range(len(extra_fields)):
                if not isinstance(extra_fields_info[i],str):
                    md_dict[extra_fields[i]] = extra_fields_info[i]    # 作为自定义的CharField
                else:
                    md_dict[extra_fields[i]] = serializers.CharField(source=extra_fields_info[i])  # 只自定义了字段
        if serializerMDF:
            for f_name,f_func in serializerMDF.items():
                md_dict[f_name]=SerializerMethodField()
                md_dict['get_'+f_name]=f_func
        # print(md_dict)
        ModelSerializer = type('DynamicModel',(serializers.ModelSerializer,), md_dict)
        return ModelSerializer

    def instance_serilize(self,instance,data=None,fields="__all__",extra_fields=None,extra_fields_info=None,serializerMDF=None):
        if hasattr(models,instance):
            md_obj = getattr(models,instance)
            from django.db.models.query import QuerySet
            if not isinstance(data,QuerySet):
                data = md_obj.objects.all()
            print(type(data))
            ModelSerializer = self.__gen_serilizer(md_obj,fields=fields,
                                                   extra_fields=extra_fields,
                                                   extra_fields_info=extra_fields_info,
                                                   serializerMDF=serializerMDF)      # 动态序列化类

            ser = ModelSerializer(instance=data,many=True)
            ser_data = ser.data[0]
            return ser_data

search=Search()