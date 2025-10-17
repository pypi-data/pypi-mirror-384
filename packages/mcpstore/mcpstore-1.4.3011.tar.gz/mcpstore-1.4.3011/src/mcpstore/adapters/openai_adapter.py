# src/mcpstore/adapters/openai_adapter.py

from __future__ import annotations

import json
from typing import List, Dict, Any, TYPE_CHECKING

from .common import enhance_description, create_args_schema, build_sync_executor, build_async_executor

if TYPE_CHECKING:
    from ..core.context.base_context import MCPStoreContext
    from ..core.models.tool import ToolInfo


class OpenAIAdapter:
    """
    Adapter that converts MCPStore tools to OpenAI function calling format.
    Compatible with langchain-openai's bind_tools method and direct OpenAI API.
    """
    
    def __init__(self, context: 'MCPStoreContext'):
        self._context = context

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get all available MCPStore tools and convert them to OpenAI function format (synchronous version)."""
        return self._context._sync_helper.run_async(self.list_tools_async())

    async def list_tools_async(self) -> List[Dict[str, Any]]:
        """Get all available MCPStore tools and convert them to OpenAI function format (asynchronous version)."""
        mcp_tools_info = await self._context.list_tools_async()
        openai_tools = []
        
        for tool_info in mcp_tools_info:
            openai_tool = self._convert_to_openai_format(tool_info)
            openai_tools.append(openai_tool)
            
        return openai_tools

    def _convert_to_openai_format(self, tool_info: 'ToolInfo') -> Dict[str, Any]:
        """
        Convert MCPStore ToolInfo to OpenAI function calling format.
        
        OpenAI function format:
        {
            "type": "function",
            "function": {
                "name": "function_name",
                "description": "Function description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter description"
                        }
                    },
                    "required": ["param1"]
                }
            }
        }
        """
        # 增强描述信息
        enhanced_description = enhance_description(tool_info)
        
        # 获取输入参数schema
        input_schema = tool_info.inputSchema or {}
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # 转换参数schema到OpenAI格式
        openai_parameters = {
            "type": "object",
            "properties": {},
            "required": required
        }
        
        # 处理每个参数
        for param_name, param_info in properties.items():
            # OpenAI支持的类型映射
            openai_param = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
            
            # 处理枚举值
            if "enum" in param_info:
                openai_param["enum"] = param_info["enum"]
            
            # 处理默认值
            if "default" in param_info:
                openai_param["default"] = param_info["default"]
                
            # 处理数组类型的items
            if param_info.get("type") == "array" and "items" in param_info:
                openai_param["items"] = param_info["items"]
            
            # 处理对象类型的properties
            if param_info.get("type") == "object" and "properties" in param_info:
                openai_param["properties"] = param_info["properties"]
                if "required" in param_info:
                    openai_param["required"] = param_info["required"]
            
            openai_parameters["properties"][param_name] = openai_param
        
        # 如果没有参数，创建一个空的参数结构
        if not properties:
            openai_parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        # 构建OpenAI function格式
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool_info.name,
                "description": enhanced_description,
                "parameters": openai_parameters
            }
        }
        
        return openai_tool

    def get_callable_tools(self) -> List[Dict[str, Any]]:
        """
        Get tools with callable functions for direct execution.
        Returns a list of dicts with 'tool' (OpenAI format) and 'callable' (execution function).
        """
        return self._context._sync_helper.run_async(self.get_callable_tools_async())

    async def get_callable_tools_async(self) -> List[Dict[str, Any]]:
        """
        Get tools with callable functions for direct execution (async version).
        """
        mcp_tools_info = await self._context.list_tools_async()
        callable_tools = []
        
        for tool_info in mcp_tools_info:
            # 转换为OpenAI格式
            openai_tool = self._convert_to_openai_format(tool_info)
            
            # 创建参数schema
            args_schema = create_args_schema(tool_info)
            
            # 创建可调用函数
            sync_executor = build_sync_executor(self._context, tool_info.name, args_schema)
            async_executor = build_async_executor(self._context, tool_info.name, args_schema)
            
            callable_tools.append({
                "tool": openai_tool,
                "callable": sync_executor,
                "async_callable": async_executor,
                "name": tool_info.name,
                "schema": args_schema
            })
            
        return callable_tools

    def create_tool_registry(self) -> Dict[str, Any]:
        """
        Create a tool registry for easy tool execution by name.
        Returns a dict mapping tool names to their executors and metadata.
        """
        return self._context._sync_helper.run_async(self.create_tool_registry_async())

    async def create_tool_registry_async(self) -> Dict[str, Any]:
        """
        Create a tool registry for easy tool execution by name (async version).
        """
        callable_tools = await self.get_callable_tools_async()
        registry = {}
        
        for tool_data in callable_tools:
            tool_name = tool_data["name"]
            registry[tool_name] = {
                "openai_format": tool_data["tool"],
                "execute": tool_data["callable"],
                "execute_async": tool_data["async_callable"],
                "schema": tool_data["schema"]
            }
            
        return registry

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """
        Execute a tool call from OpenAI response format.
        
        Args:
            tool_call: OpenAI tool call format with 'name' and 'arguments'
            
        Returns:
            str: Tool execution result
        """
        return self._context._sync_helper.run_async(self.execute_tool_call_async(tool_call))

    async def execute_tool_call_async(self, tool_call: Dict[str, Any]) -> str:
        """
        Execute a tool call from OpenAI response format (async version).
        """
        try:
            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
            arguments = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})
            
            if not tool_name:
                raise ValueError("Tool name not found in tool_call")
            
            # 如果arguments是字符串，尝试解析为JSON
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            
            # 调用工具
            result = await self._context.call_tool_async(tool_name, arguments)
            
            # 提取实际结果
            if hasattr(result, 'result') and result.result is not None:
                actual_result = result.result
            elif hasattr(result, 'success') and result.success:
                actual_result = getattr(result, 'data', str(result))
            else:
                actual_result = str(result)
            
            # 格式化输出
            if isinstance(actual_result, (dict, list)):
                return json.dumps(actual_result, ensure_ascii=False)
            return str(actual_result)
            
        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            return error_msg

    def batch_execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """
        Execute multiple tool calls in batch.
        
        Args:
            tool_calls: List of OpenAI tool call formats
            
        Returns:
            List[str]: List of tool execution results
        """
        return self._context._sync_helper.run_async(self.batch_execute_tool_calls_async(tool_calls))

    async def batch_execute_tool_calls_async(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """
        Execute multiple tool calls in batch (async version).
        """
        results = []
        for tool_call in tool_calls:
            try:
                result = await self.execute_tool_call_async(tool_call)
                results.append(result)
            except Exception as e:
                results.append(f"Error executing tool call: {str(e)}")
        return results
