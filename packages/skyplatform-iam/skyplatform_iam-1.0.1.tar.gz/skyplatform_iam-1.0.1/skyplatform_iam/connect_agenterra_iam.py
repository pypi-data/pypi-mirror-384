import os
import requests
import logging
import traceback
import copy
from dotenv import load_dotenv
from enum import Enum

# 加载环境变量
load_dotenv()


class CredentialTypeEnum(str, Enum):
    """凭证类型枚举，与后端API保持一致"""
    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"
    WECHAT_OPENID = "wechat_openid"


class ConnectAgenterraIam(object):
    def __init__(self, logger_name="skyplatform_iam", log_level=logging.INFO):
        """
        初始化AgenterraIAM连接器
        
        参数:
        - logger_name: 日志记录器名称
        - log_level: 日志级别
        """
        # 配置日志记录器
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)
        
        # 从环境变量读取配置，提供默认值以确保向后兼容
        self.agenterra_iam_host = os.environ.get('AGENTERRA_IAM_HOST')
        self.server_name = os.environ.get('AGENTERRA_SERVER_NAME')
        self.access_key = os.environ.get('AGENTERRA_ACCESS_KEY')
        
        self.logger.info(f"初始化AgenterraIAM连接器 - Host: {self.agenterra_iam_host}, Server: {self._mask_sensitive(self.server_name)}")
        
        self.headers = {
            "Content-Type": "application/json",
            "SERVER-AK": self.server_name,
            "SERVER-SK": self.access_key
        }
        self.body = {
            "server_name": self.server_name,
            "access_key": self.access_key
        }

    def _mask_sensitive(self, value, mask_char="*", show_chars=4):
        """
        脱敏处理敏感信息
        
        参数:
        - value: 要脱敏的值
        - mask_char: 脱敏字符
        - show_chars: 显示的字符数量
        
        返回: 脱敏后的字符串
        """
        if not value or not isinstance(value, str):
            return str(value) if value else "None"
        
        if len(value) <= show_chars:
            return mask_char * len(value)
        
        return value[:show_chars] + mask_char * (len(value) - show_chars)

    def _sanitize_log_data(self, data):
        """
        清理日志数据，脱敏敏感信息
        
        参数:
        - data: 要清理的数据（字典或其他类型）
        
        返回: 清理后的数据
        """
        if not isinstance(data, dict):
            return data
        
        # 需要脱敏的字段列表
        sensitive_fields = [
            'password', 'access_key', 'token', 'refresh_token', 
            'SERVER-SK', 'new_password', 'server_sk'
        ]
        
        sanitized = copy.deepcopy(data)
        
        for key, value in sanitized.items():
            if key.lower() in [field.lower() for field in sensitive_fields]:
                sanitized[key] = self._mask_sensitive(str(value))
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_log_data(value)
        
        return sanitized

    def _log_request(self, method_name, url, headers, body):
        """记录请求信息"""
        sanitized_headers = self._sanitize_log_data(headers)
        sanitized_body = self._sanitize_log_data(body)
        
        self.logger.info(f"[{method_name}] 发送请求 - URL: {url}")
        self.logger.info(f"[{method_name}] 请求头: {sanitized_headers}")
        self.logger.info(f"[{method_name}] 请求体: {sanitized_body}")

    def _log_response(self, method_name, response):
        """记录响应信息"""
        try:
            response_data = response.json() if response.content else {}
            sanitized_response = self._sanitize_log_data(response_data)
            self.logger.info(f"[{method_name}] 响应状态码: {response.status_code}")
            self.logger.info(f"[{method_name}] 响应内容: {sanitized_response}")
        except Exception as e:
            self.logger.info(f"[{method_name}] 响应状态码: {response.status_code}")
            self.logger.info(f"[{method_name}] 响应内容解析失败: {str(e)}")

    def register(self, cred_type=None, cred_value=None, password=None, nickname=None, avatar_url=None, 
                 username=None, phone=None):
        """
        注册用户时，同步至iam

        新参数格式（推荐使用）:
        - cred_type: 凭证类型 (CredentialTypeEnum: username, email, phone, wechat_openid)
        - cred_value: 凭证值
        - password: 用户密码（可选）
        - nickname: 用户昵称（可选）
        - avatar_url: 头像URL（可选）

        旧参数格式（向后兼容）:
        - username: 要注册的用户名
        - phone: 手机号码（可选）
        - password: 用户密码
        - nickname: 用户昵称（可选）

        返回:
        - 成功: 返回包含用户信息的字典
        - 失败: 返回False
        """
        method_name = "register"
        self.logger.info(f"[{method_name}] 开始用户注册 - cred_type: {cred_type}, cred_value: {self._mask_sensitive(str(cred_value))}")
        
        try:
            # 参数映射：支持旧的调用方式
            if cred_type is None and cred_value is None:
                if username:
                    cred_type = CredentialTypeEnum.USERNAME
                    cred_value = username
                    self.logger.debug(f"[{method_name}] 使用旧参数格式 - username: {self._mask_sensitive(username)}")
                elif phone:
                    cred_type = CredentialTypeEnum.PHONE
                    cred_value = phone
                    self.logger.debug(f"[{method_name}] 使用旧参数格式 - phone: {self._mask_sensitive(phone)}")
                else:
                    raise ValueError("必须提供 cred_type+cred_value 或 username/phone")

            # 验证凭证类型
            if isinstance(cred_type, str):
                cred_type = CredentialTypeEnum(cred_type)

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "cred_type": cred_type.value,
                "cred_value": cred_value
            }

            # 添加可选参数
            if password:
                body["password"] = password
            if nickname:
                body["nickname"] = nickname
            if avatar_url:
                body["avatar_url"] = avatar_url

            uri = "/api/v2/service/register"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.logger.info(f"[{method_name}] 用户注册成功")
                    return result.get("data")
                else:
                    self.logger.warning(f"[{method_name}] 用户注册失败 - 响应: {result}")
            else:
                self.logger.warning(f"[{method_name}] 用户注册失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 注册请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def login_with_password(self, cred_type=None, cred_value=None, password=None, ip_address=None, user_agent=None,
                           username=None):
        """
        账号密码登陆时，同步至iam，由iam签发token

        新参数格式（推荐使用）:
        - cred_type: 凭证类型 (CredentialTypeEnum: username, email, phone, wechat_openid)
        - cred_value: 凭证值
        - password: 用户密码
        - ip_address: IP地址（可选）
        - user_agent: 用户代理（可选）

        旧参数格式（向后兼容）:
        - username: 用户名
        - password: 用户密码
        """
        method_name = "login_with_password"
        self.logger.info(f"[{method_name}] 开始密码登录 - cred_type: {cred_type}, cred_value: {self._mask_sensitive(str(cred_value))}")
        
        try:
            # 参数映射：支持旧的调用方式
            if cred_type is None and cred_value is None:
                if username:
                    cred_type = CredentialTypeEnum.USERNAME
                    cred_value = username
                    self.logger.debug(f"[{method_name}] 使用旧参数格式 - username: {self._mask_sensitive(username)}")
                else:
                    raise ValueError("必须提供 cred_type+cred_value 或 username")

            # 验证凭证类型
            if isinstance(cred_type, str):
                cred_type = CredentialTypeEnum(cred_type)

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "cred_type": cred_type.value,
                "cred_value": cred_value,
                "password": password
            }

            # 添加可选参数
            if ip_address:
                body["ip_address"] = ip_address
            if user_agent:
                body["user_agent"] = user_agent

            uri = "/api/v2/service/login"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 密码登录成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 密码登录失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 密码登录请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def login_without_password(self, cred_type=None, cred_value=None, ip_address=None, user_agent=None,
                              username=None):
        """
        短信验证码登陆时，机机接口请求token

        新参数格式（推荐使用）:
        - cred_type: 凭证类型 (CredentialTypeEnum: username, email, phone, wechat_openid)
        - cred_value: 凭证值
        - ip_address: IP地址（可选）
        - user_agent: 用户代理（可选）

        旧参数格式（向后兼容）:
        - username: 用户名

        返回: response对象或False
        """
        method_name = "login_without_password"
        self.logger.info(f"[{method_name}] 开始免密登录 - cred_type: {cred_type}, cred_value: {self._mask_sensitive(str(cred_value))}")
        
        try:
            # 参数映射：支持旧的调用方式
            if cred_type is None and cred_value is None:
                if username:
                    cred_type = CredentialTypeEnum.USERNAME
                    cred_value = username
                    self.logger.debug(f"[{method_name}] 使用旧参数格式 - username: {self._mask_sensitive(username)}")
                else:
                    raise ValueError("必须提供 cred_type+cred_value 或 username")

            # 验证凭证类型
            if isinstance(cred_type, str):
                cred_type = CredentialTypeEnum(cred_type)

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "cred_type": cred_type.value,
                "cred_value": cred_value
            }

            # 添加可选参数
            if ip_address:
                body["ip_address"] = ip_address
            if user_agent:
                body["user_agent"] = user_agent

            uri = "/api/v2/service/login_without_password"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 免密登录成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 免密登录失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 免密登录请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def logout(self, token):
        """
        用户登出
        server_name: 服务名称
        username: 用户名
        """
        method_name = "logout"
        self.logger.info(f"[{method_name}] 开始用户登出 - token: {self._mask_sensitive(token)}")
        
        try:
            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "token": token
            }
            uri = "/api/v2/service/logout"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)

            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 用户登出成功")
                return True
            else:
                self.logger.warning(f"[{method_name}] 用户登出失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 登出请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def verify_token(self, token, api, method, server_ak="", server_sk=""):
        """
        请求iam进行鉴权
        server_name: 服务名称
        token: 用户token
        api: 当前访问的API路径

        返回:
        - 成功且有权限: 返回用户信息字典
        - 成功但无权限: 抛出403异常
        - token无效或其他错误: 返回None
        """
        method_name = "verify_token"
        self.logger.info(f"[{method_name}] 开始token验证 - api: {api}, method: {method}, token: {self._mask_sensitive(token)}")
        
        try:
            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "token": token,
                "api": api,
                "method": method,
                "server_ak": server_ak,
                "server_sk": server_sk,
            }
            uri = "/api/v2/service/verify"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                result = response.json()
                # 检查响应格式
                if result.get("success") and result.get("valid"):
                    if result.get("has_permission"):
                        # 有权限时返回用户信息
                        user_info = {
                            "user_id": result.get("user_id"),
                            "username": result.get("username"),
                            "session_id": result.get("session_id"),
                            "microservice": result.get("microservice"),
                            "is_whitelist": result.get("is_whitelist", False)
                        }
                        self.logger.info(f"[{method_name}] token验证成功，用户有权限 - user_id: {user_info.get('user_id')}")
                        return user_info
                    else:
                        # token有效但无权限，抛出403异常
                        self.logger.warning(f"[{method_name}] token有效但用户无权限访问API: {api}")
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=result.get("message", "用户无权限访问此API")
                        )
                else:
                    self.logger.warning(f"[{method_name}] token验证失败 - success: {result.get('success')}, valid: {result.get('valid')}")

            elif response.status_code == 403:
                result = response.json()
                # 处理403响应
                self.logger.warning(f"[{method_name}] 收到403响应 - {result.get('message', '用户无权限访问此API')}")
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=result.get("message", "用户无权限访问此API")
                )
            else:
                self.logger.warning(f"[{method_name}] token验证失败 - 状态码: {response.status_code}")

            return None
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            self.logger.error(f"[{method_name}] Token验证异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return None

    def reset_password(self, user_id=None, new_password=None, username=None, password=None):
        """
        重置密码

        新参数格式（推荐使用）:
        - user_id: 用户ID
        - new_password: 新密码

        旧参数格式（向后兼容）:
        - username: 用户名
        - password: 新密码
        """
        method_name = "reset_password"
        self.logger.info(f"[{method_name}] 开始重置密码 - user_id: {user_id}")
        
        # 记录旧参数格式的使用
        if username or password:
            self.logger.debug(f"[{method_name}] 检测到旧参数格式 - username: {username}")
        
        try:
            # 参数映射：支持旧的调用方式
            if user_id is None and new_password is None:
                if username and password:
                    # 旧版本使用username，但后端需要user_id
                    # 这里需要先通过其他方式获取user_id，或者提示用户使用新格式
                    raise ValueError("旧版本参数已废弃，请使用 user_id 和 new_password 参数")
                else:
                    raise ValueError("必须提供 user_id 和 new_password")

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "user_id": user_id,
                "new_password": new_password
            }
            uri = "/api/v2/service/reset_password"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )
            
            # 记录响应信息
            self._log_response(method_name, response)
            
            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 密码重置成功")
                return True
            else:
                self.logger.warning(f"[{method_name}] 密码重置失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 重置密码请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def refresh_token(self, refresh_token):
        """
        机机接口：刷新用户令牌

        参数:
        - refresh_token: 刷新令牌

        返回: response对象或False
        """
        method_name = "refresh_token"
        self.logger.info(f"[{method_name}] 开始刷新令牌 - refresh_token: {self._mask_sensitive(refresh_token)}")
        
        try:
            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "refresh_token": refresh_token
            }
            uri = "/api/v2/service/refresh_token"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 令牌刷新成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 令牌刷新失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 刷新令牌请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def assign_role_to_user(self, user_id, role_id):
        """
        机机接口：给指定用户授予指定角色

        参数:
        - user_id: 用户ID
        - role_id: 角色ID

        返回: 成功返回True，失败返回False
        """
        method_name = "assign_role_to_user"
        self.logger.info(f"[{method_name}] 开始角色分配 - user_id: {user_id}, role_id: {role_id}")
        
        try:
            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "user_id": user_id,
                "role_id": role_id
            }
            uri = "/api/v2/service/assign_role"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 角色分配成功")
                return True
            else:
                self.logger.warning(f"[{method_name}] 角色分配失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 角色分配请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def get_userinfo_by_token(self, token):
        """
                账号密码登陆时，同步至iam，由iam签发token
                """
        method_name = "get_userinfo_by_token"
        self.logger.info(f"[{method_name}] 开始获取用户信息 - token: {self._mask_sensitive(token)}")
        
        try:
            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "token": token,
            }
            uri = "/api/v2/service/token"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 获取用户信息成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 获取用户信息失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 获取用户信息请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def merge_credential(self, target_user_id, cred_type, cred_value, merge_reason=None):
        """
        机机接口：凭证合并
        
        为第三方服务提供凭证合并功能，处理用户绑定新凭证时的账号合并场景。
        例如用户先用账号密码注册，后续又绑定手机号时的账号合并需求。

        参数:
        - target_user_id: 目标用户ID（保留的用户）
        - cred_type: 要绑定的凭证类型 (CredentialTypeEnum: username, email, phone, wechat_openid)
        - cred_value: 要绑定的凭证值
        - merge_reason: 合并原因（可选）

        返回: 
        - 成功: 返回响应对象
        - 失败: 返回False
        """
        method_name = "merge_credential"
        self.logger.info(f"[{method_name}] 开始凭证合并 - target_user_id: {target_user_id}, cred_type: {cred_type}, cred_value: {self._mask_sensitive(cred_value)}")
        
        try:
            # 验证凭证类型
            if isinstance(cred_type, str):
                cred_type = CredentialTypeEnum(cred_type)

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "target_user_id": target_user_id,
                "cred_type": cred_type.value,
                "cred_value": cred_value
            }

            # 添加可选参数
            if merge_reason:
                body["merge_reason"] = merge_reason
                self.logger.debug(f"[{method_name}] 合并原因: {merge_reason}")

            uri = "/api/v2/service/merge_credential"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 凭证合并成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 凭证合并失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 凭证合并请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False

    def get_user_by_credential(self, cred_type, cred_value):
        """
        机机接口：通过凭证获取用户信息
        
        为第三方服务提供通过用户名或手机号等认证凭据获取用户信息的功能。

        参数:
        - cred_type: 凭证类型 (CredentialTypeEnum: username, email, phone, wechat_openid)
        - cred_value: 凭证值

        返回: 
        - 成功: 返回响应对象
        - 失败: 返回False
        """
        method_name = "get_user_by_credential"
        self.logger.info(f"[{method_name}] 开始获取用户信息 - cred_type: {cred_type}, cred_value: {self._mask_sensitive(cred_value)}")
        
        try:
            # 验证凭证类型
            if isinstance(cred_type, str):
                cred_type = CredentialTypeEnum(cred_type)

            body = {
                "server_name": self.server_name,
                "access_key": self.access_key,
                "cred_type": cred_type.value,
                "cred_value": cred_value
            }

            uri = "/api/v2/service/get_user_by_credential"
            url = self.agenterra_iam_host + uri
            
            # 记录请求信息
            self._log_request(method_name, url, self.headers, body)
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=body,
                verify=False
            )

            # 记录响应信息
            self._log_response(method_name, response)

            if response.status_code == 200:
                self.logger.info(f"[{method_name}] 获取用户信息成功")
                return response
            else:
                self.logger.warning(f"[{method_name}] 获取用户信息失败 - 状态码: {response.status_code}")
            
            return False
        except Exception as e:
            self.logger.error(f"[{method_name}] 获取用户信息请求异常: {str(e)}")
            self.logger.error(f"[{method_name}] 异常堆栈: {traceback.format_exc()}")
            return False