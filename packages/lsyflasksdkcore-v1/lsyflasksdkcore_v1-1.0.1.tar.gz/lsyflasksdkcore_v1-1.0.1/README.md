# lsyflasksdkcore_v1

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

领数云 Flask SDK 核心库，为 Flask 应用提供常用的功能模块和工具。

## 功能特性

- 🔐 **身份认证与授权** - JWT Token 管理和权限控制
- 📊 **数据处理** - 数据模型、序列化和 LINQ 查询
- 📈 **数据导出** - Excel/CSV 文件导出功能
- 📝 **API 文档** - Swagger 文档自动生成
- 🔒 **加密工具** - SM2 国密算法支持
- 📋 **日志管理** - 文件和 Logstash 日志记录
- 🛠 **实用工具** - 延迟加载、单例模式、树结构等

## 安装

```bash
pip install lsyflasksdkcore_v1
```

或者从源码安装：

```bash
git clone https://github.com/9kl/lsyflasksdkcore_v1.git
cd lsyflasksdkcore_v1
pip install -e .
```

## 快速开始

### 基本使用

```python
from flask import Flask
from lsyflasksdkcore_v1 import BaseModel, sresponse, eresponse

app = Flask(__name__)

# 初始化模型
model = BaseModel(app)

@app.route('/api/success')
def success():
    return sresponse(data={"message": "操作成功"})

@app.route('/api/error')
def error():
    return eresponse(message="操作失败", code=400)
```

### 权限控制

```python
from lsyflasksdkcore_v1.blueprints import AuthGrant

# 创建权限控制实例
auth = AuthGrant("user_management", __name__)

@app.route('/admin/users')
@auth.grant("view")  # 需要查看权限
def list_users():
    return sresponse(data=[])
```

### 数据导出

```python
from lsyflasksdkcore_v1.excel import export_xls

@app.route('/export/users')
def export_users():
    headers = ["ID", "用户名", "邮箱"]
    data = [
        [1, "张三", "zhangsan@example.com"],
        [2, "李四", "lisi@example.com"]
    ]
    return export_xls("用户列表", headers, data)
```

### JWT Token 管理

```python
from lsyflasksdkcore_v1.utils.token_utils import encode_auth_token, decode_auth_token

# 生成 Token
token = encode_auth_token(user_id=123, login_time=1640995200)

# 验证 Token
payload = decode_auth_token(token)
user_id = payload['data']['id']
```

## 模块说明

### 核心模块

- **context** - 请求上下文和响应处理
- **model** - 数据模型和查询结果封装
- **schema** - 数据验证和序列化模式
- **serialization** - 对象序列化工具

### 功能模块

- **blueprints** - Flask 蓝图和权限控制
- **excel** - Excel/CSV 导出功能
- **swagger** - API 文档生成
- **linq** - LINQ 风格的数据查询
- **logging** - 日志记录工具
- **export** - 数据导出处理

### 工具模块

- **utils/token_utils** - JWT Token 工具
- **utils/sm2encry** - SM2 加密工具
- **utils/lazy** - 延迟加载装饰器
- **utils/singleton_meta** - 单例模式元类
- **utils/tree** - 树形数据结构
- **utils/unique** - 唯一性工具

## 依赖要求

- Python >= 3.8
- Flask >= 3.0.3
- marshmallow >= 3.11.1
- SQLAlchemy >= 2.0.43
- PyJWT >= 2.1.0
- gmssl >= 3.2.1

详细依赖列表请查看 [requirements.txt](requirements.txt)

## 许可证

本项目采用 Apache License 2.0 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 联系方式

- 作者：fhp
- 邮箱：chinafengheping@outlook.com
- 项目地址：https://github.com/9kl/lsyflasksdkcore_v1