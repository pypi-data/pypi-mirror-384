"""
通用客户端的测试用例
测试基于handler架构的tushare风格客户端
"""
import unittest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datacenter_client.universal_client import DataApi, api


class TestDataApi(unittest.TestCase):
    """测试DataApi类（通用客户端）"""

    def setUp(self):
        """每个测试方法执行前的设置"""
        self.token = "29a5378adfe44dadbf617efe1525766a"
        self.base_url = "http://localhost:10000"
        self.api = DataApi(token=self.token, base_url=self.base_url)

    @patch('datacenter_client.universal_client.requests.post')
    def test_query_success(self, mock_post):
        """测试成功的查询"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'msg': 'success',
            'data': {
                'items': [
                    {'trade_date': '2022-10-12', 'stock_code': '00700.HK', 'stock_name': '腾讯控股', 'hold_market_cap': 1000000},
                    {'trade_date': '2022-10-12', 'stock_code': '09988.HK', 'stock_name': '阿里巴巴', 'hold_market_cap': 800000}
                ]
            }
        }
        mock_post.return_value = mock_response

        # 执行查询
        result = self.api.query('hsgt_fund_page_list', trade_date='2022-10-12')

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(list(result.columns), ['trade_date', 'stock_code', 'stock_name', 'hold_market_cap'])
        self.assertEqual(result.iloc[0]['stock_code'], '700.HK')

        # 验证请求参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('hsgt_fund_page_list', call_args[0][0])
        self.assertEqual(call_args[1]['headers']['X-API-Key'], self.token)
        self.assertIn('trade_date', call_args[1]['json'])
        self.assertEqual(call_args[1]['json']['trade_date'], '2022-10-12')

    @patch('datacenter_client.universal_client.requests.post')
    def test_query_with_fields(self, mock_post):
        """测试指定字段的查询"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'items': [{'trade_date': '2022-10-12', 'stock_code': '700.HK'}]
            }
        }
        mock_post.return_value = mock_response

        result = self.api.query('hsgt_fund_by_stock', fields='trade_date,stock_code', stock_code='700.HK')

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ['trade_date', 'stock_code'])

        # 验证fields参数
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['fields'], 'trade_date,stock_code')

    @patch('datacenter_client.universal_client.requests.post')
    def test_query_api_error(self, mock_post):
        """测试API返回错误的情况"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 1,
            'msg': '参数错误'
        }
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.api.query('hsgt_fund_page_list', trade_date='invalid-date')

        self.assertIn('参数错误', str(context.exception))

    @patch('datacenter_client.universal_client.requests.post')
    def test_query_http_error(self, mock_post):
        """测试HTTP请求错误"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.api.query('hsgt_fund_page_list')

        self.assertIn('HTTP请求失败', str(context.exception))
        self.assertIn('500', str(context.exception))

    @patch('datacenter_client.universal_client.requests.post')
    def test_query_empty_data(self, mock_post):
        """测试返回空数据的情况"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'fields': ['trade_date', 'stock_code'],
                'items': []
            }
        }
        mock_post.return_value = mock_response

        result = self.api.query('hsgt_fund_page_list', trade_date='2022-01-01')

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    def test_getattr_dynamic_method(self):
        """测试通过__getattr__动态创建方法"""
        with patch.object(self.api, 'query') as mock_query:
            mock_query.return_value = pd.DataFrame()

            # 调用动态方法
            self.api.hsgt_fund_page_list(trade_date='2022-10-12')

            # 验证query方法被正确调用
            mock_query.assert_called_once_with('hsgt_fund_page_list', trade_date='2022-10-12')

    @patch('datacenter_client.universal_client.requests.post')
    def test_timeout_error(self, mock_post):
        """测试超时错误"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(Exception) as context:
            self.api.query('hsgt_fund_page_list')

        self.assertIn('请求超时', str(context.exception))

    @patch('datacenter_client.universal_client.requests.post')
    def test_connection_error(self, mock_post):
        """测试连接错误"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(Exception) as context:
            self.api.query('hsgt_fund_page_list')

        self.assertIn('无法连接到服务器', str(context.exception))

    @patch('datacenter_client.universal_client.requests.post')
    def test_pagination_response(self, mock_post):
        """测试分页响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'msg': 'success',
            'data': {
                'items': [{'trade_date': '2022-10-12', 'stock_code': '700.HK'}]
            },
            'result_type': 'page',
            'pagination': {
                'current_page': 1,
                'page_size': 20,
                'total_count': 100,
                'total_pages': 5
            }
        }
        mock_post.return_value = mock_response

        result = self.api.query('hsgt_fund_page_list', page=1, page_size=20)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        # 验证分页信息被保存为属性
        self.assertTrue(hasattr(result, '_pagination'))
        pagination = getattr(result, '_pagination')
        self.assertEqual(pagination['current_page'], 1)
        self.assertEqual(pagination['total_count'], 100)


