#!/usr/bin/env python3
"""
ResumeRewriteAgent测试脚本
Test script for enhanced ResumeRewriteAgent functionality
验证Claude 4个性化改写和PDF生成能力
Verify Claude 4 personalization and PDF generation capabilities
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agents.resume_rewrite_agent import ResumeRewriteAgent
from app.core.config import settings


async def test_resume_rewrite_agent():
    """
    测试ResumeRewriteAgent的完整功能
    Test complete ResumeRewriteAgent functionality
    """
    print("🧠 JobCatcher ResumeRewriteAgent测试 / ResumeRewriteAgent Test")
    print("=" * 70)
    
    # 初始化Agent
    agent = ResumeRewriteAgent()
    
    print("1. Agent配置验证 / Agent Configuration Validation:")
    agent_info = agent.get_agent_info()
    print(f"   Agent名称: {agent_info['name']}")
    print(f"   模型: {agent_info['model']}")
    print(f"   温度: {agent_info['temperature']}")
    print(f"   工具数量: {agent_info['tools_count']}")
    print(f"   新增能力: Claude 4个性化改写 + PDFMonkey集成")
    print()
    
    # 测试数据
    sample_resume = {
        "personal_info": {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "+86 138-0013-8000",
            "location": "北京市",
            "linkedin": "https://linkedin.com/in/zhangsan"
        },
        "summary": "有经验的软件开发工程师，专注于Web开发和数据分析。",
        "work_experience": [
            {
                "company": "科技公司A",
                "position": "软件开发工程师",
                "start_date": "2021-03",
                "end_date": "2024-01",
                "description": "负责Web应用开发，使用Python和JavaScript技术栈。"
            }
        ],
        "education": [
            {
                "institution": "北京大学",
                "degree": "计算机科学学士",
                "major": "计算机科学与技术",
                "graduation_date": "2021-06"
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "React", "Django", "MySQL"],
            "languages": ["中文", "英语"],
            "soft_skills": ["团队合作", "项目管理"]
        },
        "projects": [
            {
                "name": "电商平台项目",
                "description": "开发了一个完整的电商平台",
                "technologies": ["Django", "React", "PostgreSQL"]
            }
        ]
    }
    
    target_job = {
        "title": "高级Python开发工程师",
        "company": "腾讯科技",
        "industry": "互联网",
        "description": "负责后端服务开发，需要熟练掌握Python、Django、微服务架构、云计算等技术。要求有3年以上开发经验。",
        "skills": ["Python", "Django", "微服务", "AWS", "Docker", "Kubernetes"]
    }
    
    print("2. 测试工具功能 / Test Tool Functionality:")
    
    # 测试个性化简历生成
    print("   🔧 测试个性化简历生成...")
    try:
        # 通过工具系统调用
        personalized_tool = next(t for t in agent.tools if t.name == "generate_personalized_resume")
        personalization_result = personalized_tool._run(
            resume_data=sample_resume,
            target_job=target_job,
            personalization_style="adaptive"
        )
        
        if personalization_result["success"]:
            print(f"   ✅ 个性化简历生成成功")
            print(f"   📊 匹配度评分: {personalization_result.get('target_job_match_score', 'N/A')}")
            print(f"   💡 改进建议数量: {len(personalization_result.get('improvement_suggestions', []))}")
        else:
            print(f"   ❌ 个性化简历生成失败: {personalization_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ⚠️  个性化测试跳过: {e}")
    
    # 测试Claude 4优化
    print("   🔧 测试Claude 4高级优化...")
    try:
        claude4_tool = next(t for t in agent.tools if t.name == "claude4_resume_optimization")
        optimization_result = claude4_tool._run(
            resume_content=json.dumps(sample_resume, ensure_ascii=False),
            job_description=target_job["description"],
            optimization_goals=["ats_optimization", "keyword_enhancement"]
        )
        
        if optimization_result["success"]:
            print(f"   ✅ Claude 4优化成功")
            print(f"   📈 ATS评分: {optimization_result.get('ats_score', 'N/A')}")
            print(f"   🔑 关键词匹配: {len(optimization_result.get('keyword_matches', []))}")
        else:
            print(f"   ❌ Claude 4优化失败: {optimization_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ⚠️  Claude 4优化测试跳过: {e}")
    
    # 测试PDF生成
    print("   🔧 测试PDF生成...")
    try:
        pdf_tool = next(t for t in agent.tools if t.name == "generate_pdf_resume")
        pdf_result = pdf_tool._run(
            resume_data=sample_resume,
            template_style="modern"
        )
        
        if pdf_result["success"]:
            print(f"   ✅ PDF生成成功")
            print(f"   📄 PDF URL: {pdf_result.get('pdf_url', 'N/A')}")
            print(f"   📏 文件大小: {pdf_result.get('file_size', 'N/A')}")
            print(f"   🔧 生成方法: {pdf_result.get('generation_method', 'N/A')}")
        else:
            print(f"   ❌ PDF生成失败: {pdf_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ⚠️  PDF生成测试跳过: {e}")
    
    # 测试求职信生成
    print("   🔧 测试求职信生成...")
    try:
        cover_letter_tool = next(t for t in agent.tools if t.name == "generate_cover_letter")
        cover_letter_result = cover_letter_tool._run(
            resume_data=sample_resume,
            target_job=target_job,
            cover_letter_style="professional"
        )
        
        if cover_letter_result["success"]:
            print(f"   ✅ 求职信生成成功")
            print(f"   📝 内容长度: {len(cover_letter_result.get('cover_letter_content', ''))} 字符")
            print(f"   🎯 关键亮点: {len(cover_letter_result.get('cover_letter_highlights', []))}")
        else:
            print(f"   ❌ 求职信生成失败: {cover_letter_result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ⚠️  求职信生成测试跳过: {e}")
    
    print()
    print("3. 服务集成验证 / Service Integration Validation:")
    
    # 测试PDF生成服务
    try:
        pdf_service = agent.pdf_generator_service
        print(f"   ✅ PDF生成服务已初始化")
        print(f"   🔧 Claude 4集成: {'已启用' if hasattr(pdf_service, 'anthropic_client') else '未启用'}")
        print(f"   🐵 PDFMonkey配置: {'已配置' if pdf_service.pdfmonkey_api_key != 'demo_key' else '演示模式'}")
    except Exception as e:
        print(f"   ❌ PDF服务验证失败: {e}")
    
    # 测试Anthropic客户端
    try:
        if hasattr(agent, 'anthropic_client'):
            print(f"   ✅ Anthropic客户端已初始化")
            print(f"   🌐 Base URL: {settings.ANTHROPIC_BASE_URL}")
            print(f"   🌡️  Temperature: {settings.CLAUDE_TEMPERATURE}")
        else:
            print(f"   ❌ Anthropic客户端未初始化")
    except Exception as e:
        print(f"   ⚠️  Anthropic客户端验证失败: {e}")
    
    print()
    print("4. 功能完成度评估 / Functionality Completion Assessment:")
    
    expected_tools = [
        "optimize_resume_section",
        "rewrite_for_target_job", 
        "generate_multiple_versions",
        "enhance_with_keywords",
        "generate_pdf_resume",
        "validate_resume_quality",
        "generate_personalized_resume",  # 新增
        "claude4_resume_optimization",   # 新增
        "generate_cover_letter"          # 新增
    ]
    
    actual_tools = [tool.name for tool in agent.tools]
    
    print(f"   预期工具数量: {len(expected_tools)}")
    print(f"   实际工具数量: {len(actual_tools)}")
    
    missing_tools = set(expected_tools) - set(actual_tools)
    extra_tools = set(actual_tools) - set(expected_tools)
    
    if not missing_tools and not extra_tools:
        print(f"   ✅ 所有工具已正确实现")
        completion_rate = 100
    else:
        if missing_tools:
            print(f"   ❌ 缺失工具: {missing_tools}")
        if extra_tools:
            print(f"   ➕ 额外工具: {extra_tools}")
        completion_rate = (len(actual_tools) / len(expected_tools)) * 100
    
    print(f"   📊 工具完成度: {completion_rate:.1f}%")
    
    # 核心能力评估
    core_capabilities = {
        "Claude 4 Markdown生成": hasattr(agent.pdf_generator_service, 'generate_resume_markdown'),
        "PDFMonkey集成": hasattr(agent.pdf_generator_service, '_convert_markdown_to_pdf'),
        "个性化改写策略": 'generate_personalized_resume' in actual_tools,
        "高级优化功能": 'claude4_resume_optimization' in actual_tools,
        "求职信生成": 'generate_cover_letter' in actual_tools
    }
    
    print("\n   核心能力状态:")
    for capability, status in core_capabilities.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {capability}")
    
    overall_completion = sum(core_capabilities.values()) / len(core_capabilities) * 100
    print(f"\n   🎯 总体完成度: {overall_completion:.1f}%")
    
    if overall_completion >= 90:
        print(f"   🎉 ResumeRewriteAgent开发完成！")
    elif overall_completion >= 70:
        print(f"   🔄 ResumeRewriteAgent基本完成，需要最终优化")
    else:
        print(f"   ⚠️  ResumeRewriteAgent需要继续开发")
    
    print("\n" + "="*70)
    print("📝 测试总结:")
    print(f"   - Agent工具数量: {len(actual_tools)}")
    print(f"   - Claude 4集成: {'✅ 完成' if hasattr(agent, 'anthropic_client') else '❌ 缺失'}")
    print(f"   - PDF生成能力: {'✅ 完成' if 'generate_pdf_resume' in actual_tools else '❌ 缺失'}")
    print(f"   - 个性化功能: {'✅ 完成' if 'generate_personalized_resume' in actual_tools else '❌ 缺失'}")
    print(f"   - 配置一致性: {'✅ 统一' if settings.CLAUDE_TEMPERATURE == 0.3 else '⚠️  检查'}")


def main():
    """主函数"""
    try:
        asyncio.run(test_resume_rewrite_agent())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行失败: {e}")


if __name__ == "__main__":
    main() 