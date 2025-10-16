#!/usr/bin/env python3
"""Run MCP Standards Server"""
import asyncio
from mcp_standards.server import main

if __name__ == "__main__":
    asyncio.run(main())