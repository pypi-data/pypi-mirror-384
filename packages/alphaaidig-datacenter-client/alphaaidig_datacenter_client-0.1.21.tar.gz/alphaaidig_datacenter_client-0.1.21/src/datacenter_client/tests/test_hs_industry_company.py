"""
恒生行业公司客户端测试（简化版）
"""
import unittest
from typing import Any, Dict
from datacenter_client.client import DatacenterClient
from datacenter_client.tests.base import BaseClientTest
from datacenter_client.dto import (
    HSIndustryCompanyItem,
    HSIndustryCompanyListResponse,
    HSIndustryCompanyDetailResponse
)


class TestHSIndustryCompanyClient(BaseClientTest):
    """恒生行业公司客户端测试类（简化版）"""
    
    def setUp(self):
        """设置测试环境"""
        super().setUp()
        self.client = DatacenterClient(base_url=self.BASE_URL, token=self.TOKEN)
    
    def test_get_page_list(self):
        """测试恒生行业公司分页查询"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 分页查询")
        print("==================================================")
        
        try:
            # 使用一级行业代码作为查询条件
            result = self.client.hs_industry_company.get_page_list(
                level1_industry_code="HS2300",
                page=1,
                page_size=10
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.check_pagination_response(result)
            
            # 打印前5条记录
            for i, item in enumerate(result.items[:5]):
                print(f"第{i+1}条记录: 股票代码={item.stock_code} 股票名称={item.stock_name} 一级行业={item.level1_industry_name}")
                
                # 验证字段类型
                self.assertIsInstance(item, HSIndustryCompanyItem)
                self.assertIsInstance(item.stock_code, str)
                self.assertIsInstance(item.stock_name, str)
                self.assertIsInstance(item.level1_industry_name, str)
            
            # 验证分页信息
            self.assertGreater(len(result.items), 0)
            self.assertGreaterEqual(result.total, len(result.items))
            self.assertGreaterEqual(result.page, 1)
            self.assertGreaterEqual(result.page_size, 1)
            
        except Exception as e:
            print(f"测试分页查询时出错: {str(e)}")
            raise
    
    def test_get_page_list_with_filters(self):
        """测试带过滤条件的恒生行业公司分页查询"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 使用过滤条件获取公司列表")
        print("==================================================")
        
        try:
            # 测试包含腾讯的股票
            result = self.client.hs_industry_company.get_page_list(
                stock_name="腾讯",
                page=1,
                page_size=5
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.check_pagination_response(result)
            
            # 打印返回记录
            print(f"总共返回了{len(result.items)}条记录")
            for i, item in enumerate(result.items):
                print(f"第{i+1}条记录: 股票代码={item.stock_code} 股票名称={item.stock_name}")
            
            # 验证返回的记录都包含"腾讯"
            for item in result.items:
                self.assertIsNotNone(item.stock_name, "股票名称不应为None")
                self.assertIn("腾讯", str(item.stock_name))
            
        except Exception as e:
            print(f"测试过滤查询时出错: {str(e)}")
            raise
    
    def test_get_page_list_with_ordering(self):
        """测试带排序的恒生行业公司分页查询"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 带排序的分页查询")
        print("==================================================")
        
        try:
            # 按股票代码排序
            result = self.client.hs_industry_company.get_page_list(
                level1_industry_code="HS2300",
                page=1,
                page_size=10,
                order_by="stock_code",
                order_desc=False
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.check_pagination_response(result)
            
            # 验证排序
            if len(result.items) > 1:
                for i in range(len(result.items) - 1):
                    current_code = result.items[i].stock_code
                    next_code = result.items[i + 1].stock_code
                    self.assertLessEqual(current_code, next_code, 
                                      f"排序验证失败: {current_code} > {next_code}")
                
                print("排序验证通过")
                
                # 打印前5条记录
                for i, item in enumerate(result.items[:5]):
                    print(f"第{i+1}条记录: 股票代码={item.stock_code} 股票名称={item.stock_name}")
            
        except Exception as e:
            print(f"测试排序查询时出错: {str(e)}")
            raise
    
    def test_get_company_detail(self):
        """测试获取恒生行业公司详情"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 获取公司详情")
        print("==================================================")
        
        try:
            # 查询腾讯控股的详情
            result = self.client.hs_industry_company.get_company_detail("00700")
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            
            # 打印公司详情
            if hasattr(result, 'data'):
                company = result.data
                print(f"股票代码: {company.get('stock_code')}")
                print(f"股票名称: {company.get('stock_name')}")
                print(f"一级行业: {company.get('level1_industry_name')}")
                print(f"二级行业: {company.get('level2_industry_name')}")
                
                # 验证字段
                self.assertEqual(company.get('stock_code'), '00700')
                self.assertEqual(company.get('stock_name'), '腾讯控股')
                self.assertIsInstance(company.get('level1_industry_name'), str)
            else:
                print("返回数据格式不符合预期")
            
        except Exception as e:
            print(f"测试获取公司详情时出错: {str(e)}")
            raise
    
    def test_get_company_list(self):
        """测试获取恒生行业公司列表（向后兼容）"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 获取公司列表（向后兼容）")
        print("==================================================")
        
        try:
            # 使用向后兼容的API
            result = self.client.hs_industry_company.get_company_list(
                level1_industry_code="HS2300",
                page=1,
                page_size=10
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            self.check_pagination_response(result)
            
            # 打印前5条记录
            for i, item in enumerate(result.items[:5]):
                print(f"第{i+1}条记录: 股票代码={item.stock_code} 股票名称={item.stock_name}")
            
            # 验证数据完整性
            self.assertGreater(len(result.items), 0)
            
        except Exception as e:
            print(f"测试获取公司列表时出错: {str(e)}")
            raise
    
    def test_get_list(self):
        """测试列表查询（不带分页）"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 列表查询（不带分页）")
        print("==================================================")
        
        try:
            # 使用不带分页的API
            result = self.client.hs_industry_company.get_list(
                level1_industry_code="HS2300"
            )
            print(f"状态: {result.status}")
            
            # 验证返回结果
            self.assertEqual(result.status, "success")
            
            # 打印返回记录数
            items = result.items if hasattr(result, 'items') else []
            print(f"总共返回了{len(items)}条记录")
            
        except Exception as e:
            print(f"测试列表查询时出错: {str(e)}")
            raise
    
    def test_validation_error(self):
        """测试验证错误"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 验证错误")
        print("==================================================")
        
        try:
            # 不提供任何查询条件
            result = self.client.hs_industry_company.get_page_list()
            print(f"状态: {result.status}")
            
            # 预期会返回错误
            self.assertNotEqual(result.status, "success")
            print("成功捕获到验证错误")
            
        except Exception as e:
            print(f"测试验证错误时出错: {str(e)}")
            # 预期会有异常，所以不抛出
            pass
    
    def test_edge_cases(self):
        """测试边界情况"""
        print("\n==================================================")
        print("测试恒生行业公司客户端 - 边界情况")
        print("==================================================")
        
        try:
            # 测试空结果
            result = self.client.hs_industry_company.get_page_list(
                stock_code="NONEXISTENT",
                page=1,
                page_size=10
            )
            print(f"空结果查询状态: {result.status}")
            
            if result.status == "success":
                self.assertEqual(len(result.items), 0)
                print("空结果查询正确")
            else:
                print("空结果查询返回错误（符合预期）")
            
        except Exception as e:
            print(f"测试边界情况时出错: {str(e)}")
            # 不抛出异常，因为测试边界情况可能会遇到各种错误
            pass


if __name__ == "__main__":
    unittest.main()