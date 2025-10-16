#!/usr/bin/env python3
"""
测试重定向功能的简单脚本
"""

import requests
import time
import sys

def test_redirect(redirect_url, expected_target):
    """测试重定向功能"""
    print(f"🔍 测试重定向: {redirect_url}")
    
    try:
        response = requests.get(redirect_url, allow_redirects=False, timeout=5)
        
        if response.status_code == 302:
            location = response.headers.get('Location')
            print(f"✅ 重定向成功!")
            print(f"   状态码: {response.status_code}")
            print(f"   重定向到: {location}")
            
            if expected_target in location:
                print(f"✅ 重定向目标正确!")
                return True
            else:
                print(f"❌ 重定向目标不匹配!")
                print(f"   期望包含: {expected_target}")
                print(f"   实际目标: {location}")
                return False
        else:
            print(f"❌ 重定向失败!")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("用法: python test_redirect.py <redirect_url> <expected_target>")
        print("示例: python test_redirect.py http://127.0.0.1:9001 https://agentchat.vercel.app")
        sys.exit(1)
    
    redirect_url = sys.argv[1]
    expected_target = sys.argv[2]
    
    print("🚀 开始测试重定向功能...")
    print(f"   重定向 URL: {redirect_url}")
    print(f"   期望目标: {expected_target}")
    print()
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)
    
    # 测试重定向
    success = test_redirect(redirect_url, expected_target)
    
    if success:
        print("\n🎉 重定向功能测试通过!")
    else:
        print("\n💥 重定向功能测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
