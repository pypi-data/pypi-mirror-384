#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI-MCP Terminal - 多线程终端管理器 for MCP
"""

from setuptools import setup, find_packages
import os

# 读取README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-mcp-terminal",
    version="1.0.54",
    author="AI-MCP Contributors",
    author_email="",
    description="AI终端管理器 - 支持MCP协议的多线程终端系统，提供并发执行、智能调度、交互检测、Web界面等功能",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kanniganfan/ai-mcp-terminal",
    packages=find_packages(),
    package_data={
        "src": [
            "static/*.html",
            "static/*.js",
            "static/*.css",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-mcp-terminal=src.main:cli_main",
        ],
    },
    keywords="mcp terminal ai multi-thread concurrent shell management",
    project_urls={
        "Bug Reports": "https://github.com/kanniganfan/ai-mcp-terminal/issues",
        "Source": "https://github.com/kanniganfan/ai-mcp-terminal",
        "Documentation": "https://github.com/kanniganfan/ai-mcp-terminal#readme",
        "Changelog": "https://github.com/kanniganfan/ai-mcp-terminal/blob/main/CHANGELOG.md",
    },
)

