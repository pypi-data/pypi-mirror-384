"""
通用客户端
提供简洁的数据查询接口
"""
import pandas as pd
import json
import requests
from functools import partial
from datacenter_common.schemas import ResultType


class PageDataFrame(pd.DataFrame):
    """
    带分页信息的DataFrame

    继承自pandas.DataFrame，添加分页相关的属性和方法
    """

    _metadata = ['_pagination']

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False, pagination=None):
        super().__init__(data=data, index=index, columns=columns, dtype=dtype, copy=copy)
        self._pagination = pagination or {}

    @property
    def pagination(self):
        """获取分页信息"""
        return self._pagination

    @property
    def has_pagination(self):
        """是否有分页信息"""
        return bool(self._pagination)

    @property
    def current_page(self):
        """当前页码"""
        return self._pagination.get('page', 1)

    @property
    def page_size(self):
        """每页大小"""
        return self._pagination.get('page_size', len(self))

    @property
    def total_count(self):
        """总记录数"""
        return self._pagination.get('total', len(self))

    @property
    def total_pages(self):
        """总页数"""
        total = self.total_count
        size = self.page_size
        return (total + size - 1) // size if size > 0 else 1

    def __repr__(self):
        base_repr = super().__repr__()
        if self.has_pagination:
            pagination_info = f"Page {self.current_page}/{self.total_pages} (Total: {self.total_count})"
            return f"{base_repr}\n[Pagination: {pagination_info}]"
        return base_repr


class DatacenterAPIError(Exception):
    """数据中心API异常类"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API错误 (code: {code}): {message}")


class DataApi:
    """
    简洁通用数据API客户端

    使用方式：
    ```python
    import datacenter_client as dc

    # 初始化客户端
    client = dc.api(token='your_token', base_url='http://localhost:10000')

    # 查询HSGT分页数据
    df = client.hsgt_page_list(page=1, page_size=20)

    # 查询指定字段的HSGT分页数据
    df = client.hsgt_page_list(page=1, page_size=10, fields='trade_date,stock_code,stock_name,hold_market_cap')

    # 按股票代码查询HSGT数据
    df = client.hsgt_by_stock(stock_code='00700.HK', limit=50)

    # 按股票代码查询并指定字段
    df = client.hsgt_by_stock(stock_code='00700.HK', limit=10, fields='trade_date,stock_code,stock_name,hold_market_cap')
    ```
    """

    def __init__(self, token: str, base_url: str = 'http://localhost:10000', timeout: int = 30):
        """
        初始化客户端

        Args:
            token: API认证token
            base_url: API服务基础URL
            timeout: 请求超时时间
        """
        self.__token = token
        self.__base_url = base_url.rstrip('/')
        self.__timeout = timeout
        self.__dataapi_url = f"{self.__base_url}/api/v1/dataapi"

    def query(self, api_name: str, fields: str = '', **kwargs) -> pd.DataFrame:
        """
        通用查询方法，与tushare的query方法完全一致

        Args:
            api_name: API名称，如'hsgt_south_fund'
            fields: 需要返回的字段，逗号分隔，如'trade_date,stock_code,stock_name'
            **kwargs: 查询参数

        Returns:
            pd.DataFrame: 查询结果
        """
        # 扁平化参数格式，与API期望格式一致
        req_params = kwargs.copy()
        req_params['fields'] = fields

        try:
            # 发送HTTP请求
            url = f"{self.__dataapi_url}/{api_name}"
            headers = {
                'X-API-Key': self.__token,
                'Content-Type': 'application/json'
            }
            res = requests.post(url, json=req_params, headers=headers, timeout=self.__timeout)

            if res.status_code != 200:
                raise Exception(f"HTTP请求失败，状态码: {res.status_code}")

            result = res.json()

            # 检查响应状态
            if result.get('code') != 0:
                raise DatacenterAPIError(
                    code=result.get('code', -1),
                    message=result.get('msg', '未知错误')
                )

            # 解析数据
            data = result.get('data', {})
            if not data:
                return pd.DataFrame()

            items = data.get('items', [])
            if not items:
                return pd.DataFrame()

            # 根据结果类型转换为DataFrame
            result_type = ResultType(result.get('result_type', 'table'))

            if result_type == ResultType.DICT:
                # 字典结果，转换为单行DataFrame
                return pd.DataFrame([data])
            elif result_type == ResultType.SINGLE:
                # 单条记录，转换为单行DataFrame
                return pd.DataFrame([data])
            elif result_type == ResultType.PAGE:
                # 分页结果，转换为PageDataFrame并保留分页信息
                pagination_info = result.get('pagination', {})
                return PageDataFrame(items, pagination=pagination_info)
            else:
                # 默认表格结果
                return pd.DataFrame(items)

        except requests.exceptions.Timeout:
            raise Exception(f"请求超时: {self.__timeout}秒")
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到服务器: {self.__base_url}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
        except Exception as e:
            raise Exception(f"查询失败: {str(e)}")

    def __getattr__(self, name: str):
        """
        魔术方法，动态创建API方法
        例如：pro.hsgt_south_fund() 等价于 pro.query('hsgt_south_fund')
        """
        return partial(self.query, name)


def api(token: str = '', base_url: str = 'http://localhost:10000', timeout: int = 30) -> DataApi:
    """
    初始化API客户端

    Args:
        token: API认证token
        base_url: API服务基础URL
        timeout: 请求超时时间

    Returns:
        DataApi: API客户端实例
    """
    if not token:
        raise ValueError('token不能为空')

    return DataApi(token=token, base_url=base_url, timeout=timeout)