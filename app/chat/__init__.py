import asyncio

from history import load_chat_history
from server import main1


# 启动聊天室
if __name__ == "__main__":
    load_chat_history()  # 加载聊天记录
    asyncio.run(main1())  # 启动异步事件循环
