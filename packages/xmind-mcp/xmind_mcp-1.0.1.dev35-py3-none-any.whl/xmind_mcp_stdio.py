#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind MCP (stdio 版本)
无需本地拉代码或部署服务器，使用标准输入输出实现 MCP 通讯。
兼容 Trae 的 MCP 客户端（command/args 模式）。

支持工具：
- read_xmind_file(filepath)
- create_mind_map(title, topics_json [, output_path])
- analyze_mind_map(filepath)
- convert_to_xmind(source_filepath [, output_filepath])
- list_xmind_files(directory='.', recursive=True)
- ai_generate_topics(context [, max_topics, creativity_level])
"""

import sys
import json
import traceback
from typing import Any, Dict, Optional

from xmind_core_engine import (
    read_xmind_file,
    create_mind_map,
    analyze_mind_map,
    convert_to_xmind,
    list_xmind_files,
    get_engine,
)
from xmind_ai_extensions import XMindAIExtensions

# 简单的 Content-Length 帧解析/发送（兼容 MCP stdio 传输）
# 参考 LSP/MCP 约定：消息以 HTTP 风格头部开头，至少包含 Content-Length

class StdioRPC:
    def __init__(self):
        self.stdin = sys.stdin.buffer
        self.stdout = sys.stdout.buffer
        self.ai = XMindAIExtensions()  # openai 可选

    def _read_headers(self) -> Optional[Dict[str, str]]:
        headers = {}
        # 逐行读取直到空行（\r\n 或 \n）
        while True:
            line = self.stdin.readline()
            if not line:
                return None
            try:
                s = line.decode('utf-8')
            except Exception:
                s = line.decode('latin-1')
            s = s.strip('\r\n')
            if s == '':
                break
            if ':' in s:
                k, v = s.split(':', 1)
                headers[k.strip().lower()] = v.strip()
        return headers

    def read_message(self) -> Optional[Dict[str, Any]]:
        # 尝试 Content-Length 解析
        headers = self._read_headers()
        if headers is None:
            return None
        length_str = headers.get('content-length')
        if length_str:
            try:
                length = int(length_str)
                body = self.stdin.read(length)
                if not body:
                    return None
                return json.loads(body.decode('utf-8'))
            except Exception:
                # 解析失败时返回 None
                return None
        else:
            # 兼容行分隔 JSON（没有 Content-Length 时）
            line = self.stdin.readline()
            if not line:
                return None
            try:
                return json.loads(line.decode('utf-8'))
            except Exception:
                return None

    def send_message(self, payload: Dict[str, Any]):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        header = f"Content-Length: {len(data)}\r\n\r\n".encode('utf-8')
        self.stdout.write(header)
        self.stdout.write(data)
        self.stdout.flush()

    async def _ai_generate_topics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        context = args.get('context') or args.get('topic') or ''
        max_topics = int(args.get('max_topics') or args.get('count') or 10)
        creativity = float(args.get('creativity_level') or 0.7)
        try:
            topics = await self.ai.generate_topics(context=context, max_topics=max_topics, creativity_level=creativity)
            # 转成可读文本
            lines = []
            for t in topics:
                lines.append(f"- {t.title}")
                for st in (t.subtopics or []):
                    lines.append(f"  - {st.title}")
            text = "\n".join(lines) if lines else "未生成主题"
            return {
                "content": [{"type": "text", "text": text}],
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": f"AI生成失败: {e}"}]}

    def _tools_list(self, msg_id: Any) -> Dict[str, Any]:
        # 与现有引擎工具保持一致字段
        tools = [
            {
                "name": "read_xmind_file",
                "description": "读取XMind文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "XMind文件路径"}
                    },
                    "required": ["filepath"],
                },
            },
            {
                "name": "create_mind_map",
                "description": "创建新的思维导图",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "思维导图标题"},
                        "topics_json": {"type": "string", "description": "主题结构的JSON字符串"},
                        "output_path": {"type": "string", "description": "输出路径(可选)"},
                    },
                    "required": ["title", "topics_json"],
                },
            },
            {
                "name": "analyze_mind_map",
                "description": "分析思维导图结构",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "XMind文件路径"}
                    },
                    "required": ["filepath"],
                },
            },
            {
                "name": "convert_to_xmind",
                "description": "转换文件为XMind格式",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_filepath": {"type": "string", "description": "源文件路径"},
                        "output_filepath": {"type": "string", "description": "输出文件路径(可选)"},
                    },
                    "required": ["source_filepath"],
                },
            },
            {
                "name": "list_xmind_files",
                "description": "列出XMind文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录(默认当前)"},
                        "recursive": {"type": "boolean", "description": "是否递归"},
                    },
                },
            },
            {
                "name": "ai_generate_topics",
                "description": "AI生成思维导图主题",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "主题上下文"},
                        "max_topics": {"type": "integer", "description": "数量(默认10)"},
                        "creativity_level": {"type": "number", "description": "创造性(0-1)"},
                    },
                },
            },
        ]
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tools},
        }

    def _initialize(self, msg_id: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": False},
                    "logging": {},
                },
                "serverInfo": {
                    "name": "xmind-mcp-stdio",
                    "version": "1.0.0",
                    "description": "XMind MCP stdio server (no web server)",
                },
            },
        }

    def _ok_text(self, msg_id: Any, text: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"content": [{"type": "text", "text": text}]},
        }

    def _error(self, msg_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        err = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
        if data is not None:
            err["error"]["data"] = data
        return err

    def _call_tool(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get('name')
        args = params.get('arguments') or {}
        try:
            if name == 'read_xmind_file':
                filepath = args.get('filepath') or args.get('file_path')
                result = read_xmind_file(filepath)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
            elif name == 'create_mind_map':
                title = args.get('title')
                topics_json = args.get('topics_json') or json.dumps(args.get('topics') or [])
                output_path = args.get('output_path')
                result = create_mind_map(title, topics_json) if not output_path else get_engine().create_mind_map(title, topics_json, output_path)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": result.get('message') or json.dumps(result, ensure_ascii=False)}]}}
            elif name == 'analyze_mind_map':
                filepath = args.get('filepath') or args.get('file_path')
                result = analyze_mind_map(filepath)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
            elif name == 'convert_to_xmind':
                src = args.get('source_filepath') or args.get('filepath')
                out = args.get('output_filepath')
                result = convert_to_xmind(src, out)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": result.get('message') or json.dumps(result, ensure_ascii=False)}]}}
            elif name == 'list_xmind_files':
                directory = args.get('directory') or '.'
                recursive = bool(args.get('recursive', True))
                result = list_xmind_files(directory, recursive)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
            elif name == 'ai_generate_topics':
                # 需要异步调用
                import asyncio
                result = asyncio.run(self._ai_generate_topics(args))
                return {"jsonrpc": "2.0", "id": msg_id, "result": result}
            else:
                return self._error(msg_id, -32601, f"Unknown tool: {name}")
        except Exception as e:
            # 捕获异常并返回错误
            return self._error(msg_id, -32603, f"Tool call failed: {e}", traceback.format_exc())

    def serve(self):
        # 主循环：读取请求并发送响应
        while True:
            msg = self.read_message()
            if msg is None:
                # 输入关闭或解析失败，退出
                break
            jsonrpc = msg.get('jsonrpc')
            msg_id = msg.get('id')
            method = msg.get('method')
            params = msg.get('params') or {}

            if jsonrpc != '2.0':
                self.send_message(self._error(msg_id, -32600, "Invalid Request: jsonrpc must be '2.0'"))
                continue

            if method == 'initialize':
                self.send_message(self._initialize(msg_id))
            elif method == 'tools/list':
                self.send_message(self._tools_list(msg_id))
            elif method == 'tools/call':
                self.send_message(self._call_tool(msg_id, params))
            elif method == 'ping':
                self.send_message({"jsonrpc": "2.0", "id": msg_id, "result": {"pong": True}})
            else:
                self.send_message(self._error(msg_id, -32601, f"Method not found: {method}"))


def main():
    server = StdioRPC()
    server.serve()


if __name__ == '__main__':
    main()