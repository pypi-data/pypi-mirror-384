"""
XGO智能体 - 基于AgentScope封装的机器人控制智能体
用户无需了解AgentScope底层实现，只需使用简洁的XGOAgent接口
"""
import os
import asyncio
from typing import Optional
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory, Mem0LongTermMemory
from agentscope.embedding import DashScopeTextEmbedding
from agentscope.tool import Toolkit
from agentscope.message import Msg
from agentscope.mcp import HttpStatelessClient


class XGOAgent:
    """
    XGO机器人智能体
    
    使用示例:
        agent = XGOAgent(
            model_type='xgo-mini',
            api_key='sk-xxx',
            model_id='qwen-max'
        )
        response = agent.run("向前走3步")
        print(response)
    """
    
    def __init__(self,
                 model_type: str = 'xgo-mini',
                 api_key: str = None,
                 model_id: str = 'qwen-max',
                 system_prompt: str = None,
                 long_term_memory: bool = False,
                 user_name: str = 'user',
                 knowledge_base: str = '',
                 tools_enabled: bool = True,
                 mcp_websearch: bool = False):
        """
        初始化XGO智能体
        
        Args:
            model_type: 机型 ('xgo-mini', 'xgo-lite', 'xgo-rider')
            api_key: 阿里云API密钥
            model_id: 模型ID (如 'qwen-max', 'qwen-plus')
            system_prompt: 自定义系统提示词
            long_term_memory: 是否启用长期记忆
            user_name: 用户标识
            knowledge_base: 知识库内容
            tools_enabled: 是否启用工具集
            mcp_websearch: 是否启用网络搜索MCP服务
        """
        self.model_type = model_type
        self.api_key = api_key
        self.model_id = model_id
        self.user_name = user_name
        
        # 加载机型描述
        self.description = self._load_description()
        
        # 构建完整系统提示词
        default_prompt = f"你是一个{model_type.upper()}机器人控制助手，可以控制机器人运动、显示、语音、视觉等功能。请根据用户需求灵活使用这些工具。"
        self.system_prompt = (system_prompt or default_prompt) + "\n\n" + self.description
        
        # 初始化组件（延迟到run时）
        self._agent = None
        self._toolkit = None
        self._long_term_memory = None
        self._tools_enabled = tools_enabled
        self._mcp_websearch = mcp_websearch
        self._knowledge_base = knowledge_base
        self._long_term_memory_enabled = long_term_memory
        
    def _load_description(self) -> str:
        """加载机型描述文本"""
        desc_file = os.path.join(
            os.path.dirname(__file__),
            'descriptions',
            f'{self.model_type.replace("xgo-", "")}.txt'
        )
        
        if os.path.exists(desc_file):
            with open(desc_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    async def _init_toolkit(self):
        """初始化工具包"""
        if not self._tools_enabled:
            return None
            
        toolkit = Toolkit()
        
        # 动态加载机型对应的工具模块
        try:
            module_name = self.model_type.replace('xgo-', '')
            tools_module = __import__(
                f'agents.tools.{module_name}',
                fromlist=['register_tools']
            )
            
            # 调用工具注册函数
            if hasattr(tools_module, 'register_tools'):
                tools_module.register_tools(toolkit, self.api_key)
                print(f"✓ {self.model_type.upper()}工具集加载成功")
        except ImportError as e:
            print(f"⚠️ 工具集加载失败: {e}")
        
        return toolkit
    
    async def _init_long_term_memory(self):
        """初始化长期记忆"""
        if not self._long_term_memory_enabled:
            return None
            
        try:
            import uuid
            import time
            
            # 生成唯一标识符，避免Qdrant存储冲突
            timestamp = int(time.time())
            instance_id = str(uuid.uuid4())[:8]
            agent_name = f"{self.model_type.upper()}Agent"
            
            memory = Mem0LongTermMemory(
                agent_name=agent_name,
                user_name=self.user_name,
                model=DashScopeChatModel(
                    model_name=self.model_id,
                    api_key=self.api_key,
                    stream=False,
                ),
                embedding_model=DashScopeTextEmbedding(
                    model_name="text-embedding-v2",
                    api_key=self.api_key,
                ),
                on_disk=True,
            )
            
            print(f"🧠 长期记忆初始化成功: {agent_name}")
            print(f"👤 用户标识: {self.user_name}")
            
            # 添加知识库
            if self._knowledge_base and self._knowledge_base.strip():
                await memory.record_to_memory(
                    thinking="这是用户的知识库，并非用户个人资料，只做资料参考",
                    content=[self._knowledge_base],
                    infer=False,
                    memory_type=None
                )
                print(f"✓ 知识库已加载")
            
            return memory
        except Exception as e:
            print(f"⚠️ 长期记忆初始化失败: {e}")
            return None
    
    async def _init_mcp(self):
        """初始化MCP服务"""
        if not self._mcp_websearch or not self._toolkit:
            return
            
        try:
            websearch_client = HttpStatelessClient(
                name="dashscope_websearch",
                transport="sse",
                sse_read_timeout=30,
                url="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            await self._toolkit.register_mcp_client(websearch_client)
            print("✓ WebSearch MCP服务已启用")
        except Exception as e:
            print(f"⚠️ MCP服务初始化失败: {e}")
    
    async def _ensure_initialized(self):
        """确保智能体已初始化"""
        if self._agent is not None:
            return
            
        # 初始化工具包
        self._toolkit = await self._init_toolkit()
        
        # 初始化长期记忆
        self._long_term_memory = await self._init_long_term_memory()
        
        # 初始化MCP
        await self._init_mcp()
        
        # 创建智能体
        agent_config = {
            'name': f"{self.model_type.upper()}Agent",
            'sys_prompt': self.system_prompt,
            'model': DashScopeChatModel(
                model_name=self.model_id,
                api_key=self.api_key,
                stream=False,
            ),
            'memory': InMemoryMemory(),
            'formatter': DashScopeChatFormatter(),
            'parallel_tool_calls': False,
            'print_hint_msg': True
        }
        
        if self._toolkit:
            agent_config['toolkit'] = self._toolkit
        
        if self._long_term_memory:
            agent_config['long_term_memory'] = self._long_term_memory
            agent_config['long_term_memory_mode'] = 'static_control'
        
        self._agent = ReActAgent(**agent_config)
        print(f"✓ {self.model_type.upper()}智能体初始化完成")
    
    def run(self, user_input: str) -> str:
        """
        同步运行接口（用户友好）
        
        Args:
            user_input: 用户输入
            
        Returns:
            智能体响应
        """
        return asyncio.run(self.run_async(user_input))
    
    async def run_async(self, user_input: str) -> str:
        """
        异步运行接口
        
        Args:
            user_input: 用户输入
            
        Returns:
            智能体响应
        """
        if not self.api_key:
            return "❌ 请设置API密钥"
        
        if not user_input or not user_input.strip():
            return f"{self.model_type.upper()}智能体已就绪"
        
        try:
            # 确保已初始化
            await self._ensure_initialized()
            
            # 执行对话
            response = await self._agent(
                Msg(self.user_name, user_input, "user")
            )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ 智能体运行异常:\n{error_details}")
            return f"❌ 执行失败: {str(e)}"