class TestApiFunction(unittest.TestCase):
    """测试api函数"""

    def test_api_success(self):
        """测试api函数成功创建客户端"""
        token = "test_token"
        base_url = "http://localhost:10000"

        client = api(token=token, base_url=base_url)

        self.assertIsInstance(client, DataApi)
        self.assertEqual(client._DataApi__token, token)
        self.assertEqual(client._DataApi__base_url, base_url)

    def test_api_empty_token(self):
        """测试api函数token为空的情况"""
        with self.assertRaises(ValueError) as context:
            api(token='')

        self.assertIn('token不能为空', str(context.exception))




class TestIntegration(unittest.TestCase):
    """集成测试，需要实际的API服务运行"""

    def setUp(self):
        """设置集成测试环境"""
        # 这些测试需要API服务运行在localhost:10000
        self.base_url = "http://localhost:10000"
        self.token = "29a5378adfe44dadbf617efe1525766a"  # 使用有效的token
        self.client = api(token=self.token, base_url=self.base_url)

    @unittest.skip("需要实际API服务运行")
    def test_real_hsgt_fund_page_list_query(self):
        """测试真实的HSGT分页查询"""
        result = self.client.hsgt_fund_page_list(page=1, page_size=5)

        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn('trade_date', result.columns)
            self.assertIn('stock_code', result.columns)

    @unittest.skip("需要实际API服务运行")
    def test_real_hsgt_fund_by_stock_query(self):
        """测试真实的按股票查询"""
        result = self.client.hsgt_fund_by_stock(stock_code='00700.HK', limit=3)

        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn('trade_date', result.columns)
            self.assertIn('stock_code', result.columns)


if __name__ == '__main__':
    # 运行示例代码
    print("=== 通用客户端测试示例 ===")

    # 示例：如何使用通用客户端
    token = "29a5378adfe44dadbf617efe1525766a"
    base_url = "http://localhost:10000"

    try:
        # 初始化客户端
        client = api(token=token, base_url=base_url)

        print("1. 查询分页数据")
        df = client.hsgt_fund_page_list(page=1, page_size=3)
        print(f"   查询结果: {len(df)} 条记录")
        if len(df) > 0:
            print(f"   前两行数据:")
            print(f"   第1行: {df.iloc[0].to_dict()}")
            if len(df) > 1:
                print(f"   第2行: {df.iloc[1].to_dict()}")

        print("2. 查询指定字段的分页数据")
        df = client.hsgt_fund_page_list(
            page=1,
            page_size=3,
            fields='trade_date,stock_code,stock_name,hold_market_cap'
        )
        print(f"   查询结果: {len(df)} 条记录")
        if len(df) > 0:
            print(f"   前两行数据:")
            print(f"   第1行: {df.iloc[0].to_dict()}")
            if len(df) > 1:
                print(f"   第2行: {df.iloc[1].to_dict()}")

        print("3. 按股票代码查询")
        df = client.hsgt_fund_by_stock(stock_code='00700.HK', limit=5)
        print(f"   查询结果: {len(df)} 条记录")
        if len(df) > 0:
            print(f"   前两行数据:")
            print(f"   第1行: {df.iloc[0].to_dict()}")
            if len(df) > 1:
                print(f"   第2行: {df.iloc[1].to_dict()}")

        print("4. 按股票代码查询并指定字段")
        df = client.hsgt_fund_by_stock(
            stock_code='00700.HK',
            limit=3,
            fields='trade_date,stock_code,stock_name,hold_market_cap'
        )
        print(f"   查询结果: {len(df)} 条记录")
        if len(df) > 0:
            print(f"   前两行数据:")
            print(f"   第1行: {df.iloc[0].to_dict()}")
            if len(df) > 1:
                print(f"   第2行: {df.iloc[1].to_dict()}")

        print("示例执行完成！")

    except Exception as e:
        print(f"示例执行失败: {e}")
        print("请确保API服务运行在 http://localhost:10000 并且token有效")

    print("\n运行单元测试...")
    unittest.main(verbosity=2, exit=False)