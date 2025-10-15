# Datacenter API 客户端

这是 Datacenter API 的官方 Python 客户端。它提供了一种便捷且符合 Python 风格的方式来与所有 API 资源进行交互。

## 安装

如果您在 `datacenter` monorepo 项目中工作，该包是 `uv` 工作区的一部分。您可以与其他包一起以可编辑模式安装它：

```bash
# 在 monorepo 的根目录执行
uv pip install -e .
```

如果该包未来发布到像 PyPI 这样的包注册中心，可以通过以下方式安装：

```bash
pip install datacenter-client
```

## 使用方法

### 初始化

首先，导入并初始化主客户端。您需要提供 API 服务的基础 URL。您也可以选择性地提供一个认证令牌。

```python
from datacenter_client import DatacenterClient

client = DatacenterClient(
    base_url="http://localhost:10000",  # 替换为您的实际 API 服务器地址
    token="your-secret-token"          # 可选：如果您的 API 需要认证
)
```

### 访问 API 资源

客户端根据 API 资源被组织成不同的子客户端。例如，所有与 A 股相关的端点都在 `a_stock` 属性下可用。

#### 示例：A 股 API

```python
# 获取 A 股的分页列表
stocks_page = client.a_stock.list(page=1, limit=10, search="平安")
print("A 股列表:", stocks_page['items'])

# 获取特定股票的详细信息
stock_details = client.a_stock.get(stock_code="000001")
print("股票详情:", stock_details)

# 获取统计摘要信息
summary = client.a_stock.summary()
print("A 股统计摘要:", summary)
```

### 错误处理

客户端会针对不同类型的 API 错误抛出特定的异常，它们都继承自 `APIError`。这使得错误处理更加健壮。

- `NotFoundError`: 对应 `404 Not Found` 错误。
- `AuthenticationError`: 对应 `401 Unauthorized` 或 `403 Forbidden` 错误。
- `InvalidRequestError`: 对应 `400 Bad Request` 错误。
- `APIError`: 对应所有其他的服务器端或网络错误。

```python
from datacenter_client import APIError, NotFoundError

try:
    # 尝试获取一个不存在的股票
    client.a_stock.get(stock_code="999999")
except NotFoundError as e:
    print(f"捕获到预期的错误: {e}")
except APIError as e:
    print(f"发生意外的 API 错误: {e.status_code} - {e}")
```

### 使用上下文管理器

客户端可以作为上下文管理器使用，它会自动处理底层 HTTP 连接的关闭。这是推荐的使用方式。

```python
from datacenter_client import DatacenterClient

with DatacenterClient(base_url="http://localhost:10000") as client:
    # 获取第一页的 A 股数据
    stocks_page = client.a_stock.list(page=1, limit=5)
    for stock in stocks_page['items']:
        print(f"- {stock['stock_code']}: {stock['stock_name']}")

# 在这里，客户端连接会被自动关闭