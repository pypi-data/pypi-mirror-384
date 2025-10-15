#!/usr/bin/env python3
"""
运行所有客户端测试的脚本
"""

import unittest
import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 设置包名
package_name = os.path.basename(current_dir)

# 导入测试模块
from datacenter_client.tests.test_a_stock import TestAStockClient
from datacenter_client.tests.test_hk_stock import TestHKStockClient
from datacenter_client.tests.test_hs_industry import TestHSIndustryClient
from datacenter_client.tests.test_margin_detail import TestMarginDetailClient

from datacenter_client.tests.test_margin_analysis import TestMarginAnalysisClient
from datacenter_client.tests.test_sw_industry import TestSWIndustryClient
from datacenter_client.tests.test_sw_industry_company import TestSWIndustryCompanyClient
from datacenter_client.tests.test_margin_account import TestMarginAccountClient
from datacenter_client.tests.test_universal_client import TestDataApi


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestAStockClient))
    suite.addTests(loader.loadTestsFromTestCase(TestHKStockClient))
    suite.addTests(loader.loadTestsFromTestCase(TestHSIndustryClient))
    suite.addTests(loader.loadTestsFromTestCase(TestMarginDetailClient))

    suite.addTests(loader.loadTestsFromTestCase(TestMarginAnalysisClient))
    suite.addTests(loader.loadTestsFromTestCase(TestSWIndustryClient))
    suite.addTests(loader.loadTestsFromTestCase(TestSWIndustryCompanyClient))
    suite.addTests(loader.loadTestsFromTestCase(TestMarginAccountClient))
    suite.addTests(loader.loadTestsFromTestCase(TestDataApi))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_specific_test(test_class_name):
    """运行特定的测试类"""
    test_classes = {
        'a_stock': TestAStockClient,
        'hk_stock': TestHKStockClient,
        'hs_industry': TestHSIndustryClient,
        'margin_detail': TestMarginDetailClient,
        'margin_analysis': TestMarginAnalysisClient,
        'sw_industry': TestSWIndustryClient,
        'sw_industry_company': TestSWIndustryCompanyClient,
        'tushare': TestDataApi,
    }
    
    if test_class_name not in test_classes:
        print(f"未找到测试类: {test_class_name}")
        print(f"可用的测试类: {', '.join(test_classes.keys())}")
        return False
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(test_classes[test_class_name]))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行特定测试类
        test_class = sys.argv[1]
        success = run_specific_test(test_class)
    else:
        # 运行所有测试
        success = run_all_tests()
    
    sys.exit(0 if success else 1)