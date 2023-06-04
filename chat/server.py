import asyncio
import urllib
from urllib.parse import urlparse

import websockets.exceptions

from app.chat.chat import send_private_message, create_private_message, my_send, handle_message
from app.chat.chatconfig import connections, SERVER_PORT
from app.chat.connection import handle_new_connection, handle_connection_closed, handle_connection


# 创建异步事件循环并启动
async def main1():
    async with websockets.serve(handle_connection, 'SERVER_ADDRESS', SERVER_PORT):
        while True:
            # await receive_system_message()
            await asyncio.sleep(0.5)  # 控制接收消息的频率


async def start_server():
    # 创建WebSocket服务器
    server = await websockets.serve(handle_connection, "SERVER_ADDRESS", SERVER_PORT)
    print("WebSocket server started.")
    # await receive_system_message()  # 接收系统消息
    # 接收连接请求并处理连接
    async for client_websocket, client_address in server:
        # 处理新连接
        await handle_new_connection(client_websocket, client_address)
        # 接收和处理消息
        try:
            async for message in client_websocket:
                await handle_message(message, connections[client_websocket]["id"])
        except websockets.exceptions.ConnectionClosed:
            # 连接关闭时的处理
            await handle_connection_closed(client_websocket)
        path = client_websocket.path
        # 根据路径调用相应的处理函数
        try:
            if path == "/chat/send":
                # 获取 WebSocket 连接的请求对象
                request = client_websocket.request
                # 解析客户端的请求参数（地址传参
                query_params = urllib.parse.parse_qs(request.path)
                chat_connection_id = query_params.get('chat_connection_id', [''])[0]
                send_id = query_params.get('send_id', [''])[0]
                message = query_params.get('message', [''])[0]
                await send_private_message(chat_connection_id, send_id, message)
            elif path == "/chat/create":
                # 获取 WebSocket 连接的请求对象
                request = client_websocket.request
                # 解析客户端的请求参数（地址传参
                query_params = urllib.parse.parse_qs(request.path)
                my_id = query_params.get('my_id', [''])[0]
                friend_id = query_params.get('friend_id', [''])[0]
                await create_private_message(my_id, friend_id)
            elif path == "/chat/system":
                # 获取 WebSocket 连接的请求对象
                request = client_websocket.request
                # 解析客户端的请求参数（地址传参
                query_params = urllib.parse.parse_qs(request.path)
                message = query_params.get('message', [''])[0]
                chat_id = query_params.get('chat_id', [''])[0]
                await my_send(chat_id, message)
            # await keep_handle_message(client_websocket)
            # elif path == "/chat/delete":
            # await handle_delete_message(client_websocket, client_websocket.path)
            # elif path == "/notification":
            # await show_notification()
        except:
            print("Invalid path")
