#!/usr/bin/env python3
"""
简化的Anthropic配置测试脚本
Simplified Anthropic configuration test script
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

def test_config():
    """测试配置加载"""
    print("🔧 JobCatcher Anthropic配置测试 / Anthropic Configuration Test")
    print("=" * 60)
    
    print("1. 环境变量配置 / Environment Variables:")
    print(f"   ANTHROPIC_API_KEY: {'✅ 已设置' if settings.ANTHROPIC_API_KEY != 'demo_key' else '❌ 使用默认值'}")
    print(f"   ANTHROPIC_BASE_URL: {settings.ANTHROPIC_BASE_URL}")
    print(f"   CLAUDE_TEMPERATURE: {settings.CLAUDE_TEMPERATURE}")
    print()
    
    print("2. 配置验证 / Configuration Validation:")
    
    # 验证API密钥格式
    if settings.ANTHROPIC_API_KEY.startswith("sk-"):
        print("   ✅ API密钥格式正确")
    else:
        print("   ⚠️  API密钥格式可能不正确")
    
    # 验证Base URL
    if settings.ANTHROPIC_BASE_URL.startswith("https://"):
        print("   ✅ Base URL格式正确")
    else:
        print("   ❌ Base URL格式不正确")
    
    # 验证温度设置
    if 0.0 <= settings.CLAUDE_TEMPERATURE <= 1.0:
        print(f"   ✅ 温度设置合理: {settings.CLAUDE_TEMPERATURE}")
    else:
        print(f"   ❌ 温度设置超出范围: {settings.CLAUDE_TEMPERATURE}")
    
    print()
    
    print("3. 推荐设置 / Recommended Settings:")
    if settings.CLAUDE_TEMPERATURE == 0.2:
        print("   ✅ 温度设置为推荐值 0.2")
    else:
        print(f"   ⚠️  当前温度 {settings.CLAUDE_TEMPERATURE}，推荐使用 0.2")
    
    print()
    print("🎉 配置测试完成 / Configuration Test Complete!")

if __name__ == "__main__":
    test_config() 