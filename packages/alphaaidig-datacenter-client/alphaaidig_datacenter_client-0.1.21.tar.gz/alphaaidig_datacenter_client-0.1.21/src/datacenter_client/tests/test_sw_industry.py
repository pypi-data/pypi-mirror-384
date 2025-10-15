from datacenter_client.tests.base import BaseClientTest
import unittest
import json


class TestSWIndustryClient(BaseClientTest):
    """申万行业客户端测试类"""
    
    def test_get_level1_list(self):
        """测试获取一级行业列表"""
        print("\n" + "=" * 50)
        print("测试申万行业客户端 - 获取一级行业列表")
        print("=" * 50)
        
        try:
            # 先获取原始数据结构
            raw_response = self.client.sw_industry._client._request("GET", "/api/v1/sw_industry/level1/list")
            print("原始数据结构:")
            print(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
            # 然后使用DTO处理
            result = self.client.sw_industry.get_level1_list()
            print(f"状态: {result.status}")
            self.print_list_info(result)
        except Exception as e:
            print(f"测试获取一级行业列表时出错: {e}")
    
    def test_get_level2_list(self):
        """测试获取二级行业列表"""
        print("\n" + "=" * 50)
        print("测试申万行业客户端 - 获取二级行业列表")
        print("=" * 50)
        
        try:
            # 不带参数测试
            raw_response = self.client.sw_industry._client._request("GET", "/api/v1/sw_industry/level2/list")
            print("不带参数测试 - 原始数据结构:")
            print(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
            result = self.client.sw_industry.get_level2_list()
            print(f"不带参数测试 - 状态: {result.status}")
            self.print_list_info(result)
        except Exception as e:
            print(f"测试获取二级行业列表时出错: {e}")
    
    def test_get_level3_list(self):
        """测试获取三级行业列表"""
        print("\n" + "=" * 50)
        print("测试申万行业客户端 - 获取三级行业列表")
        print("=" * 50)
        
        try:
            # 不带参数测试
            raw_response = self.client.sw_industry._client._request("GET", "/api/v1/sw_industry/level3/list")
            print("不带参数测试 - 原始数据结构:")
            print(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
            result = self.client.sw_industry.get_level3_list()
            print(f"不带参数测试 - 状态: {result.status}")
            self.print_list_info(result)
        except Exception as e:
            print(f"测试获取三级行业列表时出错: {e}")
    
    def test_get_all_industries(self):
        """测试获取所有行业数据"""
        print("\n" + "=" * 50)
        print("测试申万行业客户端 - 获取所有行业数据")
        print("=" * 50)
        
        try:
            # 先获取原始数据结构
            raw_response = self.client.sw_industry._client._request("GET", "/api/v1/sw_industry/all")
            print("原始数据结构:")
            print(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
            # 然后使用DTO处理
            result = self.client.sw_industry.get_all_industries()
            print(f"状态: {result.status}")
            self.print_list_info(result)
        except Exception as e:
            print(f"测试获取所有行业数据时出错: {e}")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加所有测试方法
    suite.addTest(TestSWIndustryClient('test_get_level1_list'))
    suite.addTest(TestSWIndustryClient('test_get_level2_list'))
    suite.addTest(TestSWIndustryClient('test_get_level3_list'))
    suite.addTest(TestSWIndustryClient('test_get_all_industries'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)