# SkyPlatform IAM SDK

SkyPlatform IAM认证SDK，提供FastAPI中间件和认证路由，简化第三方服务的认证集成。

## 功能特性

- 🔐 **FastAPI中间件**: 自动拦截请求进行Token验证和权限检查
- 🚀 **认证路由**: 封装用户注册、登录、登出等认证接口
- ⚙️ **灵活配置**: 支持环境变量和代码配置
- 🛡️ **白名单机制**: 支持配置无需认证的路径
- 🔧 **完整兼容**: 基于现有ConnectAgenterraIam类，保持完全兼容
- 📝 **类型提示**: 完整的TypeScript风格类型提示
- 🚨 **异常处理**: 完善的错误处理和自定义异常

## 快速开始

### 安装

```bash
pip install skyplatform-iam
```

### 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
AGENTERRA_IAM_HOST=https://your-iam-host.com
AGENTERRA_SERVER_NAME=your-server-name
AGENTERRA_ACCESS_KEY=your-access-key
```

### 基本使用

#### 方式1：一键设置（推荐）

```python
from fastapi import FastAPI
from skyplatform_iam import setup_auth

app = FastAPI()

# 一键设置认证中间件和路由
setup_auth(app)

@app.get("/protected")
async def protected_endpoint(request):
    # 获取用户信息（由中间件自动设置）
    user = request.state.user
    return {"message": "访问成功", "user": user}
```

#### 方式2：手动设置

```python
from fastapi import FastAPI
from skyplatform_iam import AuthConfig, AuthMiddleware, create_auth_router

app = FastAPI()

# 创建配置
config = AuthConfig.from_env()

# 添加认证中间件
app.add_middleware(AuthMiddleware, config=config)

# 添加认证路由
auth_router = create_auth_router(config=config, prefix="/auth")
app.include_router(auth_router)
```

#### 方式3：自定义配置

```python
from skyplatform_iam import AuthConfig, setup_auth

# 自定义配置
config = AuthConfig(
    agenterra_iam_host="https://your-iam-host.com",
    server_name="your-server-name",
    access_key="your-access-key",
    whitelist_paths=[
        "/docs", "/redoc", "/openapi.json",
        "/health", "/public",
        "/auth/register", "/auth/login"
    ],
    enable_debug=True
)

setup_auth(app, config=config)
```

## API接口

SDK自动提供以下认证接口：

- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/login_without_password` - 免密登录
- `POST /auth/logout` - 用户登出
- `POST /auth/reset_password` - 重置密码
- `POST /auth/refresh_token` - 刷新Token
- `POST /auth/assign_role` - 分配角色
- `POST /auth/user_info` - 获取用户信息

## 中间件功能

### 自动Token验证

中间件会自动：
1. 检查请求路径是否在白名单中
2. 从请求头提取Authorization Token
3. 调用IAM服务验证Token和权限
4. 将用户信息设置到 `request.state.user`

### 白名单配置

默认白名单路径：
- `/docs`, `/redoc`, `/openapi.json` - API文档
- `/health` - 健康检查
- `/auth/*` - 认证相关接口

添加自定义白名单：

```python
config = AuthConfig.from_env()
config.add_whitelist_path("/public")
config.add_whitelist_path("/status")
```

### 获取用户信息

在受保护的路由中获取用户信息：

```python
@app.get("/user-profile")
async def get_user_profile(request):
    if hasattr(request.state, 'user'):
        user = request.state.user
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "session_id": user["session_id"]
        }
    else:
        raise HTTPException(status_code=401, detail="未认证")
```

## 异常处理

SDK提供完整的异常处理：

```python
from skyplatform_iam.exceptions import (
    AuthenticationError,    # 认证失败
    AuthorizationError,     # 权限不足
    TokenExpiredError,      # Token过期
    TokenInvalidError,      # Token无效
    ConfigurationError,     # 配置错误
    IAMServiceError,        # IAM服务错误
    NetworkError           # 网络错误
)
```

## 配置选项

### AuthConfig参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agenterra_iam_host` | str | ✓ | IAM服务地址 |
| `server_name` | str | ✓ | 服务名称 |
| `access_key` | str | ✓ | 访问密钥 |
| `whitelist_paths` | List[str] | ✗ | 白名单路径 |
| `token_header` | str | ✗ | Token请求头名称（默认：Authorization） |
| `token_prefix` | str | ✗ | Token前缀（默认：Bearer ） |
| `enable_debug` | bool | ✗ | 启用调试模式 |

## 开发和测试

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python examples/test_sdk.py
```

### 运行示例

```bash
# 启动示例应用
python examples/basic_usage.py

# 访问 http://localhost:8000/docs 查看API文档
```

## 兼容性

- Python 3.8+
- FastAPI 0.68.0+
- 完全兼容现有的 `ConnectAgenterraIam` 类

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 提供FastAPI中间件和认证路由
- 支持完整的认证功能
- 兼容现有ConnectAgenterraIam类