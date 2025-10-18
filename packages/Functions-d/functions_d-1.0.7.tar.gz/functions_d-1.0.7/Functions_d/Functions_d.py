# -*- coding:utf-8 -*-
import datetime
import inspect
import json
import logging
import os
import shutil
import time
import urllib.request
import traceback
import pandas as pd
import WeComMsg
import xlwings as xw
import yagmail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import HiveClients
import HiveClient
from PIL import ImageGrab, Image
from bs4 import BeautifulSoup
import re
import xlsxwriter
import numpy as np
# 新增的库（Edge浏览器需要）
from pypinyin import lazy_pinyin
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import platform
import requests


class DataProcessingAndMessaging:
    def __init__(self):
        # -------------------------- 1. 主类日志初始化 --------------------------
                # -------------------------- 1. 主类日志初始化 --------------------------
        # 获取调用者的堆栈信息（主类日志关联调用脚本）
        caller_frame = inspect.stack()[1]
        caller_filename = caller_frame.filename
        # 修复：处理中文文件名/路径的编码问题（确保日志文件名正确）
        caller_filename = os.path.abspath(caller_filename)
        log_file = os.path.splitext(os.path.basename(caller_filename))[0] + ".log"

        # 初始化主类日志记录器
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 文件处理器（保存到日志文件）- 修复：显式指定UTF-8编码
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            # 控制台处理器（方便开发调试）- 修复：显式指定UTF-8编码（部分终端需配置）
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        self.logger.info("初始化 DataProcessingAndMessaging 类")

        # -------------------------- 2. 主类核心参数初始化 --------------------------
        self.start_time = None
        self.current_script_name = None
        self.log_filename = None
        self.current_script_names = None
        self.current_path = None
        self.path = None

        # 企业微信消息发送参数
        self.corpid = "wxd4e113eb4c0136b9"
        self.corpsecret = "PMfPOv2Qqq0iXZAdWHF7WdaW4kkWUZcwyGE4NZtve3k"
        self.agentid = "1000026"

        # -------------------------- 3. 企业微信文档功能初始化（原WechatWorkDocs） --------------------------
        # 企业微信文档参数（独立配置）
        self.WECHAT_DOC_CORP_ID = "wxd4e113eb4c0136b9"
        self.WECHAT_DOC_SECRET = "PMfPOv2Qqq0iXZAdWHF7WdaW4kkWUZcwyGE4NZtve3k"
        self.WECHAT_DOC_SPACE_ID = None  # 空间ID，根目录可留空
        self.WECHAT_DOC_LOG_FILE = "docs_operation_log.txt"  # 文档功能独立日志文件
        self.wechat_doc_access_token = None

        # 初始化文档功能的独立日志（确保日志文件存在）
        if not os.path.exists(self.WECHAT_DOC_LOG_FILE):
            with open(self.WECHAT_DOC_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(f"文档操作日志 - 开始于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 预获取文档access_token（失败不中断主类初始化，后续操作自动重试）
        try:
            self.wechat_doc_access_token = self._wechat_doc_get_access_token()
        except Exception as e:
            self.logger.warning(f"企业微信文档access_token初始化失败（后续操作会自动重试）：{str(e)}")



    def init_edge_driver(self, headless=True):
        """初始化Edge驱动（彻底移除architecture参数，用环境变量指定32位）"""
        # 1. 强制指定32位驱动（适配旧版本webdriver-manager）
        os.environ['WDM_ARCH'] = 'x86'  # 关键：通过环境变量指定32位，无需architecture参数

        # 2. 创建Edge浏览器选项
        edge_options = Options()
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--ignore-certificate-errors')

        if headless:
            edge_options.add_argument('--headless=new')
            edge_options.add_argument('--window-size=1920,1080')

        # 3. 初始化驱动（不传入任何architecture参数）
        service = Service(EdgeChromiumDriverManager().install())  # 此处必须移除architecture参数

        # 4. 启动浏览器
        driver = webdriver.Edge(service=service, options=edge_options)
        self.logger.info("Edge浏览器初始化成功（适配旧版本webdriver-manager）")
        return driver

    def Start_Get_filepath_and_filename(self):
        self.start_time = time.time()
        # 获取调用者的堆栈信息
        caller_frame = inspect.stack()[1]
        # 获取调用者的文件名
        self.current_script_name = caller_frame.filename
        self.log_filename = os.path.splitext(self.current_script_name)[0] + ".log"
        self.current_script_names = os.path.basename(self.current_script_name)
        self.current_path = os.path.dirname(os.path.abspath(self.current_script_name))
        # 修改 here，确保 path 指向主脚本所在的目录
        self.path = self.current_path + os.sep  # 直接使用 current_path
        print(f"当前时间：{self.get_date_and_time('%Y-%m-%d %H:%M:%S', 0)}")
        print(f"开始执行脚本：{self.current_script_names}")
        self.logger.info(f"开始执行脚本：{self.current_script_names}")

    def End_operation(self):
        print(f"脚本：{self.current_script_names} 执行成功")
        self.logger.info(f"脚本：{self.current_script_names} 执行成功")
        end_time = time.time()  # 结束运行时间
        elapsed_time = round(end_time - self.start_time, 0)
        print(f"运行时间：{elapsed_time} 秒")
        self.logger.info(f"运行时间：{elapsed_time} 秒")
        self.logger.info('\n' * 10)

    def uxin_wx(self, name, message, mentioned_list=None):
        # corpid = "wxd4e113eb4c0136b9"
        # corpsecret = "PMfPOv2Qqq0iXZAdWHF7WdaW4kkWUZcwyGE4NZtve3k"
        # agentid = "1000026"
        sender = WeComMsg.WeChatWorkSender(self.corpid, self.corpsecret, self.agentid)
        try:
            # 记录发送对象和消息类型
            target_type = "群聊（Webhook）" if name.startswith("https://") else "用户"
            self.logger.info(f"开始向{target_type}发送消息，目标：{name}")

            if name.startswith("https://"):  # 群聊Webhook
                if isinstance(message, str) and message.endswith(('.xlsx', '.docx', '.pdf', '.txt')) and os.path.isfile(
                        message):
                    # 发送群聊文件
                    file_name = os.path.basename(message)
                    file_size = os.path.getsize(message) / 1024
                    self.logger.info(f"发送群聊文件消息：文件名={file_name}，大小={file_size:.2f}KB")
                    result = sender.send_file_to_group(name, message)
                    # 提取并记录message_id
                    msg_id = result.get('msgid', '未知')  # 群聊消息用msgid
                    self.logger.info(f"群聊文件消息发送结果：{'成功' if result.get('errcode') == 0 else '失败'}，"
                                     f"错误信息：{result.get('errmsg')}，消息ID：{msg_id}")

                elif isinstance(message, str):
                    # 发送群聊文本
                    at_info = f"，@对象：{mentioned_list}" if mentioned_list else ""
                    self.logger.info(f"发送群聊文本消息：内容={message}{at_info}")
                    result = sender.send_text_to_group(name, message, mentioned_list=mentioned_list)
                    # 提取并记录message_id
                    msg_id = result.get('msgid', '未知')
                    self.logger.info(f"群聊文本消息发送结果：{'成功' if result.get('errcode') == 0 else '失败'}，"
                                     f"错误信息：{result.get('errmsg')}，消息ID：{msg_id}")

                else:
                    err_msg = "不支持的群聊消息类型"
                    print(err_msg)
                    self.logger.warning(err_msg)
                    return

            else:  # 个人用户
                if isinstance(message, str) and message.endswith(('.jpg', '.jpeg', '.png', '.gif')) and os.path.isfile(
                        message):
                    # 发送个人图片
                    img_name = os.path.basename(message)
                    img_size = os.path.getsize(message) / 1024
                    self.logger.info(f"发送个人图片消息：图片名={img_name}，大小={img_size:.2f}KB")
                    result = sender.send_image([name], message)
                    # 提取并记录message_id
                    msg_id = result.get('msgid', '未知')  # 个人消息用msgid
                    self.logger.info(f"个人图片消息发送结果：{'成功' if result.get('errcode') == 0 else '失败'}，"
                                     f"错误信息：{result.get('errmsg')}，消息ID：{msg_id}")

                elif isinstance(message, str) and message.endswith(
                        ('.xlsx', '.docx', '.pdf', '.txt', 'xls', 'csv')) and os.path.isfile(message):
                    # 发送个人文件
                    file_name = os.path.basename(message)
                    file_size = os.path.getsize(message) / 1024
                    self.logger.info(f"发送个人文件消息：文件名={file_name}，大小={file_size:.2f}KB")
                    result = sender.send_file([name], message)
                    # 提取并记录message_id
                    msg_id = result.get('msgid', '未知')
                    self.logger.info(f"个人文件消息发送结果：{'成功' if result.get('errcode') == 0 else '失败'}，"
                                     f"错误信息：{result.get('errmsg')}，消息ID：{msg_id}")

                elif isinstance(message, str):
                    # 发送个人文本
                    self.logger.info(f"发送个人文本消息：内容={message}")
                    result = sender.send_text([name], message)
                    # 提取并记录message_id
                    msg_id = result.get('msgid', '未知')
                    self.logger.info(f"个人文本消息发送结果：{'成功' if result.get('errcode') == 0 else '失败'}，"
                                     f"错误信息：{result.get('errmsg')}，消息ID：{msg_id}")

                else:
                    err_msg = "不支持的个人消息类型"
                    print(err_msg)
                    self.logger.warning(err_msg)
                    return

            # 控制台输出结果
            if result.get('errcode') == 0:
                print(f"给 {name} 的消息发送成功，消息ID：{result.get('msgid', '未知')}")
            else:
                print(f"给 {name} 的消息发送失败，错误码：{result.get('errcode')}，"
                      f"错误信息：{result.get('errmsg')}，消息ID：{result.get('msgid', '未知')}")

        except Exception as e:
            self.logger.error(f"消息发送失败，报错信息: {e}", exc_info=True)
            print(f"发送失败，报错信息: {e}")

    def recall_message(self, msgid):
        try:
            self.logger.info(f"开始撤回消息，msgid: {msgid}")
            sender = WeComMsg.WeChatWorkSender(self.corpid, self.corpsecret, self.agentid)
            result = sender.recall_message(msgid)

            # 记录撤回结果
            if result.get('errcode') == 0:
                self.logger.info(f"消息撤回成功，msgid: {msgid}")
                print(f"消息撤回成功，msgid: {msgid}")
            else:
                err_msg = f"消息撤回失败，错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}"
                self.logger.warning(err_msg)
                print(err_msg)

            return result
        except Exception as e:
            err_msg = f"撤回消息时发生错误: {str(e)}"
            self.logger.error(err_msg, exc_info=True)
            print(err_msg)
            return

    def Get_update_time(self, data_table):
        url4 = f'http://cptools.xin.com/hive/getLastUpdateTime?table={data_table}'
        res = urllib.request.Request(url4)
        response = urllib.request.urlopen(res)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        someData = soup.select("p")
        json_data = json.loads(someData[0].text)
        d_time = json_data['data']
        d_code = json_data['code']
        d_message = json_data['message']
        # print(d_time, d_code, d_message)
        utc_time = datetime.datetime.utcfromtimestamp(int(d_time))
        beijing_time = utc_time + datetime.timedelta(hours=8)
        self.logger.info(f'更新时间：{beijing_time}')
        print(f'更新时间：{beijing_time}')
        return beijing_time

    def extract_main_table_from_sql(self, sql_query):
        lines = sql_query.split('\n')
        from_line = None
        for line in lines:
            if line.strip().lower().startswith('from'):
                parts = line.strip().split('from', 1)
                if len(parts) > 1:
                    from_table_info = parts[1].strip()
                    # 去除可能存在的别名
                    table_name = from_table_info.split(' ')[0]
                    from_line = table_name
                    break
        self.logger.info(f'数据表：{from_line}')
        print(f'数据表：{from_line}')
        return from_line

    def replace_day(self, sqls, day_num):
        today = datetime.date.today()
        oneday = datetime.timedelta(days=day_num)
        yesterday = str(today - oneday)
        yesterday = yesterday.replace('-', '')
        yesterday_m = yesterday[0:6]
        sqls = sqls.replace('$dt_ymd', yesterday)
        sqls = sqls.replace('$dt_ym', yesterday_m)
        return sqls

    def get_date_and_time(self, format_type, days):
        today = datetime.datetime.today()
        target_date = today - datetime.timedelta(days=days)
        result = target_date.strftime(format_type)
        return result

    def sende_email(self, name, contact_name, title, rec, file, cc=False, bcc=None):
        yag = yagmail.SMTP(user='cc_yingxiao@xin.com', password='cw46pfeznNQx', host='mail.xin.com', port='587',
                           smtp_ssl=False, smtp_starttls=True)
        contents = f'{name} 好：\n \n ' \
                   f'附件为{title}，请查收！\n \n' \
                   f'如有疑问请联系{contact_name}，谢谢~'
        if cc and bcc:
            yag.send(rec, title, contents, file, cc, bcc)
        elif cc:
            yag.send(rec, title, contents, file, cc)
        elif bcc:
            yag.send(rec, title, contents, file, bcc)
        else:
            yag.send(rec, title, contents, file)
        self.logger.info(f'邮件主题：{title} \n邮件附件：{file} 发送完成')
        print(f'邮件主题：{title} \n邮件附件：{file} 发送完成')


    def run_sql(self, path, sql_name, channel=False, sql_content=None):
        """
        执行SQL（支持直接传入SQL内容或从文件读取）

        :param path: SQL文件所在路径
        :param sql_name: SQL文件名（当sql_content为None时有效）
        :param channel: 是否需要替换日期变量
        :param sql_content: 直接传入的SQL内容（可选，优先级高于文件读取）
        :return: 查询结果（非DDL操作时）
        """
        if path is None:
            raise ValueError("path cannot be None")

        # 优先使用传入的SQL内容，否则从文件读取
        if sql_content is None:
            sql_file_path = os.path.join(path, sql_name)
            # self.logger.info(f"准备执行SQL文件：{sql_file_path}")
            # print(f"准备执行SQL文件：{sql_file_path}")

            # 读取SQL文件
            try:
                with open(sql_file_path, encoding='utf-8') as sql_file:
                    sql = sql_file.read()
                self.logger.info(f"SQL文件内容读取成功，长度：{len(sql)}字符")
            except FileNotFoundError:
                error_msg = f"SQL文件不存在：{sql_file_path}"
                self.logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            except Exception as e:
                error_msg = f"读取SQL文件失败：{str(e)}"
                self.logger.error(error_msg)
                raise
        else:
            sql = sql_content
            sql_file_path = f"[直接传入的SQL内容]"
            self.logger.info(f"使用直接传入的SQL内容，长度：{len(sql)}字符")

        try:
            # 替换日期变量（如果需要）
            if channel:
                original_sql = sql  # 保存原始SQL用于日志
                sql = self.replace_day(sql, 0)
                self.logger.info(f"已替换SQL中的日期变量（channel=True）")
                self.logger.info(f"替换前SQL：\n{original_sql}\n替换后SQL：\n{sql}")

            # 连接Hive并执行
            self.logger.info(f"开始连接Hive服务器（地址：172.20.2.190:10023）")
            hive_client = HiveClient.HiveClient('172.20.2.190', 10023, 'cc_yingxiao', 'e147bbed39c810e32f7842cf5f59b9ae')
            self.logger.info(f"Hive连接成功，开始执行SQL：{sql_file_path}")
            print(f"插入表格：开始执行 sql：{sql_file_path}" if channel else f"开始执行 sql：{sql_file_path}")

            # 执行SQL（区分DDL和查询）
            if channel:
                # 执行DDL操作（无返回数据）
                hive_client.ddls(sql)
                self.logger.info(f"SQL执行成功（DDL）：{sql_file_path}")
                print(f"插入表格：{sql_file_path} 执行完成")
                return None
            else:
                # 执行查询（返回数据）
                data = hive_client.pdre(sql)

                # 计算返回数据行数
                if isinstance(data, pd.DataFrame):
                    row_count = len(data) if not data.empty else 0
                else:
                    row_count = len(data) if data else 0
                self.logger.info(f"SQL执行成功（查询）：{sql_file_path}，返回数据行数：{row_count}")

                # 记录查询结果（前10行+后10行）
                if row_count > 0:
                    if isinstance(data, pd.DataFrame):
                        data_str = data.to_string()
                    else:
                        data_str = str(data)

                    data_lines = data_str.split('\n')
                    if len(data_lines) <= 20:
                        self.logger.info(f"Hive查询结果完整数据：\n{data_str}")
                    else:
                        head_lines = '\n'.join(data_lines[:10])
                        tail_lines = '\n'.join(data_lines[-10:])
                        self.logger.info(
                            f"Hive查询结果（共{row_count}行，仅显示前10行和后10行）：\n"
                            f"前10行：\n{head_lines}\n...\n后10行：\n{tail_lines}"
                        )

                print(f"{sql_file_path} 执行完成，返回数据行数：{row_count}")
                return data

        except Exception as e:
            # 错误处理逻辑
            error_summary = f"SQL执行失败（来源：{sql_file_path}）：{str(e)}"
            self.logger.error(error_summary)
            full_error_details = repr(e)
            self.logger.error(f"Hive原始错误详情（完整内容）：\n{full_error_details}")
            stack_trace = traceback.format_exc()
            self.logger.error(f"错误堆栈信息：\n{stack_trace}")
            print(f"SQL执行失败：{error_summary}")
            print(f"Hive原始错误详情：\n{full_error_details}")
            raise

    def run_sql_2(self, path=None, sql_name=None, channel=False, sql_content=None):
        """
        执行SQL（支持直接传入SQL内容或从文件读取）- 优化版Hive连接
        支持两种调用方式：
        1. 直接执行SQL语句：run_sql_2(sql_content='select * from table')
        2. 执行本地SQL文件：run_sql_2(path, 'filename.sql') 或 run_sql_2(path, 'filename.sql', channel=True)

        :param path: SQL文件所在路径（执行文件时必填）
        :param sql_name: SQL文件名（执行文件时必填）
        :param sql_content: 直接传入的SQL内容（可选，优先级最高）
        :param channel: 是否需要替换日期变量（$dt_ymd/$dt_ym，默认False）
        :return: 查询结果（非DDL操作时返回DataFrame，DDL操作返回None）
        """
        # 1. 处理SQL来源（优先用sql_content，其次用path+sql_name）
        if sql_content is not None:
            # 场景1：直接传入SQL语句
            sql = sql_content
            sql_file_path = "[直接传入的SQL内容]"
            self.logger.info(f"[run_sql_2] 使用直接传入的SQL内容，长度：{len(sql)}字符")
        else:
            # 场景2：从本地文件读取SQL（需校验path和sql_name）
            if path is None or sql_name is None:
                raise ValueError("当不传入sql_content时，必须提供path和sql_name")

            sql_file_path = os.path.join(path, sql_name)
            self.logger.info(f"[run_sql_2] 准备执行SQL文件：{sql_file_path}")
            print(f"[run_sql_2] 准备执行SQL文件：{sql_file_path}")

            # 读取SQL文件
            try:
                with open(sql_file_path, encoding='utf-8') as sql_file:
                    sql = sql_file.read()
                self.logger.info(f"[run_sql_2] SQL文件内容读取成功，长度：{len(sql)}字符")
            except FileNotFoundError:
                error_msg = f"[run_sql_2] SQL文件不存在：{sql_file_path}"
                self.logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            except Exception as e:
                error_msg = f"[run_sql_2] 读取SQL文件失败：{str(e)}"
                self.logger.error(error_msg)
                raise

        # 后续逻辑保持不变...
        try:
            if channel:
                original_sql = sql
                sql = self.replace_day(sql, 0)
                self.logger.info(f"[run_sql_2] 已替换SQL中的日期变量")
                self.logger.debug(f"[run_sql_2] 替换前SQL：\n{original_sql}\n替换后SQL：\n{sql}")

            self.logger.info(f"[run_sql_2] 开始连接Hive服务器")
            hive_client = HiveClients.HiveClients(
                host='172.20.2.190',
                port=10023,
                username='cc_yingxiao',
                password='e147bbed39c810e32f7842cf5f59b9ae',
                auth='LDAP',
                database='default'
            )
            self.logger.info(f"[run_sql_2] Hive连接成功，开始执行SQL：{sql_file_path}")
            print(f"[run_sql_2] 插入表格：开始执行 sql：{sql_file_path}" if channel
                  else f"[run_sql_2] 开始执行 sql：{sql_file_path}")

            if channel:
                hive_client.ddls(sql)
                self.logger.info(f"[run_sql_2] SQL执行成功（DDL）：{sql_file_path}")
                print(f"[run_sql_2] 插入表格：{sql_file_path} 执行完成")
                return None
            else:
                data = hive_client.pdre(sql)

                # 统计返回数据行数
                if isinstance(data, pd.DataFrame):
                    row_count = len(data) if not data.empty else 0
                else:
                    row_count = len(data) if data else 0
                self.logger.info(f"[run_sql_2] SQL执行成功（查询）：{sql_file_path}，返回数据行数：{row_count}")

                # 日志记录查询结果
                if row_count > 0:
                    data_str = data.to_string() if isinstance(data, pd.DataFrame) else str(data)
                    data_lines = data_str.split('\n')
                    if len(data_lines) <= 20:
                        self.logger.info(f"[run_sql_2] Hive查询结果完整数据：\n{data_str}")
                    else:
                        head_lines = '\n'.join(data_lines[:10])
                        tail_lines = '\n'.join(data_lines[-10:])
                        self.logger.info(
                            f"[run_sql_2] Hive查询结果（共{row_count}行，仅显示前10行和后10行）：\n"
                            f"前10行：\n{head_lines}\n...\n后10行：\n{tail_lines}"
                        )

                print(f"[run_sql_2] {sql_file_path} 执行完成，返回数据行数：{row_count}")
                return data

        except Exception as e:
            error_summary = f"[run_sql_2] SQL执行失败（来源：{sql_file_path}）：{str(e)}"
            self.logger.error(error_summary)
            full_error_details = repr(e)
            self.logger.error(f"[run_sql_2] Hive原始错误详情：\n{full_error_details}")
            stack_trace = traceback.format_exc()
            self.logger.error(f"[run_sql_2] 错误堆栈信息：\n{stack_trace}")
            print(f"[run_sql_2] SQL执行失败：{error_summary}")
            print(f"[run_sql_2] Hive原始错误详情：\n{full_error_details}")
            raise

    def writer_excel_data(self, path, filename, send_file, sheet_data, headers):
        self.logger.info('开始处理Excel表格')
        print('开始处理Excel表格')
        filename = path + filename  # 模板名
        send_file = send_file  # 附件名
        dfs = []
        sheet_names = []
        clear_ranges = []
        date_ranges = []
        for sheet in sheet_data:  # 循环清除
            dfs.append(sheet['data'])
            sheet_names.append(sheet['sheet_name'])
            clear_ranges.append(sheet['clear_range'])
            date_ranges.append(sheet['date_range'])
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(filename)

        for i in range(0, len(dfs)):
            sheet_name = sheet_names[i]
            # 检查sheet是否存在，不存在则创建
            if sheet_name not in [sheet.name for sheet in wb.sheets]:
                wb.sheets.add(name=sheet_name)
            wb.sheets[sheet_name].range(clear_ranges[i]).clear_contents()  # 选择清除数据的位置
            wb.sheets[sheet_name].range(date_ranges[i]).options(index=False, header=headers).value = dfs[i]  # 选择粘贴数据的位置

        wb.save()
        wb.close()
        app.quit()
        shutil.copyfile(filename, send_file)  # 复制表格
        self.logger.info(f'表格 {os.path.basename(send_file)}  处理完成')
        print(f'表格 {os.path.basename(send_file)}  处理完成')



    def Yesterday_data_num(self, data, sql_name, columns, num):
        self.logger.info(f'检查{sql_name}表中昨日数据数量')
        print(f'检查{sql_name}表中昨日数据数量')
        df = data[[columns]].copy()
        df = df[~df[columns].isnull()]
        df.loc[:, 'date'] = pd.to_datetime(df[columns]).dt.strftime('%Y/%m/%d')
        df_filter = df[df['date'] == self.get_date_and_time('%Y/%m/%d', 1)]
        df_filter_group = df_filter.groupby(['date']).agg({
            columns: 'count'
        }).reset_index(drop=False)
        df_filter_group.rename(columns={columns: '昨日数据量'}, inplace=True)
        df_num = df_filter_group['昨日数据量']
        if pd.isnull(df_filter_group['昨日数据量']).any():
            self.logger.warning(f'警告：数据表 {sql_name} 昨日数据量为0，请尽快检查数据')
            print(f'警告：数据表 {sql_name} 昨日数据量为0，请尽快检查数据')
            self.uxin_wx('dongyang', f'警告：数据表 {sql_name} 昨日数据量为0，请尽快检查数据')
        else:
            df_num_value = df_num.iloc[0] if len(df_num) > 0 else 0
            if df_num_value < num:
                self.logger.warning(
                    f'警告：数据表 {sql_name} 昨日数据量不足{num}，只有{df_num_value}，请尽快检查数据')
                print(f'警告：数据表 {sql_name} 昨日数据量不足{num}，只有{df_num_value}，请尽快检查数据')
                self.uxin_wx('dongyang',
                             f'警告：数据表 {sql_name} 昨日数据量不足{num}，只有{df_num_value}，请尽快检查数据')

    def screen(self, filename, sheetname, screen_area, img_name):
        self.logger.info('开始截图')
        print('开始截图')
        # pythoncom.CoInitialize()  # 多线程
        app = xw.App(visible=False, add_book=False)
        # app.display_alerts = False
        # app.screen_updating = False
        wb = app.books.open(filename)
        sht = wb.sheets[sheetname]
        range_val = sht.range(screen_area)
        range_val.api.CopyPicture()
        sht.api.Paste()
        pic = sht.pictures[0]  # 当前图片
        pic.api.Copy()  # 复制图片
        while True:
            img = ImageGrab.grabclipboard()  # 获取剪贴板的图片数据
            if img is not None:
                break
        # 如果图片已存在则覆盖
        if os.path.exists(img_name):
            os.remove(img_name)
        img.save(img_name)  # 保存图片
        pic.delete()  # 删除sheet上的图片

        # 设置图片尺寸
        def get_FileSize(img_name):
            # filePath = unicode(filePath,'utf8')
            fsize = os.path.getsize(img_name)
            fsize = fsize / float(1024)
            return round(fsize, 2)

        # 当图片大小小于100k时更改图片尺寸
        def Change_size(img_name):
            p_size = self.get_FileSize(img_name)
            if p_size < 101:
                sImg = Image.open(img_name)  # 图片位置
                w, h = sImg.size
                dImg = sImg.resize((int(w * 1.1), int(h * 1.1)), Image.LANCZOS)  # 设置压缩尺寸和选项，注意尺寸要用括号
                dImg.save(img_name)  # 图片位置

        Change_size(img_name)
        wb.close()  # 关闭excel
        app.quit()
        # pythoncom.CoUninitialize()
        self.logger.info(f'图片：{img_name} 截图并保存完成')
        print(f'图片：{img_name} 截图并保存完成')

    def column_label(self, n):
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def excel_catch_screen(self, data, path, filename, sheet_name, start_range, image_filename):
        image_path = path + image_filename + '.png'
        self.screen(filename, sheet_name,
                    f"{start_range}:%s" % (self.column_label(len(data.columns)) + str(len(data) + 1)), image_path)

    def send_email_new(self, recipient_emails, cc_emails=None, bcc_emails=None, subject="", html_body="", attachments=None):
        sender_email = 'cc_yingxiao@xin.com'
        sender_password = 'cw46pfeznNQx'
        # 创建一个多部分消息
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        if bcc_emails:
            msg['Bcc'] = ', '.join(bcc_emails)
        msg['Subject'] = subject

        # 添加 HTML 正文
        body = MIMEText(html_body, 'html')
        msg.attach(body)

        # 添加附件
        if attachments:
            for attachment in attachments:
                with open(attachment, 'rb') as file:
                    # 使用 os.path.basename 来获取正确的文件名
                    part = MIMEApplication(file.read(), Name=os.path.basename(attachment))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                    msg.attach(part)

        # 连接到 SMTP 服务器
        with smtplib.SMTP('mail.xin.com', 587, timeout=120) as smtp:
            # smtp.starttls()
            smtp.login(sender_email, sender_password)
            all_recipients = recipient_emails
            if cc_emails:
                all_recipients += cc_emails
            if bcc_emails:
                all_recipients += bcc_emails
            smtp.sendmail(sender_email, all_recipients, msg.as_string())

    # def insert_df_to_hive(self, df, data_table):
    #     hive_client = HiveClient('172.20.2.190', 10023, 'cc_yingxiao', 'e147bbed39c810e32f7842cf5f59b9ae')
    #     hive_client.insert_df_to_hive(df, data_table)

    def format_excel_worksheet(self, worksheet, df, workbook):
        # self.logger.info('开始格式化 Excel 工作表')
        # print('开始格式化 Excel 工作表')
        # 定义日期格式（包含边框和居中样式）
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'font_name': '微软雅黑',
            'font_size': 10,
            'border': 1,
            'align': 'center'
        })

        # 定义数据区域格式
        data_format = workbook.add_format({
            'font_name': '微软雅黑',
            'font_size': 10,
            'border': 1,
            'align': 'center'
        })

        # 标题行样式（保持不变）
        header_format = workbook.add_format({
            'font_name': '微软雅黑',
            'font_size': 10,
            'bold': True,
            'bg_color': '#ADD8E6',
            'font_color': 'black',
            'border': 1,
            'align': 'center'
        })

        columns_dtypes = df.dtypes  # 获取列数据类型

        def get_char_length(text):
            """优化后的字符长度计算"""
            text = str(text).strip()
            return sum(2 if re.match(r'[\u4e00-\u9fff\uff00-\uffef]', c) else 1 for c in text)

        # 设置列宽和基础格式
        for col_num, (column_name, col_dtype) in enumerate(zip(df.columns, columns_dtypes)):
            max_data_len = df[column_name].apply(get_char_length).max()
            header_len = get_char_length(column_name)
            max_len = max(max_data_len, header_len) + 2
            worksheet.set_column(col_num, col_num, max_len)

        # 写入标题行
        worksheet.write_row(0, 0, df.columns, header_format)

        # 写入数据行（根据列数据类型应用格式）
        max_row, max_col = df.shape
        for row in range(1, max_row + 1):
            for col in range(max_col):
                value = df.iat[row - 1, col]
                col_dtype = columns_dtypes[col]

                # 日期类型处理
                if pd.api.types.is_datetime64_any_dtype(col_dtype):
                    if pd.isna(value):
                        worksheet.write_blank(row, col, None, date_format)
                    else:
                        worksheet.write(row, col, value, date_format)
                # 其他数据类型
                else:
                    worksheet.write(row, col, value, data_format)

        # 冻结窗格和添加筛选
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, max_row, max_col)
        # self.logger.info('Excel 工作表格式化完成')
        # print('Excel 工作表格式化完成')

    def export_df_to_excel(self, df_list, sheet_names, file_path):
        new_df_list = []
        for df in df_list:
            # 全面替换 Inf 和 NaN
            df = df.replace([np.inf, -np.inf, np.nan], None)
            new_df_list.append(df)

        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

        for idx, (df, sheet_name) in enumerate(zip(new_df_list, sheet_names)):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            workbook = writer.book
            self.format_excel_worksheet(worksheet, df, workbook)

        writer.close()
        self.logger.info(f'Excel 文件导出完成: {file_path}')
        print(f'Excel 文件导出完成: {file_path}')


    # # 将中文字转化成拼音+数字
    # def name_to_pinyin(self, name):
    #     """
    #     将中文名称+数字格式转换为拼音+数字格式
    #     :param name: 原始名称（如"张三123"）
    #     :return: 转换后的拼音名称（如"zhangsan123"）
    #     """
    #     match = re.match(r'(\D+)(\d+)', name)
    #     if not match:
    #         return name  # 如果不符合格式，保留原值
    #
    #     chinese_part = match.group(1)
    #     number_part = match.group(2)
    #
    #     # 转换为拼音（去除空格）
    #     pinyin = ''.join(lazy_pinyin(chinese_part))
    #
    #     # 组合拼音和数字
    #     return pinyin + number_part

    def name_to_pinyin(self, name):
        """
        将中文名称转换为拼音+其他字符（兼容带数字/符号的名称）
        :param name: 原始名称（如"张三123"、"李四"、"王五_456"）
        :return: 转换后的拼音名称（如"zhangsan123"、"lisi"、"wangwu_456"）
        """
        # 提取字符串中的所有中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', name)  # 匹配所有中文
        non_chinese_part = re.sub(r'[\u4e00-\u9fa5]', '', name)  # 提取非中文字符（数字、符号等）

        if not chinese_chars:
            return name  # 无中文字符，直接返回原值

        # 转换中文字符为拼音（去除空格）
        pinyin = ''.join(lazy_pinyin(chinese_chars))

        # 拼接拼音和非中文部分（保留数字、符号等）
        return pinyin + non_chinese_part

    # 车辆转移任务  转移给新负责人
    def car_task_transfer(self, df, name_column):
        """车辆转移任务（改用requests直接调用API，无需浏览器驱动）"""
        self.logger.info("开始处理车辆分配任务（使用requests调用API）")
        print("开始处理车辆分配任务（使用requests调用API）")

        try:
            # 检查必要的列
            if 'vin' not in df.columns:
                raise ValueError("数据框中缺少必要的'vin'列")
            if name_column not in df.columns:
                raise ValueError(f"数据框中缺少指定的名称列: {name_column}")

            # 转换名称为拼音
            df["name"] = df[name_column].apply(self.name_to_pinyin)
            process_df = df[['vin', 'name']].copy().reset_index()
            self.logger.info(f"成功转换{len(process_df)}条记录")

            # 获取当前日期
            today = self.get_date_and_time("%Y-%m-%d", 0)
            self.logger.info(f"当前处理日期: {today}")

            # 直接用requests调用API（无需浏览器）
            success_count = 0
            fail_count = 0
            for index, row in process_df.iterrows():
                try:
                    # 构建API地址
                    api_url = f"http://api-cs.xin.com/super/tool/again_allot_car_task?date={today}&vin={row['vin']}&master_name={row['name']}"

                    # 发送GET请求（模拟浏览器访问）
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                    }
                    response = requests.get(api_url, headers=headers, timeout=10)

                    # 检查请求是否成功
                    if response.status_code == 200:
                        success_count += 1
                        self.logger.info(f"第{index + 1}条成功：{row['vin']} 任务分配给{row['name']}")
                    else:
                        fail_count += 1
                        self.logger.error(f"第{index + 1}条失败（状态码：{response.status_code}）：{row['vin']} 任务分配给{row['name']}")

                    time.sleep(2)  # 避免请求过于频繁
                except Exception as e:
                    fail_count += 1
                    self.logger.error(f"第{index + 1}条出错：{str(e)}")

            # 处理结果统计
            self.logger.info(f"处理完成 - 成功: {success_count}, 失败: {fail_count}")
            print(f"处理完成 - 成功: {success_count}, 失败: {fail_count}")

        except Exception as e:
            self.logger.error(f"车辆分配处理出错: {str(e)}")
            raise

    def _wechat_doc_get_access_token(self):
        """获取企业微信文档接口访问令牌（内部辅助方法）"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.WECHAT_DOC_CORP_ID}&corpsecret={self.WECHAT_DOC_SECRET}"
        response = requests.get(url)
        result = response.json()

        if result.get("errcode") != 0:
            error_msg = f"获取文档access_token失败: {result.get('errmsg')}"
            self._wechat_doc_log(error_msg)
            raise Exception(error_msg)

        self._wechat_doc_log("成功获取文档access_token")
        return result.get("access_token")

    def _wechat_doc_log(self, message):
        """企业微信文档操作日志记录（单独日志文件，内部辅助方法）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}\n"
        with open(self.WECHAT_DOC_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        # 同时在主日志中同步记录（便于调试）
        self.main_logger.info(f"[企业微信文档] {message}")

    def _wechat_doc_refresh_token_if_needed(self):
        """令牌过期时自动刷新（内部辅助方法）"""
        if not self.wechat_doc_access_token:
            self.wechat_doc_access_token = self._wechat_doc_get_access_token()


    # -------------------------- 企业微信文档功能：核心辅助方法（原WechatWorkDocs内部方法） --------------------------
    def _wechat_doc_get_access_token(self):
        """（文档功能独立）获取企业微信文档访问令牌"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.WECHAT_DOC_CORP_ID}&corpsecret={self.WECHAT_DOC_SECRET}"
        response = requests.get(url)
        result = response.json()

        if result.get("errcode") != 0:
            error_msg = f"获取文档access_token失败: {result.get('errmsg')}"
            self._wechat_doc_log(error_msg)
            raise Exception(error_msg)

        # self._wechat_doc_log("成功获取文档access_token")
        return result.get("access_token")

    def _wechat_doc_log(self, message):
        """（文档功能独立）文档操作日志记录（不依赖主类日志）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}\n"
        with open(self.WECHAT_DOC_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        # 同时在主类日志中同步记录（便于统一排查）
        self.logger.info(f"[企业微信文档] {message}")

    def _wechat_doc_refresh_token_if_needed(self):
        """（文档功能独立）自动刷新过期的access_token"""
        if not self.wechat_doc_access_token:
            self.wechat_doc_access_token = self._wechat_doc_get_access_token()

    # -------------------------- 企业微信文档功能：对外方法（原WechatWorkDocs公开方法） --------------------------
    def wx_create_table(self, sheet_name, admin_users=None):
        """
        创建企业微信智能表格
        :param sheet_name: 表格名称
        :param admin_users: 管理员用户ID列表（可选）
        :return: 新建表格的docid和url字典
        """
        self._wechat_doc_refresh_token_if_needed()

        url = f"https://qyapi.weixin.qq.com/cgi-bin/wedoc/create_doc?access_token={self.wechat_doc_access_token}"
        data = {
            "spaceid": self.WECHAT_DOC_SPACE_ID,
            "fatherid": self.WECHAT_DOC_SPACE_ID,  # 在根目录创建
            "doc_type": 10,  # 10表示智能表格
            "doc_name": sheet_name
        }

        if admin_users:
            data["admin_users"] = admin_users

        response = requests.post(url, data=json.dumps(data))
        result = response.json()

        if result.get("errcode") != 0:
            error_msg = f"创建智能表格失败: {result.get('errmsg')}"
            self._wechat_doc_log(error_msg)
            raise Exception(error_msg)

        # 记录操作日志
        docid = result.get("docid")
        self._wechat_doc_log(f"创建智能表格成功：名称={sheet_name}，docid={docid}")
        return {
            "docid": docid,
            "url": result.get("url")
        }

    def wx_get_sheets(self, docid):
        """
        查询企业微信文档的子表信息
        :param docid: 文档ID
        :return: 子表列表（包含子表ID、标题、类型等信息）
        """
        self._wechat_doc_log(f"开始查询文档[{docid}]的子表信息")
        self._wechat_doc_refresh_token_if_needed()

        url = f"https://qyapi.weixin.qq.com/cgi-bin/wedoc/smartsheet/get_sheet?access_token={self.wechat_doc_access_token}"
        data = {
            "docid": docid,
            "need_all_type_sheet": True
        }

        response = requests.post(url, data=json.dumps(data))
        result = response.json()

        if result.get("errcode") != 0:
            error_msg = f"查询子表失败: {result.get('errmsg')}"
            self._wechat_doc_log(error_msg)
            raise Exception(error_msg)

        sheet_list = result.get("sheet_list", [])
        # 记录查询结果
        self._wechat_doc_log(f"查询文档[{docid}]子表完成，共找到{len(sheet_list)}个子表")
        for sheet in sheet_list:
            sheet_info = (f"子表信息 - ID: {sheet['sheet_id']}, 标题: {sheet['title']}, "
                          f"类型: {sheet['type']}, 可见性: {'可见' if sheet['is_visible'] else '不可见'}")
            self._wechat_doc_log(sheet_info)
            print(f"[企业微信文档] {sheet_info}")  # 控制台同步输出

        return sheet_list

    def wx_run_excel(self, docid, sheet_id):
        """
        从企业微信智能表格导出记录到Excel（新增：含“日期”“时间”关键词列自动转为北京时间）
        :param docid: 文档ID
        :param sheet_id: 子表ID
        :param excel_filename: 导出的Excel文件路径（含文件名）
        """
        self._wechat_doc_log(f"开始读取文档[{docid}]子表[{sheet_id}]的记录到dataframe")
        self._wechat_doc_refresh_token_if_needed()

        # -------------------------- 1. 分页获取企业微信表格记录（修复重复代码，保留核心逻辑） --------------------------
        url = f"https://qyapi.weixin.qq.com/cgi-bin/wedoc/smartsheet/get_records?access_token={self.wechat_doc_access_token}"
        data = {
            "docid": docid,
            "sheet_id": sheet_id,
            "key_type": "CELL_VALUE_KEY_TYPE_FIELD_TITLE",
            "limit": 1000,
            "offset": 0
        }

        all_records = []
        has_more = True
        while has_more:
            response = requests.post(url, data=json.dumps(data))
            result = response.json()
            if result.get("errcode") != 0:
                error_msg = f"查询记录失败: {result.get('errmsg')}"
                self._wechat_doc_log(error_msg)
                raise Exception(error_msg)
            records = result.get("records", [])
            all_records.extend(records)
            has_more = result.get("has_more", False)
            data["offset"] = result.get("next", 0)

        if not all_records:
            msg = f"文档[{docid}]子表[{sheet_id}]没有找到记录，无需导出"
            self._wechat_doc_log(msg)
            print(f"[企业微信文档] {msg}")
            return

        # -------------------------- 2. 核心工具：统一时间转换（兼容所有格式） --------------------------
        def _unified_time_convert(value):
            """
            统一转换工具：支持DateTimeFieldProperty、毫秒/秒级时间戳、文本嵌套等格式，输出北京时间
            :param value: 原始数据（任意格式）
            :return: 北京时间字符串（YYYY-MM-DD HH:MM:SS）或原始值（转换失败）
            """
            # 空值直接返回
            if value is None or str(value).strip() in ["", "None", "nan"]:
                return ""

            # 场景1：处理DateTimeFieldProperty类型（企业微信日期字段标准格式）
            # 格式1：字典 → {"type":"DateTimeFieldProperty","value":1759852800000}
            if isinstance(value, dict) and value.get("type") == "DateTimeFieldProperty":
                ts = value.get("value")
                if isinstance(ts, (int, float)):
                    return _timestamp_to_beijing(ts)
                else:
                    self._wechat_doc_log(f"DateTimeFieldProperty时间戳非数字：{value}")
                    return str(value)

            # 格式2：列表嵌套字典 → [{"type":"DateTimeFieldProperty","value":1759852800000}]
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                nested_dict = value[0]
                # 子场景1：嵌套DateTimeFieldProperty
                if nested_dict.get("type") == "DateTimeFieldProperty":
                    ts = nested_dict.get("value")
                    if isinstance(ts, (int, float)):
                        return _timestamp_to_beijing(ts)
                    else:
                        self._wechat_doc_log(f"嵌套DateTimeFieldProperty时间戳非数字：{value}")
                        return str(value)
                # 子场景2：嵌套文本（如[{"text":"1759852800000"}]）
                elif "text" in nested_dict:
                    text_val = nested_dict["text"]
                    return _extract_and_convert_ts(text_val)
                # 其他嵌套格式（如[{"title":"2025-10-07"}]）
                else:
                    return str(nested_dict.get("title", nested_dict.get("text", str(value))))

            # 场景2：纯文本/数字（直接提取时间戳）
            else:
                return _extract_and_convert_ts(str(value))

        def _timestamp_to_beijing(timestamp):
            """毫秒级时间戳转北京时间（内部调用，不对外暴露）"""
            try:
                # 统一转为毫秒级（若传入秒级，自动补全）
                ts = int(timestamp)
                if len(str(ts)) == 10:
                    ts *= 1000  # 秒级 → 毫秒级
                # UTC时间转北京时间（+8小时）
                utc_dt = datetime.datetime.utcfromtimestamp(ts / 1000)
                beijing_dt = utc_dt + datetime.timedelta(hours=8)
                return beijing_dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OverflowError) as e:
                self._wechat_doc_log(f"时间戳转换失败（值：{timestamp}），错误：{str(e)}")
                return str(timestamp)

        def _extract_and_convert_ts(raw_text):
            """从文本中提取10-13位时间戳并转换（内部调用，不对外暴露）"""
            # 用正则提取文本中的10-13位数字（时间戳特征）
            ts_match = re.search(r"\d{10,13}", raw_text)
            if ts_match:
                ts = ts_match.group()
                return _timestamp_to_beijing(ts)
            # 无时间戳则返回原始文本（如已是“2025-10-07”格式）
            else:
                return raw_text

        # -------------------------- 3. 格式化记录（新增：标记日期相关列并转换） --------------------------
        rows = []
        # 先获取所有自定义字段名（用于后续标记日期列）
        custom_fields = set()
        for record in all_records[:1]:  # 取第一条记录即可（所有记录字段结构一致）
            if record.get("values"):
                custom_fields = set(record["values"].keys())
                break
        # 系统字段 + 自定义字段 = 所有字段
        all_fields = ["记录ID", "创建时间", "更新时间", "最后编辑者"] + list(custom_fields)
        # 标记含“日期”“时间”关键词的列（需转换的目标列）
        date_related_columns = [col for col in all_fields if any(kw in str(col) for kw in ["日期", "时间"])]
        self._wechat_doc_log(f"识别到需转换的日期相关列：{date_related_columns}")

        # 循环处理每条记录
        for record in all_records:
            # 系统字段初始化（创建时间、更新时间已在日期列中，优先转换）
            row = {
                "记录ID": record.get("record_id"),
                "创建时间": _unified_time_convert(record.get("create_time")),  # 系统时间戳转换
                "更新时间": _unified_time_convert(record.get("update_time")),  # 系统时间戳转换
                "最后编辑者": record.get("updater_name")
            }

            # 处理自定义字段（仅转换日期相关列）
            values = record.get("values", {})
            for field_name, field_value in values.items():
                # 判断是否为日期相关列，是则调用统一转换工具
                if field_name in date_related_columns:
                    row[field_name] = _unified_time_convert(field_value)
                # 非日期列按原有逻辑处理
                else:
                    if isinstance(field_value, list) and len(field_value) > 0:
                        if isinstance(field_value[0], dict):
                            row[field_name] = field_value[0].get("text",
                                                                 field_value[0].get("title", str(field_value[0])))
                        else:
                            row[field_name] = str(field_value)
                    else:
                        row[field_name] = str(field_value) if field_value is not None else ""

            rows.append(row)

        # -------------------------- 4. 导出Excel（优化：日期列格式美化） --------------------------
        df = pd.DataFrame(rows)
        df = df[df['更新时间'] != '0']
        # 使用openpyxl引擎，确保Excel中日期格式正常显示（避免文本格式）
        # with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
        #     df.to_excel(writer, index=False, sheet_name="企业微信数据")
        #     worksheet = writer.sheets["企业微信数据"]
        #
        #     # 对日期相关列设置格式：列宽适配 + 日期格式
        #     for col_idx, col_name in enumerate(df.columns, 1):  # Excel列号从1开始
        #         if col_name in date_related_columns:
        #             # 列宽设为22（适配“YYYY-MM-DD HH:MM:SS”）
        #             worksheet.column_dimensions[chr(64 + col_idx)].width = 22
        #             # 批量设置单元格格式为“日期时间”（避免Excel按文本显示）
        #             for row_idx in range(2, len(df) + 2):  # 第1行是表头，从第2行开始
        #                 cell = worksheet.cell(row=row_idx, column=col_idx)
        #                 cell.number_format = "YYYY-MM-DD HH:MM:SS"

        msg = f"成功读取{len(rows)}条记录到dataframe（{len(date_related_columns)}个日期相关列已转为北京时间）"
        self._wechat_doc_log(msg)
        print(f"[企业微信文档] {msg}")

        return df

    def wx_delete_table(self, docid):
        """
        删除企业微信文档
        :param docid: 文档ID
        :return: 删除成功返回True
        """
        self._wechat_doc_log(f"开始删除文档：docid={docid}")
        self._wechat_doc_refresh_token_if_needed()

        url = f"https://qyapi.weixin.qq.com/cgi-bin/wedoc/del_doc?access_token={self.wechat_doc_access_token}"
        data = {"docid": docid}

        response = requests.post(url, data=json.dumps(data))
        result = response.json()

        if result.get("errcode") != 0:
            error_msg = f"删除文档失败: {result.get('errmsg')}"
            self._wechat_doc_log(error_msg)
            raise Exception(error_msg)

        self._wechat_doc_log(f"文档删除成功：docid={docid}")
        return True

# 表格导出使用示例
# df1 = pd.DataFrame(df)
# df2 = pd.DataFrame(df)
# df3 = pd.DataFrame(df)
#
# export_dfs_to_excel(
#     df_list=[df1, df2, df3],
#     sheet_names=['汇总', '扣款', '赚钱'],
#     file_path='多Sheet数据.xlsx'
# )


# # 新版发送邮件调用代码
# recipients = ["dongyang@xin.com"]
# cc = ["dongyang@xin.com"]
# bcc = ["dongyang@xin.com"]
# subject = "测试邮件"
# html_body = "这是一封测试邮件"
# files1 = [send_file1]
# sender.send_email(recipients, cc, bcc, subject, html_body, files1)


# 实例化 DataProcessingAndMessaging 类
# ux = DataProcessingAndMessaging()
# for method_name in dir(ux):
#     if not method_name.startswith("__"):
#         globals()[method_name] = getattr(ux, method_name)
# # 开始运行脚本，这将设置路径，确保 path和 current_script_name已被正确赋值
# Start_Get_filepath_and_filename()
# path = ux.path
# current_script_name = ux.current_script_name

