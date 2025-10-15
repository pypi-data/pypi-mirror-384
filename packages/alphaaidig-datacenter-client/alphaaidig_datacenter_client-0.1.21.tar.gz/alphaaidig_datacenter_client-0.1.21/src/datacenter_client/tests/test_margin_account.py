from datacenter_client.tests.base import BaseClientTest
import unittest

class TestMarginAccountClient(BaseClientTest):
    """融资融券账户客户端测试类"""

    def test_page_list(self):
        """测试分页获取融资融券账户列表"""
        print("\n" + "=" * 50)
        print("测试融资融券账户客户端 - 分页获取列表")
        print("=" * 50)
        
        try:
            result = self.client.margin_account.page_list(page=1, page_size=5)
            self.print_pagination_info(result)
            self.assertTrue(hasattr(result, 'items'))
            self.assertEqual(len(result.items), 5)
        except Exception as e:
            self.fail(f"测试分页获取列表时出错: {e}")

    def test_list(self):
        """测试获取融资融券账户列表（不分页）"""
        print("\n" + "=" * 50)
        print("测试融资融券账户客户端 - 获取列表（不分页）")
        print("=" * 50)
        
        try:
            result = self.client.margin_account.list(limit=5)
            self.assertTrue(hasattr(result, 'items'))
            self.assertTrue(hasattr(result, 'total'))
            self.assertLessEqual(len(result.items), 5)
            self.assertEqual(len(result.items), result.total)
            print(f"获取到 {len(result.items)} 条记录")
        except Exception as e:
            self.fail(f"测试获取列表时出错: {e}")




if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加单个测试方法
    suite.addTest(TestMarginAccountClient('test_page_list'))
    suite.addTest(TestMarginAccountClient('test_list'))

    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)