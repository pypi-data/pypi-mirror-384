"""
CAN 设备操作工具函数
"""

import requests
import logging
import threading
from threading import Event
import paho.mqtt.client as mqtt
import ast
import time
import re
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def send_frame_to_can(channel_id: str, frame_id: int, signals: dict, duration: int, interval: int, ip: str = "127.0.0.1") -> str:
    """
    发送 CAN 信号并返回结果
    
    Args:
        channel_id: CAN 通道id
        frame_id: 信号帧id（整数）
        signals: 信号字典，格式：{"signal_name": value}
        duration: 信号发送持续时间
        interval: 信号发送间隔时间
        ip: can server ip , 默认 script server 和 CAN server 在一个地方
        
    Returns:
        str: 命令执行结果
    """
    url = "http://" + ip + ":8083/channels/send"

    request_payload = {
        "channel_id": channel_id,
        "frame_id": frame_id,
        "signals": signals,
    }
    for i in range(duration//interval):
        try:
            response = requests.post(url, json=request_payload, timeout=5)
            response.raise_for_status()
            # print("send_frame_to_channel send frame,", response.json())
            status = response.json()
            if status.get("status") == "success":
                time.sleep(interval/1000)
                continue
            return f"{channel_id} send frame failed"
        except requests.exceptions.RequestException as e:
            return f"请求失败: {str(e)}"
        except ValueError:
            return "响应内容不是有效的 JSON"

    time.sleep(1)
    return "CAN命令执行成功"

PORT = 1883
QOS = 1
CLIENT_ID = "subscriber_py"
RECONNECT_DELAY = 1
MQTT_HOST = "10.211.55.2" # MQTT代理服务器的地址
MQTT_PREFIX = "nodeid/etscan/signals"  # 替换为实际节点编号

def get_signal(channel_list: List[str], file_path: str, stop_event: Event, ip: str = "127.0.0.1"):
    """
    MQTT订阅线程函数
    
    Args:
        channel_list: CAN 通道id列表
        file_path: 信号保存文件路径
        stop_event: 停止获取 CAN 信号的事件
        ip: can server ip , 默认 script server 和 CAN server 在一个地方
        
    Returns:
        None
    """
    connected_event = threading.Event()

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"成功连接到 {ip}:{PORT}")
            connected_event.set()
            
            # =====================添加===========================

            # 创建文件目录（如果不存在）
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 创建空文件，确保文件存在
            with open(file_path, 'w') as f:
                f.write('')  # 创建空文件
            logger.info(f"✅ 已创建CAN采集文件: {file_path}")
            
            # =====================添加===========================


            # 订阅所有指定的频道
            for channel_id in channel_list:
                topic = f"{MQTT_PREFIX}/{channel_id}"
                result, mid = client.subscribe(topic, qos=QOS)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"已订阅主题: {topic}")
                else:
                    logger.error(f"订阅失败: {topic}, 错误码: {result}")
        else:
            logger.error(f"连接失败，错误码: {rc}")
            connected_event.clear() 

    def on_message(client, userdata, msg):
        data = msg.payload.decode()
        with open(file_path, 'a') as f:
            # 使用JSON格式存储，每行一条记录
            f.write(data + '\n')

    def on_disconnect(client, userdata, rc, properties=None):
        logger.warning(f"与MQTT代理的连接已断开，原因: {rc}")
        connected_event.clear()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        logger.info(f"尝试连接到 {ip}:{PORT}...")
        client.connect(ip, PORT)
        
        # 启动非阻塞网络循环
        client.loop_start()

        # 等待初始连接成功或超时
        if connected_event.wait(timeout=1.0):
            logger.info("初始连接成功")
        else:
            logger.warning("初始连接超时，等待重连...")
        
        # 等待停止事件或连接失败
        while not stop_event.is_set():
            if not connected_event.is_set():
                # 检查是否客户端已断开连接
                if not client.is_connected():
                    # 尝试重连
                    try:
                        logger.info("尝试重新连接...")
                        client.reconnect()
                        # 等待重连结果
                        connected_event.wait(timeout=RECONNECT_DELAY)
                    except Exception as e:
                        logger.error(f"重连失败: {str(e)}")
                else:
                    # 如果客户端连接但回调未触发，等待重连
                    connected_event.wait(timeout=RECONNECT_DELAY)
            
            # 降低CPU使用率
            time.sleep(0.5)
        
    except ConnectionRefusedError:
        logger.error(f"无法连接到 {ip}:{PORT}，请检查：")
        logger.error("1. 服务器IP和端口是否正确")
        logger.error("2. 防火墙是否开放端口")
        logger.error("3. MQTT服务是否正常运行")
    except Exception as e:
        logger.error(f"发生未知错误: {str(e)}")
    finally:
        # 清理资源
        logger.info("正在关闭MQTT连接...")
        client.loop_stop()
        client.disconnect()
        logger.info("MQTT连接已关闭")

