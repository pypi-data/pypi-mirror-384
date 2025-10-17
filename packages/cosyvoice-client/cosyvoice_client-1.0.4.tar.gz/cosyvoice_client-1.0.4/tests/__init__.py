"""测试包初始化"""

import asyncio
from collections.abc import Generator

import pytest

# 配置 pytest 异步支持
pytestmark = pytest.mark.asyncio
