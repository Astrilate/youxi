import base64
import datetime
import json

from app.chat.chatconfig import clients, chat_history, private_chats
from app.chat.history import save_chat_history


# 生成消息ID
def generate_message_id():
    return str(datetime.datetime.now().timestamp())


# 定义发送函数
async def my_send(chat_id, message):
    for client in clients.values():
        if client == chat_id:
            await client.send(json.dumps(message))


# 处理收到的消息
# async def handle_message(message, client_id):
async def handle_message(message, client_id):
    # async def handle_message(msg_type, content, client_id):
    # 解析收到的消息
    try:
        data = json.loads(message)
        chat_id = data["chatId"]  # 对象id
        sender_type = data["senderType"]  # 0对方，1自己，2系统
        msg_type = data["msgType"]  # 0文本，1图片，2json
        content = data["content"]
        time = data["time"]
    except json.JSONDecodeError:
        # 消息解析错误，返回错误信息给指定的客户端
        error_message = {
            "error": "Invalid JSON format"
        }
        await my_send(client_id, json.dumps(error_message))
        return
    except KeyError as e:
        # 缺少必要的键错误，返回错误信息给指定的客户端
        error_message = {
            "error": f"Missing key: {str(e)}"
        }
        # await client_websocket.send(json.dumps(error_message))
        await my_send(client_id, error_message)
        return

    if msg_type == 0:
        # 处理文本消息
        # sender = client_id
        # timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 创建文本消息
        text_message = {
            "chatId": chat_id,
            "senderType": sender_type,
            "msgType": msg_type,
            "content": content,
            "time": time
        }
        message_record = {"message_id": message_id, "text_message": text_message}

        # 保存到聊天记录
        chat_history.append(message_record)
        save_chat_history()

        # 发消息
        # for client in clients.values():
        # if client == chat_id:
        # await client.send(json.dumps(text_message))
        await my_send(chat_id, text_message)

    elif msg_type == 1:
        # 处理图片消息
        # sender = client_id
        # timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 解码图片数据
        image_data = base64.b64decode(content)

        # 生成图片文件名
        image_filename = f"image_{message_id}.png"

        # 保存图片文件
        with open(image_filename, "wb") as file:
            file.write(image_data)

        # 创建图片消息
        image_message = {
            "chatId": chat_id,
            "senderType": sender_type,
            "msgType": msg_type,
            "content": image_filename,
            "time": time
        }
        im_message_record = {"message_id": message_id, "image_message": image_message}

        # 保存到聊天记录
        chat_history.append(im_message_record)
        save_chat_history()

        # 发消息
        # for client in clients.values():
        # if client == chat_id:
        # await client.send(json.dumps(image_message))
        await my_send(chat_id, image_message)


# 创建私聊消息
# def create_private_message(message_id, sender, recipient, content):
def create_private_message(my_id, friend_id):
    timestamp = datetime.datetime.now().timestamp()
    dict_name = f"connection{timestamp}"
    private_chats[dict_name] = {"my_id": my_id, "friend_id": friend_id}


# 发送私聊消息
async def send_private_message(send_id, chat_connection_id, message):
    # 区分发送者和接受者
    try:
        # 检查私聊连接是否存在
        if "connection" + str(chat_connection_id) not in private_chats:
            raise KeyError(f"Chat '{chat_connection_id}' not found.")

        if send_id == private_chats["connection" + str(chat_connection_id)]["my_id"]:
            recipient = private_chats["connection" + str(chat_connection_id)]["friend_id"]
            sender = private_chats["connection" + str(chat_connection_id)]["my_id"]
        else:
            recipient = private_chats["connection" + str(chat_connection_id)]["my_id"]
            sender = private_chats["connection" + str(chat_connection_id)]["friend_id"]
        # recipient_websocket = connected_users[recipient]
        # 发送私聊消息给接收者
        await recipient.send(json.dumps(message))
        # 发送私聊消息给发送者
        sender_websocket = sender
        await sender_websocket.send(json.dumps(message))

    except KeyError as e:
        error = f"Error: {str(e)}"
        print(error)
        error_message = make_message(send_id, 1, 2, error, datetime.datetime.now().timestamp())
        await my_send(send_id, error_message)

    except Exception as e:
        error = f"Error occurred while sending private message: {str(e)}"
        print(error)
        error_message = make_message(send_id, 1, 2, error, datetime.datetime.now().timestamp())
        await my_send(send_id, error_message)


def make_message(chat_id, sender_type, msg_type, content, time):
    f_message = {
        "chatId": chat_id,  # 对象id
        "senderType": sender_type,  # 0对方，1自己，2系统
        "msgType": msg_type,  # 0文本，1图片，2json
        "content": content,
        "time": time
    }
    return f_message
