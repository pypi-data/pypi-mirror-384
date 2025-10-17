"""
XGOAgent 测试脚本
测试三个机型的智能体创建和运行
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xgo_blockly.services.agents import XGOAgent


async def test_agent(model_type: str, api_key: str):
    """
    测试指定机型的智能体
    
    Args:
        model_type: 机型类型
        api_key: API密钥
    """
    print(f"\n{'='*60}")
    print(f"测试 {model_type.upper()} 智能体")
    print(f"{'='*60}\n")
    
    try:
        # 创建智能体
        agent = XGOAgent(
            model_type=model_type,
            api_key=api_key,
            model_id='qwen-max',
            system_prompt=f'你是一个{model_type.upper()}机器狗控制助手',
            long_term_memory=False,
            tools_enabled=True,
            mcp_websearch=False
        )
        
        # 测试简单对话
        response = await agent.run_async("你好！请介绍一下你的功能")
        print(f"\n【响应】:\n{response}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("XGO智能体架构测试")
    print("="*60)
    
    # 从环境变量或配置获取API密钥
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    
    if not api_key:
        print("\n⚠️  未设置API密钥，请设置环境变量 DASHSCOPE_API_KEY")
        print("或者在代码中直接设置 api_key 变量")
        return
    
    # 测试三个机型
    models = ['xgo-mini', 'xgo-lite', 'xgo-rider']
    results = {}
    
    for model in models:
        success = await test_agent(model, api_key)
        results[model] = success
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for model, success in results.items():
        status = "✓ 通过" if success else "❌ 失败"
        print(f"{model.upper():15} {status}")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    # 运行测试
    asyncio.run(main())
