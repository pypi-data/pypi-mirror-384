from xl_router.exceptions import MessagePrompt
from xl_router.utils.base.json import to_lowcase, iter_lowcase, iter_camel
from flask import Blueprint, request
from jsonschema.exceptions import ValidationError
import functools
import random
import os
import importlib
import inspect
import re


class ParamHandler:
    """处理请求参数的工具类"""
    
    @staticmethod
    def get_params():
        """根据请求类型获取参数"""
        if request.method in ['GET', 'DELETE']:
            return to_lowcase({**request.args, **request.view_args})
            
        if 'multipart/form-data' in request.content_type:
            return {
                **request.files,
                **to_lowcase(request.form.to_dict())
            }
            
        try:
            params = request.get_json()
            return iter_lowcase(params)
        except:
            return {'data': request.get_data()}

    @staticmethod
    def clean_params(params):
        """清理空值参数"""
        return {k: v for k, v in params.items() if v not in ('', 'null', None)}


class ResourceLoader:
    """资源类加载器"""
    
    @staticmethod
    def get_resource_classes_from_module(module, file_path=None):
        """从模块中获取资源类"""
        resource_classes = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name.endswith("Resource"):
                # 检查类是否有path属性，如果没有则自动生成
                if not hasattr(obj, 'path') or obj.path is None:
                    auto_path = ResourceLoader._generate_path_from_filename(file_path)
                    if auto_path is not None:
                        obj.path = auto_path
                resource_classes.append(obj)
        return resource_classes

    @staticmethod
    def _generate_path_from_filename(file_path):
        """根据文件名自动生成路径"""
        if not file_path:
            return None
            
        filename = os.path.basename(file_path)
        
        # 匹配 resource_xxx_yyy.py 模式
        pattern = re.compile(r'^resource_(.+)\.py$')
        match = pattern.match(filename)
        
        if match:
            # 将下划线分隔的部分转换为路径
            path_parts = match.group(1).split('_')
            return '/' + '/'.join(path_parts)
        
        # 匹配 resource.py 模式（简单情况）
        if filename == 'resource.py':
            return ''
        
        return None

    @staticmethod
    def get_resource_classes(resources_file):
        """从文件中获取所有资源类"""
        path = os.path.dirname(resources_file)
        resource_classes = []
        pattern = re.compile(r'.*resource(?!s).*\.py$')
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if pattern.match(file):
                    file_path = os.path.join(root, file)
                    spec = importlib.util.spec_from_file_location('module', file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    resource_classes += ResourceLoader.get_resource_classes_from_module(module, file_path)
                    
        return resource_classes


class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def format_response(data):
        """格式化响应数据"""
        if isinstance(data, dict):
            data = iter_camel(data)
        elif isinstance(data, list):
            data = [iter_camel(item) if isinstance(item, dict) else item 
                   for item in data]
        elif data is None or isinstance(data, str):
            pass
        else:
            return data
            
        return {'code': 200, 'msg': '操作成功', 'data': data}


class Router(Blueprint):
    """路由基类"""

    def __init__(self, module, url_prefix=None, **kwargs):
        if url_prefix is None:
            url_prefix = f'/{module}'
        name = str(random.randint(100000, 999999))
        super().__init__(module, name, url_prefix=url_prefix, **kwargs)
        router_frame = inspect.stack()[1]
        router_file = router_frame.filename
        self.param_handler = ParamHandler()
        self.resource_loader = ResourceLoader()
        self.response_formatter = ResponseFormatter()
        self.auto_add_resources(router_file)

    def verify_user(self):
        """用户验证，通过继承覆盖此方法实现具体逻辑"""
        return True

    def handle_error(self, e):
        """错误处理，通过继承覆盖此方法实现具体逻辑"""
        pass

    @staticmethod
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def wrap_view_func(self, func, public=False):
        """包装视图函数,处理参数验证、错误处理和响应格式化"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            params = self.param_handler.clean_params(
                self.param_handler.get_params()
            )
            
            if not self.verify_user() and not public:
                return {'code': 401, 'msg': '用户无权限'}
                
            try:
                data = self.decorator(func)(**params)
            except MessagePrompt as e:
                return {'code': 500, 'msg': str(e)}
            except ValidationError as e:
                return {'code': 400, 'msg': str(e)}
            except Exception as e:
                self.handle_error(e)
                raise e
                
            return self.response_formatter.format_response(data)
            
        return wrapper

    def add_resource(self, rule, resource_class):
        """添加资源类路由"""
        http_methods = ['get', 'post', 'put', 'delete']

        for method_name in http_methods:
            if method_name in dir(resource_class):
                method = getattr(resource_class, method_name)
                public = getattr(method, 'public', False)
                method = functools.partial(method)
                endpoint = str(random.randint(10000000, 99999999))
                self.add_url_rule(
                    rule,
                    endpoint,
                    self.wrap_view_func(method, public=public),
                    methods=[method_name.upper()]
                )

    def add_resources(self, resource_classes):
        """批量添加资源类路由"""
        for resource_class in resource_classes:
            self.add_resource(resource_class.path, resource_class)

    def auto_add_resources(self, resources_file):
        """自动添加资源文件中的路由"""
        resource_classes = self.resource_loader.get_resource_classes(resources_file)
        self.add_resources(resource_classes)

    def add(self, rule, public=False, **options):
        """添加单个路由装饰器"""
        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(
                rule,
                endpoint,
                self.wrap_view_func(f, public=public),
                **options
            )
        return decorator
