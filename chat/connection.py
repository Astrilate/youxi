import datetime
import json
import urllib
import uuid
from urllib.parse import urlparse, parse_qs
import websockets
import websockets.exceptions

from app.chat.chat import my_send, handle_message, make_message
from app.chat.chatconfig import connected_users, connections, error_history, clients
from app.chat.history import save_error_history


# 生成客户端ID（测试用，到时候要换成正儿八紧的消息ID）
def generate_client_id():
    return str(uuid.uuid4())


# ws://server_address:port/chat?client_id=12345 举个例子
async def get_client_info(client_websocket):
    # 获取 WebSocket 连接的请求对象
    request = client_websocket.request
    # 获取客户端的远程地址（IP地址）
    remote_address = client_websocket.remote_address[0]
    # 解析客户端的请求参数（地址传参）
    query_params = urllib.parse.parse_qs(request.path)
    # 获取客户端传递的参数
    client_id = query_params.get('client_id', [''])[0]
    # 构造客户端信息字典
    client_info = {
        'remote_address': remote_address,
        'client_id': client_id
    }
    return client_info


async def get_chat_message(client_websocket):
    # 获取 WebSocket 连接的请求对象
    request = client_websocket.request

    # 获取客户端的远程地址（IP地址）
    remote_address = client_websocket.remote_address[0]

    # 解析客户端的请求参数（JSON 传参）
    query_string = request.query_string.decode('utf-8')
    query_params = json.loads(query_string)

    # 获取客户端传递的参数
    message = query_params.get('MsgRecord', '')

    return message


# 创建新连接
async def handle_new_connection(client_websocket, client_address):
    try:
        # 执行与新连接相关的初始化操作 分配一个唯一的客户端ID（测试用）
        # client_id = generate_client_id()
        welcome_message = "Welcome！"
        await client_websocket.send(welcome_message)
        # 获取客户端信息
        client_info = await get_client_info(client_websocket)
        # 添加到连接列表
        connections[client_websocket] = client_info
        # 发送连接成功的系统通知
        connection_notice = f"New connection from {client_address}"
        client_id = connections[client_websocket]["client_id"]
        connection_notice_message = make_message(client_id, 2, 0, connection_notice,
                                                 datetime.datetime.now().timestamp())
        await my_send(client_id, connection_notice)
        print(connection_notice)
    except websockets.exceptions.ConnectionClosedError as e:
        # 连接关闭异常处理
        print("连接关闭：", e)
        # 保存到错误日志
        error_history.append(e)
        save_error_history()
    except websockets.exceptions.WebSocketException as e:
        # WebSocket异常处理
        print("WebSocket异常：", e)
        # 保存到错误日志
        error_history.append(e)
        save_error_history()
    except Exception as e:
        # 处理连接初始化过程中的异常
        print(f"Error handling new connection from {client_address}: {str(e)}")
        await client_websocket.close()
        # 保存到错误日志
        error_history.append(e)
        save_error_history()


# 处理WebSocket连接，最基本的那个函数
async def handle_connection(websocket, path):
    # 接收客户端的连接请求
    client_id = await websocket.recv(1024)
    # 不知道这里要不要填个数字来限制连接大小
    print(f"New client connected: {client_id}")
    # 提取WebSocket服务器的URL地址
    # server_url = urllib.parse.urlparse(path)
    # print("WebSocket server URL:", server_url.geturl())
    # 添加客户端到字典中
    clients[client_id] = websocket
    # 发送欢迎消息给客户端
    welcome_message = {
        "chatId": websocket,
        "senderType": 2,
        "msgType": 0,
        "content": "Welcome,Dear User!",
        "time": datetime.datetime.now().timestamp()
    }
    await websocket.send(json.dumps(welcome_message))
    # 处理客户端发送的消息
    try:
        async for message in websocket:
            await handle_message(message, connections[websocket]["id"])
    except websockets.exceptions.ConnectionClosedOK:
        # 连接关闭
        await handle_connection_closed(websocket)
    except websockets.exceptions.ConnectionClosed:
        # 连接关闭时的处理
        await handle_connection_closed(websocket)
    finally:
        # 从字典中删除客户端
        del clients[client_id]
        print(f"Client disconnected: {client_id}")


async def handle_connection_closed(client_websocket):
    # 获取客户端ID和地址
    client_id = connections[client_websocket]["id"]
    client_address = connections[client_websocket]["address"]

    # 从连接列表和已连接用户字典中删除客户端
    del connections[client_websocket]
    if client_id in connected_users:
        del connected_users[client_id]
    disconnect_message = {
        "chatId": client_id,
        "senderType": 1,
        "msgType": 0,
        "content": f"Client {client_id} has disconnected.",
        "time": datetime.datetime.now().timestamp()
    }
    await my_send(client_id, json.dumps(disconnect_message))
    # 输出连接关闭的消息
    print(f"Client {client_id} disconnected: {client_address}")
    # 关闭 WebSocket 连接
    await client_websocket.close()
