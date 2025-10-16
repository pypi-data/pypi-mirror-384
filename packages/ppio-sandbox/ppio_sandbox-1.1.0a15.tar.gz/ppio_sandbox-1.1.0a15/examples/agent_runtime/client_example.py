"""
Agent Runtime Client 使用示例

展示如何使用 Agent Client 模块调用部署在 PPIO 沙箱中的 Agent
"""

import asyncio
import os
from ppio_sandbox.agent_runtime.client import (
    AgentRuntimeClient, 
    InvocationRequest,
    InvocationResponse
)


async def basic_client_example():
    """基础客户端使用示例"""
    print("=== 基础客户端使用示例 ===")
    
    # 方式一：使用环境变量（推荐）
    # 设置环境变量：export PPIO_API_KEY=your-api-key
    async with AgentRuntimeClient() as client:
        
        # 列出可用的 Agent 模板
        print("\n1. 列出可用模板...")
        try:
            templates = await client.list_templates()
            print(f"找到 {len(templates)} 个模板:")
            
            for template in templates[:3]:  # 显示前3个
                print(f"  - {template.name} (v{template.version}) - {template.template_id}")
                
        except Exception as e:
            print(f"列出模板失败: {e}")
            return
        
        if not templates:
            print("没有找到可用模板，请先部署一些 Agent")
            return
        
        # 使用第一个模板进行测试
        template_id = templates[0].template_id
        print(f"\n2. 使用模板 {template_id} 调用 Agent...")
        
        # 自动管理会话（适合简单场景）
        request = InvocationRequest(
            prompt="你好，请介绍一下你自己",
            metadata={"user_id": "example_user"}
        )
        
        try:
            response = await client.invoke_agent(
                template_id=template_id,
                request=request
            )
            
            print(f"Agent 响应: {response.result}")
            print(f"处理时间: {response.duration:.2f}s")
            
        except Exception as e:
            print(f"调用 Agent 失败: {e}")


async def session_management_example():
    """会话管理示例"""
    print("\n=== 会话管理示例 ===")
    
    async with AgentRuntimeClient() as client:
        
        # 获取可用模板
        templates = await client.list_templates()
        if not templates:
            print("没有找到可用模板")
            return
            
        template_id = templates[0].template_id
        
        # 创建独立的 Sandbox 会话
        print(f"\n1. 创建会话...")
        session = await client.create_session(
            template_id=template_id,
            timeout_seconds=600  # 10分钟
        )
        
        print(f"会话已创建，Sandbox ID: {session.sandbox_id}")
        
        try:
            # 多轮对话
            questions = [
                "你好，我是新用户",
                "你能做什么？",
                "帮我解释一下人工智能"
            ]
            
            for i, question in enumerate(questions):
                print(f"\n第 {i+1} 轮对话:")
                print(f"用户: {question}")
                
                request = InvocationRequest(
                    prompt=question,
                    metadata={"conversation_turn": i + 1}
                )
                
                response = await session.invoke(request)
                print(f"Agent: {response.get('result', 'No response')}")
                
                # 检查会话状态
                status = await session.get_status()
                print(f"会话状态: {status}")
                
        finally:
            # 关闭会话会自动销毁对应的 Sandbox
            await session.close()
            print("会话已关闭")


async def streaming_example():
    """流式响应示例"""
    print("\n=== 流式响应示例 ===")
    
    async with AgentRuntimeClient() as client:
        
        templates = await client.list_templates()
        if not templates:
            print("没有找到可用模板")
            return
            
        template_id = templates[0].template_id
        
        print(f"开始流式调用 Agent...")
        
        try:
            # 流式调用
            stream = await client.invoke_agent_stream(
                template_id=template_id,
                request={
                    "prompt": "请写一个关于人工智能的简短介绍",
                    "max_tokens": 500
                }
            )
            
            print("Agent 响应 (流式):")
            async for chunk in stream:
                print(chunk, end="", flush=True)
            print("\n流式响应完成")
            
        except Exception as e:
            print(f"流式调用失败: {e}")


async def template_management_example():
    """模板管理示例"""
    print("\n=== 模板管理示例 ===")
    
    async with AgentRuntimeClient() as client:
        
        # 列出所有模板
        print("1. 列出所有模板...")
        templates = await client.list_templates()
        
        for template in templates:
            print(f"\n模板: {template.name}")
            print(f"  ID: {template.template_id}")
            print(f"  版本: {template.version}")
            print(f"  作者: {template.author}")
            print(f"  描述: {template.description}")
            print(f"  标签: {', '.join(template.tags)}")
            
            # 显示 Agent 元信息
            metadata = template.metadata
            if metadata and "agent" in metadata:
                agent_info = metadata["agent"]
                agent_metadata = agent_info.get("metadata", {})
                print(f"  Agent 名称: {agent_metadata.get('name', '未知')}")
                print(f"  入口文件: {agent_info.get('spec', {}).get('entrypoint', 'app.py')}")
        
        # 按标签过滤
        print("\n2. 按标签过滤模板...")
        tagged_templates = await client.list_templates(tags=["ai", "chat"])
        print(f"找到 {len(tagged_templates)} 个带有 'ai' 或 'chat' 标签的模板")
        
        # 获取特定模板详情
        if templates:
            template_id = templates[0].template_id
            print(f"\n3. 获取模板 {template_id} 的详细信息...")
            
            detailed_template = await client.get_template(template_id)
            print(f"创建时间: {detailed_template.created_at}")
            print(f"更新时间: {detailed_template.updated_at}")
            print(f"状态: {detailed_template.status}")


async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    try:
        # 使用无效的 API Key
        client = AgentRuntimeClient(api_key="invalid-key")
        
        async with client:
            templates = await client.list_templates()
            
    except Exception as e:
        print(f"预期的认证错误: {type(e).__name__}: {e}")
    
    # 正常客户端
    async with AgentRuntimeClient() as client:
        
        # 尝试获取不存在的模板
        try:
            await client.get_template("non-existent-template-id")
        except Exception as e:
            print(f"预期的模板不存在错误: {type(e).__name__}: {e}")
        
        # 尝试调用不存在的模板
        try:
            await client.invoke_agent(
                template_id="non-existent-template-id",
                request="Hello"
            )
        except Exception as e:
            print(f"预期的调用错误: {type(e).__name__}: {e}")


async def main():
    """主函数"""
    print("PPIO Agent Runtime Client 示例")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("PPIO_API_KEY"):
        print("警告: 未设置 PPIO_API_KEY 环境变量")
        print("请设置: export PPIO_API_KEY=your-api-key")
        print("某些示例可能无法正常工作")
        print()
    
    try:
        await basic_client_example()
        await session_management_example()
        await streaming_example()
        await template_management_example()
        await error_handling_example()
        
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"\n示例执行出错: {e}")
    
    print("\n示例执行完成")


if __name__ == "__main__":
    asyncio.run(main())