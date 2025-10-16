from functools import reduce
from importlib import import_module
import json
from urllib.parse import unquote

from lesscode_flask.utils.helpers import app_config
from lesscode_flask.utils.redis.redis_helper import RedisHelper

try:
    flask_login = import_module("flask_login")
except ImportError as e:
    raise Exception(f"flask_login is not exist,run:pip install Flask-Login==0.6.3")


class PermissionsCheckMixin:

    def has_permission(self, permission):
        return self.has_permissions((permission,))

    def has_permissions(self, permissions):
        has_permissions = reduce(
            lambda a, b: a and b,
            [permission in self.permissions_url for permission in permissions],
            True,
        )

        return has_permissions

    # 权限集合(symbol)
    permissions = []
    # 权限集合(url)
    permissions_url = []


class User(flask_login.UserMixin, PermissionsCheckMixin):
    """
    在线用户对象类
    """

    def __init__(self, id="AnonymousUserId", username="AnonymousUser", display_name="匿名用户", phone_no: str = None,
                 email: str = None,
                 type: int = 0, account_status: str = None, permissions=[], permissions_url=[], roleIds=[],
                 client_id: str = None,
                 sub: str = None,limit_policy: str =None):
        # '账号id',
        self.id = id
        # 用户名
        self.username = username
        # '显示名',
        self.display_name = display_name
        # 手机号,
        self.phone_no = phone_no
        #  邮箱
        self.email = email
        # 用户类型 0：匿名用户，1：普通用户，2：API用户，3:客户端用户
        self.type = type
        self.sub = sub
        # # 组织机构id',
        # self.org_id = org_id
        # '1正常（激活）；2未激活（管理员新增，首次登录需要改密码）； 3锁定（登录错误次数超限，锁定时长可配置）； 4休眠（长期未登录（字段，时长可配置），定时） 5禁用-账号失效；
        self.account_status = account_status
        # 当前用户登录成功的客户端id'
        self.client_id = client_id
        # 权限集合(symbol)
        self.permissions = permissions
        # 权限集合(url)
        self.permissions_url = permissions_url
        # # 角色集合
        self.roleIds = roleIds
        # 限速策略
        self.limit_policy = limit_policy

    #
    @property
    def is_anonymous_user(self):
        """
        判断是否是匿名用户
        :return:
        """
        return self.type == 0

    @property
    def is_user(self):
        """
        判断是否是普通用户
        :return:
        """
        return self.type == 1

    @property
    def is_api_user(self):
        """
        判断是否是API用户
        :return:
        """
        return self.type == 2

    @property
    def is_client_user(self):
        """
        判断是否是客户端用户
        :return:
        """
        return self.type == 3

    # def __str__(self):
    #     return (f"User(id={self.id},username={self.username},phone_no={self.phone_no},"
    #             f"display_name={self.display_name},email={self.email},type={self.type},"
    #             f"account_status={self.account_status},permissions={self.permissions},client_id={self.client_id})")
    #
    # def __repr__(self):
    #     return (f"User(id={self.id},username={self.username},phone_no={self.phone_no},"
    #             f"display_name={self.display_name},email={self.email},type={self.type},"
    #             f"account_status={self.account_status},permissions={self.permissions},client_id={self.client_id})")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "phone_no": self.phone_no,
            "email": self.email if self.email else "",
            "type": self.type if self.type else "",
            "account_status": self.account_status,
            "client_id": self.client_id,
            "sub": self.sub if self.sub else "",
            "permissions": json.dumps(self.permissions),
            "permissions_url": json.dumps(self.permissions_url),
            "roleIds": json.dumps(self.roleIds),
            "limit_policy": self.limit_policy if self.limit_policy else ""

        }

    @staticmethod
    def to_user(user_data):
        if not isinstance(user_data, dict):
            user_data = user_data.__dict__
        user = User(id=user_data.get("id"), username=user_data.get("username", ""),
                    display_name=user_data.get("display_name", ""), phone_no=user_data.get("phone_no", ""),
                    email=user_data.get("email", ""), type=user_data.get("type", 0),
                    account_status=user_data.get("account_status", 1),
                    client_id=user_data.get("client_id", ""), sub=user_data.get("sub", ""),limit_policy =user_data.get("limit_policy", ""))
        permissions = user_data.get("permissions", [])
        if isinstance(permissions, str):
            user.permissions = json.loads(permissions)
        else:
            user.permissions = permissions
        permissions_url = user_data.get("permissions_url", [])
        if isinstance(permissions_url, str):
            user.permissions_url = json.loads(permissions_url)
        else:
            user.permissions_url = permissions_url
        roleIds = user_data.get("roleIds", [])
        if isinstance(roleIds, str):
            user.roleIds = json.loads(roleIds)
        else:
            user.roleIds = roleIds
        return user

    @staticmethod
    def get_user(request):
        # 使用token访问的用户
        if app_config.get("GATEWAY_USER_ENABLE"):
            user_json = request.headers.get("User", "")
            if user_json:
                return User.get_gateway_user(user_json)
        # 使用token访问的用户
        authorization = request.headers.get("Authorization", "")
        if "Bearer " in authorization:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if token:
                return User.get_token_user(token)
        apikey = request.headers.get("app_key")
        if apikey:
            # 使用AK访问的接口用户
            return User.get_api_user(apikey)
        # 无任何用户信息返回 匿名用户
        return User()

    @staticmethod
    def get_gateway_user(user_json):
        """
        网关传输信息中获取用户信息
        :param user_json:
        :return:
        """
        if user_json:
            user_dict = json.loads(user_json)
            if user_dict and isinstance(user_dict, dict):
                if type(user_dict["roleIds"]) == str:
                    user_dict["roleIds"] = json.loads(user_dict["roleIds"])
                user = User(
                    id=user_dict["id"],
                    username=user_dict["username"],
                    display_name=unquote(user_dict["display_name"]),
                    phone_no=user_dict["phone_no"],
                    permissions=user_dict.get("permissions", []),
                    roleIds=user_dict["roleIds"],
                    client_id=user_dict["client_id"],
                    limit_policy = user_dict.get("limit_policy", ""),
                )
                return user
        return User()

    @staticmethod
    def get_token_user(token):
        """
        根据token获取用户信息。
        该函数通过Redis缓存来获取用户信息。如果在缓存中找到了对应的用户数据，
        则会创建一个User对象并返回；如果没有找到，则返回一个AnonymousUser对象。
        参数:
        - token (str): 用户的令牌。
        返回:
        - User: 如果找到了用户信息，则返回一个User对象。
        - AnonymousUser: 如果没有找到用户信息，则返回一个AnonymousUser对象。
        """
        # 生成用户缓存键
        user_cache_key = f"oauth2:user:{token}"
        # 从Redis中获取用户数据
        user_dict = RedisHelper(app_config.get("REDIS_OAUTH_KEY", "redis")).sync_hgetall(user_cache_key)
        # 检查是否获取到了用户数据
        if user_dict:
            # 创建并返回User对象
            user = User.to_user(user_dict)
            return user
        return User()

    @staticmethod
    def get_api_user(apikey):
        """
        使用API key 获取用户信息
        :param apikey:
        :return:
        """
        user_cache_key = f"oauth2:user:{apikey}"
        app_cache_key = f"oauth2:app:{apikey}"
        # 优先从缓存中获取
        user_dict = RedisHelper(app_config.get("REDIS_OAUTH_KEY", "redis")).sync_hgetall(user_cache_key)
        if user_dict:
            user = User.to_user(user_dict)
            # apikey 的用户每次从缓存中获取权限信息
            app_dict = RedisHelper(app_config.get("REDIS_OAUTH_KEY", "redis")).sync_hgetall(app_cache_key)
            permissions = []
            permissions_url = []
            for key, value in app_dict.items():
                permissions_url.append(key)
                # 3.15 添加，如果value是字符串就转成dict
                if isinstance(value, str):
                    value = json.loads(value)
                permissions.append(value.get("symbol", ""))
            user.permissions_url = permissions_url
            user.permissions = permissions
            return user
        return User()
