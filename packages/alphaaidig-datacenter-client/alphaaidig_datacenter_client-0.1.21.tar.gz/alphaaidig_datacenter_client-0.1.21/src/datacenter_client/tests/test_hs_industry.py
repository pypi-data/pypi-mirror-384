from datacenter_client.tests.base import BaseClientTest
import unittest
from typing import List, Dict, Any


class TestHSIndustryClient(BaseClientTest):
    """恒生行业客户端测试类"""
    
    def test_level1_list(self):
        """测试获取恒生一级行业列表"""
        result = self.client.hs_industry.get_level1_list()
        self.assertEqual(result.status, "success")
        
        items = result.items
        self.assertIsInstance(items, List)
        self.assertGreater(len(items), 0)
        
        # 验证数据结构
        for item in items[:3]:  # 只检查前3个
            self.assertTrue(hasattr(item, 'industry_code'))
            self.assertTrue(hasattr(item, 'name'))
            self.assertIsNotNone(item.industry_code)
            self.assertIsNotNone(item.name)
    
    def test_level2_list(self):
        """测试获取恒生二级行业列表"""
        # 先尝试不带参数获取二级行业列表
        result = self.client.hs_industry.get_level2_list()
        self.assertEqual(result.status, "success")
        
        items = result.items
        self.assertIsInstance(items, List)
        self.assertGreater(len(items), 0)
        
        # 验证数据结构
        for item in items[:3]:  # 只检查前3个
            self.assertTrue(hasattr(item, 'industry_code'))
            self.assertTrue(hasattr(item, 'name'))
            self.assertTrue(hasattr(item, 'level1_industry_code'))
            self.assertTrue(hasattr(item, 'level1_name'))
            self.assertIsNotNone(item.industry_code)
            self.assertIsNotNone(item.name)
            self.assertIsNotNone(item.level1_industry_code)
            self.assertIsNotNone(item.level1_name)
        
        # 尝试使用一级行业代码获取二级行业列表
        level1_code = "HS0000"  # 能源业
        result_with_param = self.client.hs_industry.get_level2_list(level1_code=level1_code)
        self.assertEqual(result_with_param.status, "success")
        
        # 验证所有返回的二级行业都属于指定的一级行业
        for item in result_with_param.items:
            self.assertEqual(item.level1_industry_code, level1_code)
    
    def test_level3_list(self):
        """测试获取恒生三级行业列表"""
        # 先尝试不带参数获取三级行业列表
        result = self.client.hs_industry.get_level3_list()
        self.assertEqual(result.status, "success")
        
        items = result.items
        self.assertIsInstance(items, List)
        self.assertGreater(len(items), 0)
        
        # 验证数据结构
        for item in items[:3]:  # 只检查前3个
            self.assertTrue(hasattr(item, 'industry_code'))
            self.assertTrue(hasattr(item, 'name'))
            self.assertTrue(hasattr(item, 'level1_industry_code'))
            self.assertTrue(hasattr(item, 'level1_name'))
            self.assertTrue(hasattr(item, 'level2_industry_code'))
            self.assertTrue(hasattr(item, 'level2_name'))
            self.assertIsNotNone(item.industry_code)
            self.assertIsNotNone(item.name)
            self.assertIsNotNone(item.level1_industry_code)
            self.assertIsNotNone(item.level1_name)
            self.assertIsNotNone(item.level2_industry_code)
            self.assertIsNotNone(item.level2_name)
        
        # 尝试使用一级行业代码获取三级行业列表
        level1_code = "HS0000"  # 能源业
        result_with_param1 = self.client.hs_industry.get_level3_list(level1_code=level1_code)
        self.assertEqual(result_with_param1.status, "success")
        
        # 验证所有返回的三级行业都属于指定的一级行业
        for item in result_with_param1.items:
            self.assertEqual(item.level1_industry_code, level1_code)
        
        # 尝试使用一级行业代码和二级行业代码获取三级行业列表
        level2_code = "001000"  # 石油及天然气
        result_with_param2 = self.client.hs_industry.get_level3_list(
            level1_code=level1_code, 
            level2_code=level2_code
        )
        self.assertEqual(result_with_param2.status, "success")
        
        # 验证所有返回的三级行业都属于指定的一级和二级行业
        for item in result_with_param2.items:
            self.assertEqual(item.level1_industry_code, level1_code)
            self.assertEqual(item.level2_industry_code, level2_code)
    
    def test_all_industries(self):
        """测试获取所有恒生行业信息"""
        result = self.client.hs_industry.get_all_industries()
        self.assertEqual(result.status, "success")
        
        industries = result.industries
        self.assertIsInstance(industries, List)
        self.assertGreater(len(industries), 0)
        
        # 验证数据结构
        for item in industries[:3]:  # 只检查前3个
            self.assertTrue(hasattr(item, 'level1_industry_code'))
            self.assertTrue(hasattr(item, 'level1_industry_name'))
            self.assertTrue(hasattr(item, 'id'))
            self.assertIsNotNone(item.level1_industry_code)
            self.assertIsNotNone(item.level1_industry_name)
            self.assertIsNotNone(item.id)
    
    def test_summary(self):
        """测试获取统计信息"""
        result = self.client.hs_industry.get_summary()
        self.assertEqual(result.status, "success")
        
        summary = result.summary
        self.assertIsNotNone(summary)
        
        # 验证数据结构
        self.assertTrue(hasattr(summary, 'total_industries'))
        self.assertTrue(hasattr(summary, 'level_distribution'))
        self.assertIsInstance(summary.total_industries, int)
        self.assertIsInstance(summary.level_distribution, dict)
        
        # 验证级别分布包含1、2、3级
        self.assertIsNotNone(summary.level_distribution)
        level_distribution: Dict[int, int] = summary.level_distribution  # type: ignore
        self.assertIsInstance(level_distribution, dict)
        self.assertIn(1, level_distribution)
        self.assertIn(2, level_distribution)
        self.assertIn(3, level_distribution)
        
        # 验证各级别数量为正整数
        self.assertGreater(level_distribution[1], 0)
        self.assertGreater(level_distribution[2], 0)
        self.assertGreater(level_distribution[3], 0)
    
    def test_api_data_consistency(self):
        """测试API数据一致性"""
        # 获取三级行业数据
        level3_result = self.client.hs_industry.get_level3_list()
        level3_items = level3_result.items
        
        # 获取一级行业数据
        level1_result = self.client.hs_industry.get_level1_list()
        level1_items = level1_result.items
        
        # 获取二级行业数据
        level2_result = self.client.hs_industry.get_level2_list()
        level2_items = level2_result.items
        
        self.assertGreater(len(level1_items), 0)
        self.assertGreater(len(level2_items), 0)
        self.assertGreater(len(level3_items), 0)
        
        # 从三级行业数据中提取所有一级和二级行业代码
        level1_codes_from_level3 = set()
        level2_codes_from_level3 = set()
        
        for item in level3_items:
            level1_codes_from_level3.add(item.level1_industry_code)
            level2_codes_from_level3.add(item.level2_industry_code)
        
        # 检查数据一致性
        self.assertEqual(len(level1_items), len(level1_codes_from_level3))
        self.assertEqual(len(level2_items), len(level2_codes_from_level3))


if __name__ == "__main__":
    unittest.main()