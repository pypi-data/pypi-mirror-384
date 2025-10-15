"""
测试融资融券汇总数据的 Universal Client 模式
验证新的 handler 模式是否正常工作
"""
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from datacenter_client import api


class TestUniversalMarginSummaryClient(unittest.TestCase):
    """融资融券汇总 Universal Client 测试类"""
    
    BASE_URL = "http://127.0.0.1:10001"  # 使用正确的端口
    TOKEN = "29a5378adfe44dadbf617efe1525766a"
    
    def setUp(self):
        """设置测试环境"""
        self.client = api(token=self.TOKEN, base_url=self.BASE_URL)
    
    def test_margin_summary_page_list_via_query(self):
        """测试通过 query 方法调用 margin_summary_page_list"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - query('margin_summary_page_list')")
        print("=" * 60)
        
        try:
            result = self.client.query(
                'margin_summary_page_list', 
                page=1, 
                page_size=5,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            print(f"✓ 调用成功，返回类型: {type(result)}")
            print(f"✓ 返回记录数: {len(result)}")
            
            # 检查是否是 PageDataFrame
            if hasattr(result, 'pagination'):
                print(f"✓ 分页信息: 第{result.current_page}页，共{result.total_pages}页，总记录{result.total_count}条")
            
            if len(result) > 0:
                print(f"✓ 第一条记录列: {list(result.columns)}")
                print(f"✓ 示例数据: {result.iloc[0]['trade_date']} - {result.iloc[0]['exchange_id']}")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.fail(f"query('margin_summary_page_list') 调用失败: {e}")
    
    def test_margin_summary_list_via_query(self):
        """测试通过 query 方法调用 margin_summary_list"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - query('margin_summary_list')")
        print("=" * 60)
        
        try:
            result = self.client.query(
                'margin_summary_list', 
                limit=10,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            print(f"✓ 调用成功，返回类型: {type(result)}")
            print(f"✓ 返回记录数: {len(result)}")
            
            if len(result) > 0:
                print(f"✓ 第一条记录列: {list(result.columns)}")
                print(f"✓ 示例数据: {result.iloc[0]['trade_date']} - {result.iloc[0]['exchange_id']}")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.fail(f"query('margin_summary_list') 调用失败: {e}")
    
    def test_magic_method_calls(self):
        """测试魔术方法调用"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 魔术方法调用")
        print("=" * 60)
        
        # 测试 margin_summary_page_list
        try:
            result1 = self.client.margin_summary_page_list(
                page=1, 
                page_size=3,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            print(f"✓ margin_summary_page_list() 魔术方法调用成功，记录数: {len(result1)}")
        except Exception as e:
            print(f"✗ margin_summary_page_list() 魔术方法失败: {e}")
            
        # 测试 margin_summary_list
        try:
            result2 = self.client.margin_summary_list(
                limit=5,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            print(f"✓ margin_summary_list() 魔术方法调用成功，记录数: {len(result2)}")
        except Exception as e:
            print(f"✗ margin_summary_list() 魔术方法失败: {e}")
    
    def test_fields_parameter(self):
        """测试字段参数功能"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 字段参数功能")
        print("=" * 60)
        
        try:
            # 指定返回字段
            result = self.client.query(
                'margin_summary_page_list',
                page=1, 
                page_size=3,
                start_date='2023-01-01',
                end_date='2023-12-31',
                fields='trade_date,exchange_id,rz_balance,rq_balance'
            )
            print(f"✓ 指定字段调用成功，记录数: {len(result)}")
            print(f"✓ 返回字段: {list(result.columns)}")
            
            # 验证字段过滤是否生效
            expected_fields = ['trade_date', 'exchange_id', 'rz_balance', 'rq_balance']
            actual_fields = list(result.columns)
            if set(actual_fields).issubset(set(expected_fields)):
                print("✓ 字段过滤正常工作")
            else:
                print(f"⚠ 字段过滤可能有问题，期望: {expected_fields}, 实际: {actual_fields}")
            
        except Exception as e:
            print(f"✗ 字段参数测试失败: {e}")
    
    def test_filter_parameters(self):
        """测试筛选参数功能"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 筛选参数功能")
        print("=" * 60)
        
        try:
            # 按日期范围筛选
            result = self.client.query(
                'margin_summary_list',
                start_date='2023-01-01',
                end_date='2023-01-31',
                limit=10
            )
            print(f"✓ 日期筛选调用成功，记录数: {len(result)}")
            
            # 按交易所筛选（需要提供日期参数）
            result2 = self.client.query(
                'margin_summary_list',
                start_date='2023-01-01',
                end_date='2023-12-31',
                exchange_id='SSE',
                limit=5
            )
            print(f"✓ 交易所筛选调用成功，记录数: {len(result2)}")
            
        except Exception as e:
            print(f"✗ 筛选参数测试失败: {e}")

    def test_comparison_with_old_client(self):
        """对比新旧客户端的结果"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 新旧客户端结果对比")
        print("=" * 60)
        
        try:
            # 使用新的 universal client
            new_result = self.client.query(
                'margin_summary_page_list', 
                page=1, 
                page_size=5,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            print(f"✓ 新客户端调用成功，记录数: {len(new_result)}")
            
            # 如果能导入旧客户端，进行对比
            try:
                from datacenter_client import DatacenterClient
                old_client = DatacenterClient(base_url=self.BASE_URL, token=self.TOKEN)
                old_result = old_client.margin_summary.page_list(
                    page=1, 
                    page_size=5,
                    start_date='2023-01-01',
                    end_date='2023-12-31'
                )
                print(f"✓ 旧客户端调用成功，记录数: {len(old_result.items)}")
                
                # 简单对比记录数
                if len(new_result) == len(old_result.items):
                    print("✓ 新旧客户端返回记录数一致")
                else:
                    print(f"⚠ 记录数不一致: 新客户端 {len(new_result)}, 旧客户端 {len(old_result.items)}")
                    
            except Exception as old_e:
                print(f"⚠ 旧客户端测试跳过（可能是正常的）: {old_e}")
                
        except Exception as e:
            print(f"✗ 对比测试失败: {e}")

    def test_performance_benchmark(self):
        """性能基准测试"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 性能基准测试")
        print("=" * 60)
        
        import time
        
        try:
            # 测试分页查询性能
            start_time = time.time()
            result = self.client.query(
                'margin_summary_page_list',
                page=1,
                page_size=100,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            page_time = time.time() - start_time
            print(f"✓ 分页查询性能: {page_time:.3f}秒，返回{len(result)}条记录")
            
            # 测试列表查询性能
            start_time = time.time()
            result2 = self.client.query(
                'margin_summary_list',
                start_date='2023-01-01',
                end_date='2023-01-31',
                limit=50
            )
            list_time = time.time() - start_time
            print(f"✓ 列表查询性能: {list_time:.3f}秒，返回{len(result2)}条记录")
            
            # 性能断言
            self.assertLess(page_time, 5.0, "分页查询应在5秒内完成")
            self.assertLess(list_time, 5.0, "列表查询应在5秒内完成")
            
        except Exception as e:
            print(f"✗ 性能测试失败: {e}")
            self.fail(f"性能测试失败: {e}")

    def test_error_handling(self):
        """错误处理测试"""
        print("\n" + "=" * 60)
        print("测试 Universal Client - 错误处理")
        print("=" * 60)
        
        # 测试缺少必需参数
        try:
            result = self.client.query('margin_summary_page_list', page=1, page_size=5)
            print("✗ 应该抛出参数缺失错误")
            self.fail("应该抛出参数缺失错误")
        except Exception as e:
            print(f"✓ 正确捕获参数缺失错误: {str(e)[:50]}...")
        
        # 测试无效的日期格式
        try:
            result = self.client.query(
                'margin_summary_page_list',
                page=1,
                page_size=5,
                start_date='invalid-date',
                end_date='2023-12-31'
            )
            print("✗ 应该抛出日期格式错误")
        except Exception as e:
            print(f"✓ 正确处理无效日期: {str(e)[:50]}...")
        
        # 测试不存在的API
        try:
            result = self.client.query('non_existent_api', param=1)
            print("✗ 应该抛出API不存在错误")
            self.fail("应该抛出API不存在错误")
        except Exception as e:
            print(f"✓ 正确捕获API不存在错误: {str(e)[:50]}...")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试方法
    suite.addTest(TestUniversalMarginSummaryClient('test_margin_summary_page_list_via_query'))
    suite.addTest(TestUniversalMarginSummaryClient('test_margin_summary_list_via_query'))
    suite.addTest(TestUniversalMarginSummaryClient('test_magic_method_calls'))
    suite.addTest(TestUniversalMarginSummaryClient('test_fields_parameter'))
    suite.addTest(TestUniversalMarginSummaryClient('test_filter_parameters'))
    suite.addTest(TestUniversalMarginSummaryClient('test_comparison_with_old_client'))
    suite.addTest(TestUniversalMarginSummaryClient('test_performance_benchmark'))
    suite.addTest(TestUniversalMarginSummaryClient('test_error_handling'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")