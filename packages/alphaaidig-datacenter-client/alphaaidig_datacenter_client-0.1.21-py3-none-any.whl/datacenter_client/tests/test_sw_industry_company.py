from datacenter_client.tests.base import BaseClientTest
from datacenter_client.dto import SWIndustryCompanyItem, IndustryCompanyCountItem
import unittest


class TestSWIndustryCompanyClient(BaseClientTest):
    """申万行业公司客户端测试类"""
    
    def test_page_list(self):
        """测试分页获取申万行业公司列表"""
        print("\n" + "=" * 50)
        print("测试申万行业公司客户端 - 分页获取列表")
        print("=" * 50)
        
        try:
            result = self.client.sw_industry_company.page_list(page=1, page_size=5)
            print(f"状态: {result.status}")
            self.print_pagination_info(result)
            
            # 测试DTO功能
            if result.items:
                item = result.items[0]
                self.assertIsInstance(item, SWIndustryCompanyItem)
                print(f"第一条记录的股票代码: {item.stock_code}")
                print(f"第一条记录的股票名称: {item.stock_name}")
                print(f"第一条记录的行业代码: {item.industry_code}")
                print(f"第一条记录的一级行业名称: {item.level1_industry}")
                print(f"第一条记录的一级行业代码: {item.level1_industry_code}")
        except Exception as e:
            print(f"测试分页获取列表时出错: {e}")
    
    def test_list(self):
        """测试获取申万行业公司列表"""
        print("\n" + "=" * 50)
        print("测试申万行业公司客户端 - 获取列表")
        print("=" * 50)
        
        try:
            result = self.client.sw_industry_company.list()
            print(f"状态: {result.status}")
            self.print_list_info(result)
            
            # 测试DTO功能
            if result.items:
                item = result.items[0]
                self.assertIsInstance(item, SWIndustryCompanyItem)
                print(f"第一条记录的股票代码: {item.stock_code}")
                print(f"第一条记录的股票名称: {item.stock_name}")
                print(f"第一条记录的行业代码: {item.industry_code}")
                print(f"第一条记录的一级行业名称: {item.level1_industry}")
                print(f"第一条记录的一级行业代码: {item.level1_industry_code}")
        except Exception as e:
            print(f"测试获取列表时出错: {e}")
    
    def test_list_with_filters(self):
        """测试使用过滤条件获取申万行业公司列表"""
        print("\n" + "=" * 50)
        print("测试申万行业公司客户端 - 使用过滤条件获取列表")
        print("=" * 50)
        
        try:
            # 使用一级行业代码过滤
            result = self.client.sw_industry_company.list(level1_industry_code="801010.SI")
            print(f"状态: {result.status}")
            self.print_list_info(result)
            
            # 测试DTO功能
            if result.items:
                item = result.items[0]
                self.assertIsInstance(item, SWIndustryCompanyItem)
                print(f"第一条记录的股票代码: {item.stock_code}")
                print(f"第一条记录的股票名称: {item.stock_name}")
                print(f"第一条记录的行业代码: {item.industry_code}")
                print(f"第一条记录的一级行业名称: {item.level1_industry}")
                print(f"第一条记录的一级行业代码: {item.level1_industry_code}")
        except Exception as e:
            print(f"测试使用过滤条件获取列表时出错: {e}")
    
    def test_validation_error(self):
        """测试不提供查询条件时的验证错误"""
        print("\n==================================================")
        print("测试申万行业公司客户端 - 验证错误")
        print("==================================================")
        
        # 测试page_list方法
        with self.assertRaises(ValueError) as context:
            self.client.sw_industry_company.page_list()
        print(f"成功捕获验证错误: {str(context.exception)}")
        
        # 测试list方法
        with self.assertRaises(ValueError) as context:
            self.client.sw_industry_company.list()
        print(f"成功捕获验证错误: {str(context.exception)}")
        
        # 测试industry_company_count方法的type参数验证
        with self.assertRaises(ValueError) as context:
            self.client.sw_industry_company.industry_company_count(type="invalid")
        print(f"成功捕获验证错误: {str(context.exception)}")
    
    def test_industry_company_count_level1(self):
        """测试按一级行业统计公司数量"""
        print("\n==================================================")
        print("测试申万行业公司客户端 - 按一级行业统计公司数量")
        print("==================================================")
        
        try:
            result = self.client.sw_industry_company.industry_company_count(type="level1")
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.assertTrue(len(result.items) > 0)
            
            # 打印前5条记录
            for i, item in enumerate(result.items[:5]):
                print(f"第{i+1}条记录: 行业代码={item.industry_code} 行业名称={item.industry_name} 公司数量={item.company_count}")
                
                # 验证字段类型
                self.assertIsInstance(item, IndustryCompanyCountItem)
                self.assertIsInstance(item.industry_code, str)
                self.assertIsInstance(item.industry_name, str)
                self.assertIsInstance(item.company_count, int)
                self.assertTrue(item.company_count >= 0)
            
            print(f"总共返回了{len(result.items)}个一级行业的统计结果")
            
        except Exception as e:
            print(f"测试按一级行业统计公司数量时出错: {str(e)}")
            raise
    
    def test_industry_company_count_level2(self):
        """测试按二级行业统计公司数量"""
        print("\n==================================================")
        print("测试申万行业公司客户端 - 按二级行业统计公司数量")
        print("==================================================")
        
        try:
            result = self.client.sw_industry_company.industry_company_count(type="level2")
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.assertTrue(len(result.items) > 0)
            
            # 打印前5条记录
            for i, item in enumerate(result.items[:5]):
                print(f"第{i+1}条记录: 行业代码={item.industry_code} 行业名称={item.industry_name} 公司数量={item.company_count}")
                
                # 验证字段类型
                self.assertIsInstance(item, IndustryCompanyCountItem)
                self.assertIsInstance(item.industry_code, str)
                self.assertIsInstance(item.industry_name, str)
                self.assertIsInstance(item.company_count, int)
                self.assertTrue(item.company_count >= 0)
            
            print(f"总共返回了{len(result.items)}个二级行业的统计结果")
            
        except Exception as e:
            print(f"测试按二级行业统计公司数量时出错: {str(e)}")
            raise
    
    def test_industry_company_count_level3(self):
        """测试按三级行业统计公司数量"""
        print("\n==================================================")
        print("测试申万行业公司客户端 - 按三级行业统计公司数量")
        print("==================================================")
        
        try:
            result = self.client.sw_industry_company.industry_company_count(type="level3")
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.assertTrue(len(result.items) > 0)
            
            # 打印前5条记录
            for i, item in enumerate(result.items[:5]):
                print(f"第{i+1}条记录: 行业代码={item.industry_code} 行业名称={item.industry_name} 公司数量={item.company_count}")
                
                # 验证字段类型
                self.assertIsInstance(item, IndustryCompanyCountItem)
                self.assertIsInstance(item.industry_code, str)
                self.assertIsInstance(item.industry_name, str)
                self.assertIsInstance(item.company_count, int)
                self.assertTrue(item.company_count >= 0)
            
            print(f"总共返回了{len(result.items)}个三级行业的统计结果")
            
        except Exception as e:
            print(f"测试按三级行业统计公司数量时出错: {str(e)}")
            raise
    
    def test_industry_company_count_with_filters(self):
        """测试使用过滤条件按行业统计公司数量"""
        print("\n==================================================")
        print("测试申万行业公司客户端 - 使用过滤条件按行业统计公司数量")
        print("==================================================")
        
        try:
            # 使用一级行业代码过滤
            result = self.client.sw_industry_company.industry_company_count(
                type="level2",
                industry_code="801010.SI"
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            
            # 打印所有记录
            for i, item in enumerate(result.items):
                print(f"第{i+1}条记录: 行业代码={item.industry_code} 行业名称={item.industry_name} 公司数量={item.company_count}")
                
                # 验证字段类型
                self.assertIsInstance(item, IndustryCompanyCountItem)
                self.assertIsInstance(item.industry_code, str)
                self.assertIsInstance(item.industry_name, str)
                self.assertIsInstance(item.company_count, int)
                self.assertTrue(item.company_count >= 0)
            
            print(f"总共返回了{len(result.items)}个二级行业的统计结果")
            
        except Exception as e:
            print(f"测试使用过滤条件按行业统计公司数量时出错: {str(e)}")
            raise


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试方法
    suite.addTest(TestSWIndustryCompanyClient('test_page_list'))
    suite.addTest(TestSWIndustryCompanyClient('test_list'))
    suite.addTest(TestSWIndustryCompanyClient('test_list_with_filters'))
    suite.addTest(TestSWIndustryCompanyClient('test_validation_error'))
    suite.addTest(TestSWIndustryCompanyClient('test_industry_company_count_level1'))
    suite.addTest(TestSWIndustryCompanyClient('test_industry_company_count_level2'))
    suite.addTest(TestSWIndustryCompanyClient('test_industry_company_count_level3'))
    suite.addTest(TestSWIndustryCompanyClient('test_industry_company_count_with_filters'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)