from datacenter_client.tests.base import BaseClientTest
import unittest


class TestHKStockClient(BaseClientTest):
    """港股客户端测试类"""
    
    def test_list(self):
        """测试获取港股列表"""
        print("\n" + "=" * 50)
        print("测试港股客户端 - 获取列表")
        print("=" * 50)
        
        try:
            result = self.client.hk_stock.page_list()
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
        except Exception as e:
            print(f"测试获取列表时出错: {e}")
    
    def test_get(self):
        """测试获取单只港股信息"""
        print("\n" + "=" * 50)
        print("测试港股客户端 - 获取单只股票信息")
        print("=" * 50)
        
        try:
            result = self.client.hk_stock.get("00700")
            print(f"状态: {result.status}")
            self.print_item_info(result)
        except Exception as e:
            print(f"测试获取单只股票信息时出错: {e}")
    
    def test_page_list(self):
        """测试分页获取港股列表"""
        print("\n" + "=" * 50)
        print("测试港股客户端 - 分页获取列表")
        print("=" * 50)
        
        try:
            result = self.client.hk_stock.page_list(page=1, page_size=5)
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
        except Exception as e:
            print(f"测试分页获取列表时出错: {e}")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加单个测试方法
    suite.addTest(TestHKStockClient('test_list'))
    suite.addTest(TestHKStockClient('test_get'))
    suite.addTest(TestHKStockClient('test_page_list'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)