def check_data(file_path, rules):
    with open(file_path, 'r', encoding='gbk') as file:
        for line in file:
            try:
                # 将每行数据解析为字典
                data_all = ast.literal_eval(line.strip())
                data = data_all["signals"]
                # 检查当前行是否满足所有规则
                if all(_check_rule(data, rule) for rule in rules):
                    return True
            except (ValueError, SyntaxError):
                # 如果解析失败，跳过该行
                continue
    return False


def _check_rule(data, rule):
    target = rule['title']
    if target not in data:
        return False  # 如果字段不存在，直接返回 False
    # 获取字段的值
    value = data[target]
    # 检查是否满足所有条件
    for condition in rule['values']:
        relation = condition['relation']
        expected_value = condition['value']
        if not _compare(value, relation, int(expected_value)):
            return False
    return True


def _compare(value, relation, expected_value):
    if relation == '>':
        return value > expected_value
    elif relation == '<':
        return value < expected_value
    elif relation == '=':
        return value == expected_value
    elif relation == '>=':
        return value >= expected_value
    elif relation == '<=':
        return value <= expected_value
    elif relation == '!=':
        return value != expected_value
    else:
        raise ValueError(f"Unsupported relation: {relation}")


def extract_title_and_values(input_str):
    # 将输入字符串解析为 Python 对象（列表）
    data = ast.literal_eval(input_str)
    result = [{'title': item['title'], 'values': item['values']} for item in data]
    return result


def judge_can(can_file_url, signal_str):
    rules = extract_title_and_values(signal_str)
    # save_path = can_file_url[:-8] + "result.txt"
    can_judge_result = True
    for rule in rules:
        temp_rule_list = []
        temp_rule_list.append(rule)
        can_judge_result = check_data(can_file_url, temp_rule_list)
        if can_judge_result == False:
            break
    return can_judge_result

def evaluate_judge_expression(judge_list, expression):
    # Step 1: 创建ID到is_pass的映射字典
    id_to_pass = {item['id']: item['is_pass'] for item in judge_list}
    
    # Step 2: 安全地将ID替换为布尔值
    # 使用正则匹配所有 [xxx] 格式的ID
    def replace_id(match):
        id_str = match.group(0)
        if id_str in id_to_pass:
            return str(id_to_pass[id_str])  # 返回布尔值对应的字符串
        else:
            logger.error(f"Unknown ID in expression: {id_str}")
    if expression is None or expression == "":
        expression = ""
        for item in judge_list:
            if expression != "":
                expression = expression + '&&'
            expression = expression + item['id']

    # 替换表达式中的所有ID为对应的布尔值字符串
    replaced_expr = re.sub(r'\[.*?\]', replace_id, expression)
    
    # Step 3: 转换逻辑运算符 && → and，|| → or
    # 保留空格处理，避免粘连
    normalized_expr = replaced_expr.replace('&&', ' and ').replace('||', ' or ')
    
    # Step 4: 安全地评估表达式
    try:
        # 直接评估布尔逻辑表达式
        return eval(normalized_expr, {}, {})
    except Exception as e:
        logger.error(f"Error evaluating expression: {e}")

def judge_signal(target_signal: List[str], file_path: str):

    judge_list = []
    for signal in target_signal:
        signal_list = []
        a = {
            "title": signal.get("title"),
            "values": signal.get("values")
        }
        signal_list.append(a)
        is_pass = judge_can(file_path, str(signal_list))
        judge = {
            "id": signal.get("logic_id"),
            "is_pass": is_pass,
        }
        judge_list.append(judge)
    logger.info(f" can 信号判断: {judge_list=}")
    return judge_list

# def judge_signal(target_signal: List[str], expression: str, file_path: str):

#     judge_list = []
#     for signal in target_signal:
#         signal_list = []
#         a = {
#             "title": signal.get("title"),
#             "values": signal.get("values")
#         }
#         signal_list.append(a)
#         is_pass = judge_can(file_path, str(signal_list))
#         judge = {
#             "id": signal.get("logic_id"),
#             "is_pass": is_pass,
#         }
#         judge_list.append(judge)
#     logger.info(f" can 信号判断: {judge_list=}, {expression=}")
#     is_pass = evaluate_judge_expression(judge_list, expression)
#     return is_pass

