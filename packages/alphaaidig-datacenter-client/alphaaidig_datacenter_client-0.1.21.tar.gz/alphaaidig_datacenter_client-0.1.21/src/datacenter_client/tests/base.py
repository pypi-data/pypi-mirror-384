import unittest
from typing import Dict, Any, List

from datacenter_client.client import DatacenterClient


class BaseClientTest(unittest.TestCase):
    """基础测试类，提供通用的测试设置和方法"""
    
    BASE_URL = "http://127.0.0.1:10000"
    TOKEN = "4e2e929a1ba14b06b8e8ca7e7e560efe"
    
    def setUp(self):
        """设置测试环境"""
        self.client = DatacenterClient(base_url=self.BASE_URL, token=self.TOKEN)
    
    def check_success_response(self, result: Dict[str, Any]) -> bool:
        """检查响应是否成功"""
        # 检查result是否为字典且包含status和data字段
        return isinstance(result, dict) and result.get('status') == 'success' and 'data' in result
    
    def check_pagination_response(self, result: Any) -> bool:
        """检查分页响应格式"""
        # 检查是否有status和data字段，且data中有items和pagination
        if isinstance(result, dict) and result.get('status') == 'success' and 'data' in result:
            data = result['data']
            return isinstance(data, dict) and 'items' in data and 'pagination' in data
        # 兼容旧格式
        return isinstance(result, dict) and 'items' in result and 'pagination' in result
    
    def print_pagination_info(self, result: Any):
        """打印分页信息"""
        # 检查是否是DTO对象
        if hasattr(result, 'status') and hasattr(result, 'data'):
            # DTO对象
            print(f"返回记录数: {len(result.items)}")
            if hasattr(result, 'pagination') and result.pagination:
                print(f"分页信息: {result.pagination}")
            if result.items:
                print(f"第一条记录: {result.items[0]}")
        elif isinstance(result, dict) and result.get('status') == 'success' and 'data' in result:
            # 新的响应格式
            data = result['data']
            if isinstance(data, dict) and 'items' in data:
                print(f"返回记录数: {len(data['items'])}")
                if 'pagination' in data:
                    print(f"分页信息: {data['pagination']}")
                if data['items']:
                    print(f"第一条记录: {data['items'][0]}")
            else:
                print("返回数据格式不符合预期")
        elif isinstance(result, dict) and 'items' in result and 'pagination' in result:
            # 旧格式
            print(f"返回记录数: {len(result['items'])}")
            print(f"分页信息: {result['pagination']}")
            if result['items']:
                print(f"第一条记录: {result['items'][0]}")
        else:
            print("返回数据格式不符合预期")
    
    def print_list_info(self, result: Any):
        """打印列表信息"""
        # 检查是否是DTO对象
        if hasattr(result, 'status') and hasattr(result, 'data'):
            # DTO对象
            print(f"返回记录数: {len(result.items)}")
            if hasattr(result, 'total'):
                print(f"总记录数: {result.total}")
            if result.items:
                print(f"第一条记录: {result.items[0]}")
        elif isinstance(result, dict) and result.get('status') == 'success' and 'data' in result:
            # 新的响应格式
            data = result['data']
            if isinstance(data, dict) and 'items' in data:
                print(f"返回记录数: {len(data['items'])}")
                if 'total' in data:
                    print(f"总记录数: {data['total']}")
                if data['items']:
                    print(f"第一条记录: {data['items'][0]}")
            elif isinstance(data, list):
                print(f"返回记录数: {len(data)}")
                if data:
                    print(f"第一条记录: {data[0]}")
            else:
                print("返回数据格式不符合预期")
        elif isinstance(result, list):
            # 纯列表格式
            print(f"返回记录数: {len(result)}")
            if result:
                print(f"第一条记录: {result[0]}")
        elif isinstance(result, dict):
            # 如果是字典，可能是分页数据
            if 'items' in result:
                print(f"返回记录数: {len(result['items'])}")
                if result['items']:
                    print(f"第一条记录: {result['items'][0]}")
            else:
                print("返回数据格式不符合预期")
        else:
            print("返回数据格式不符合预期")
    
    def print_item_info(self, result: Any):
        """打印单项信息"""
        # 检查是否是DTO对象
        if hasattr(result, 'status') and hasattr(result, 'data'):
            # DTO对象
            # 根据不同的DTO类型，访问不同的属性
            if hasattr(result, 'industries'):
                print(f"返回数据: {result.industries}")
            elif hasattr(result, 'industry'):
                print(f"返回数据: {result.industry}")
            elif hasattr(result, 'summary'):
                print(f"返回数据: {result.summary}")
            else:
                print(f"返回数据: {result.data}")
        elif isinstance(result, dict) and result.get('status') == 'success' and 'data' in result:
            # 新的响应格式
            print(f"返回数据: {result['data']}")
        elif isinstance(result, dict):
            # 旧格式或其他格式
            print(f"返回数据: {result}")
        else:
            print("请求失败")