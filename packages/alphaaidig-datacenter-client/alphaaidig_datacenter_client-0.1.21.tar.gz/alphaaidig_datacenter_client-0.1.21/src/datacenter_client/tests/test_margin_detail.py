from datacenter_client.tests.base import BaseClientTest
import unittest


class TestMarginDetailClient(BaseClientTest):
    """融资融券明细客户端测试类"""
    
    def test_page_list_by_date(self):
        """测试按日期分页获取融资融券明细"""
        print("\n" + "=" * 50)
        print("测试融资融券明细客户端 - 按日期分页获取")
        print("=" * 50)
        
        try:
            result = self.client.margin_detail.page_list_by_date(trade_date="2025-08-01", page=1, page_size=100)
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
        except Exception as e:
            print(f"测试按日期分页获取时出错: {e}")
    
    def test_page_list_by_stock(self):
        """测试按股票分页获取融资融券明细"""
        print("\n" + "=" * 50)
        print("测试融资融券明细客户端 - 按股票分页获取")
        print("=" * 50)
        
        try:
            result = self.client.margin_detail.page_list_by_stock(stock_code="510100.SH", page=1, page_size=5)
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
        except Exception as e:
            print(f"测试按股票分页获取时出错: {e}")
            
    def test_list_by_stock(self):
        """测试按股票获取融资融券明细（不分页）"""
        print("\n" + "=" * 50)
        print("测试融资融券明细客户端 - 按股票获取（不分页）")
        print("=" * 50)
        
        try:
            result = self.client.margin_detail.list_by_stock(stock_code="510100.SH")
            print(f"状态: {result.status}")
            print(f"获取到 {len(result.items)} 条记录")
            if result.items:
                print(f"第一条记录: {result.items[0].stock_code} - {result.items[0].trade_date}")
        except Exception as e:
            print(f"测试按股票获取（不分页）时出错: {e}")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加单个测试方法
    # suite.addTest(TestMarginDetailClient('test_page_list_by_date'))
    # suite.addTest(TestMarginDetailClient('test_page_list_by_stock'))
    suite.addTest(TestMarginDetailClient('test_list_by_stock'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)