from datacenter_client.tests.base import BaseClientTest
import unittest


class TestMarginAnalysisClient(BaseClientTest):
    """融资融券分析客户端测试类"""
    
    def test_page_list(self):
        """测试通用分页获取融资融券分析"""
        print("\n" + "=" * 50)
        print("测试融资融券分析客户端 - 通用分页获取")
        print("=" * 50)
        
        try:
            result = self.client.margin_analysis.page_list(analysis_type="index", target_code="000300.SH", page=1, page_size=5)
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
        except Exception as e:
            print(f"测试通用分页获取时出错: {e}")
    
    def test_list(self):
        """测试批量获取融资融券分析"""
        print("\n" + "=" * 50)
        print("测试融资融券分析客户端 - 批量获取")
        print("=" * 50)
        
        try:
            result = self.client.margin_analysis.list(
                analysis_type="industry", 
                target_codes=['801010.SI', '801030.SI', '801040.SI', '801050.SI', '801080.SI', '801880.SI', '801110.SI', '801120.SI', '801130.SI', '801140.SI', '801150.SI', '801160.SI', '801170.SI', '801180.SI', '801200.SI', '801210.SI', '801780.SI', '801790.SI', '801230.SI', '801710.SI', '801720.SI', '801730.SI', '801890.SI', '801740.SI', '801750.SI', '801760.SI', '801770.SI', '801950.SI', '801960.SI', '801970.SI', '801980.SI'], 
                start_date="20230901", 
                end_date="20250922"
            )   
            print(f"状态: {result.status}")
            self.print_list_info(result)
        except Exception as e:
            print(f"测试批量获取时出错: {e}")
    
    

if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加单个测试方法
    suite.addTest(TestMarginAnalysisClient('test_page_list'))
    suite.addTest(TestMarginAnalysisClient('test_list'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)