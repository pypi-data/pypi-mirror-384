#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : langchain_agent.py

from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from .pmp.prompt_generator import PromptGenerator, TemplateName


class StataAgent:
    # Set default MCP server
    mcp_client = MultiServerMCPClient(
        {
            "stata-mcp": {
                "command": "uv",
                "args": [
                    "--directory",
                    "/Users/sepinetam/Documents/Github/stata-mcp",
                    "run",
                    'main.py'
                ],
                "transport": "stdio",
            }
        }
    )

    def __init__(self,
                 model: str = "gpt-5",
                 work_dir: str = None):
        """
        Please set your OPENAI_API_KEY and OPENAI_BASE_URL (OPENAI_API_BASE) in your environment.

        Although OpenAI's ChatGPT is great enough, I recommend to use DeepSeek as its ability and score.
        If you want to know more about it, visit https://www.statamcp.com/reports to find more information.
        """
        # Set model also could be changed
        self.model = init_chat_model(model=model, model_provider="openai")
        self.work_dir = work_dir

        # Manage prompt
        self.prompt_generator = PromptGenerator(
            template_name=TemplateName.ReAct,
            ROOT=self.work_dir,
            agent_provider="langchain"
        )
        self.instructions = self.prompt_generator.instructions(
            root=self.work_dir
        )

    async def set_agent(self):
        tools = await self.mcp_client.get_tools()
        agent = create_react_agent(self.model, tools, prompt=self.instructions)
        return agent

    async def run(self, data_source: str, task: str, is_display: bool = True):
        message = self.prompt_generator.tasks(
            datas=data_source,
            aims=task,
            root=self.work_dir
        )

        task_message = {"messages": message}
        agent = await self.set_agent()
        result = await agent.ainvoke(
            task_message,
            config={"recursion_limit": 50}
        )
        if is_display:
            print(result)
        return result
