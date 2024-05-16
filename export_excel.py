import sqlite3
import openpyxl
import os
import re
from tqdm import tqdm
from datetime import datetime
from script.msg_pb2 import MessageBytesExtra

# 定义类型映射字典
type_mapping = {
    (1, 0): "普通消息",
    (3, 0): "图片消息",
    (34, 0): "语言消息",
    (35, 0): "邮件消息",
    (37, 0): "新添加的朋友",
    (42, 0): "名片消息",
    (43, 0): "视频消息",
    (47, 0): "表情消息",
    (48, 0): "位置分享消息",
    (49, 1): "网址链接",
    (49, 3): "QQ音乐分享链接",
    (49, 4): "外部视频分享链接",
    (49, 5): "外部网址分享链接",
    (49, 6): "文件",
    (49, 7): "微信游戏分享",
    (49, 8): "GIF图片",
    (49, 17): "发起位置共享",
    (49, 19): "聊天记录分享",
    (49, 24): "收藏分享",
    (49, 33): "小程序分享",
    (49, 36): "小程序分享",
    (49, 50): "视频号名片",
    (49, 51): "视频号视频分享",
    (49, 57): "引用消息",
    (49, 63): "视频号直播分享",
    (49, 87): "群公告",
    (49, 92): "音乐分享",
    (49, 101): "王者荣耀活动链接",
    (49, 2000): "微信转账",
    (50, 0): "语音通话",
    (65, 0): "朋友推荐消息",
    (10000, 0): "系统提示",
    (10000, 4): "拍了拍",
    (10000, 5): "群聊邀请",
    (10000, 57): "撤回消息",
    (10000, 8000): "群聊邀请",
}


def get_message_type(category, subcategory):
    """
    根据大类和小类获取消息类型
    :param category: 大类
    :param subcategory: 小类
    :return: 类型名称，如果找不到则返回"未知类型"
    """
    message_type = type_mapping.get((category, subcategory), "未知类型")
    return message_type


def get_wxid():
    wxidnums = []
    for folder_name in os.listdir('db\\'):
        if os.path.isdir('db\\' + folder_name):
            wxidnums.append(folder_name)
    return wxidnums


def get_data(wxidnum):
    conn = sqlite3.connect(f'db\\{wxidnum}\\MSG.db')
    cursor = conn.execute('''
    SELECT a.localId, a.CreateTime, a.IsSender, a.StrContent, a.StrTalker, b.Remark, b.NickName, a.BytesExtra, a.Type, a.SubType 
    FROM msg a 
    JOIN Contact b ON a.StrTalker = b.UserName
    ORDER BY a.localId ASC;
                ''')

    print("正在读取数据库...")
    db_all = []
    for row in cursor:
        db_all.append(row)
    return db_all


def get_contact(wxidnum):
    print("正在读取联系人数据库...")
    conn = sqlite3.connect(f'db\\{wxidnum}\\MSG.db')
    cursor = conn.execute('''
    select UserName,Remark,NickName from Contact
    ''')
    contact_db = {}
    for row in tqdm(cursor):
        contact_db[row[0]] = [row[1], row[2]]
    print("联系人数据库读取完成")
    return contact_db


def deal_data(db_all, wxidnum):
    all_data_list = []
    contact_data = get_contact(wxidnum)
    print("数据库读取完成,开始处理数据...")
    for row in tqdm(db_all):
        row_list = list(row)
        row_list[1] = datetime.fromtimestamp(row_list[1]).strftime("%Y-%m-%d %H:%M:%S")  # 将时间戳转为时间
        if '@chatroom' in row[4]:
            if row[2] == 1:
                row_list[7] = '我'  # IsSender为1则为自己发送
            else:
                msgbytes = MessageBytesExtra()  # 解析发送人
                msgbytes.ParseFromString(row[7])  # 解析第七个字段BytesExtra
                for tmp in msgbytes.message2:
                    if tmp.field1 != 1:
                        continue
                    wxid = tmp.field2
                    row_list[7] = wxid

                    try:
                        if contact_data[wxid][0] != '':
                            row_list[7] = contact_data[wxid][0]  # 如果有备注,则改为备注,没有备注则为昵称
                        else:
                            row_list[7] = contact_data[wxid][1]  # 修改第7个字段的值,将字节码修改为昵称
                    except KeyError:
                        continue
        else:
            if row[2] == 1:
                row_list[7] = '我'  # IsSender为1则为自己发送
            else:
                if row[5] != '':
                    row_list[7] = row[5]
                else:
                    row_list[7] = row[6]
        row_list[8] = get_message_type(row[8], row[9])
        if row_list[8] == '系统提示':
            row_list[7] = ''
        row_list.pop()
        all_data_list.append(row_list)
    return all_data_list


def write_excel(data, wxidnum):
    print('数据处理完毕,开始导出数据...')
    workbook = openpyxl.Workbook()
    sheet = workbook['Sheet']
    sheet.append(['序号', '时间', '发送人', '消息内容', '发送人微信号', '备注', '昵称', '消息发送者', '消息类型'])
    for i in tqdm(range(len(data))):
        try:
            data[i][3] = re.sub('[\x00-\x1f\x7f]', '', data[i][3])
            sheet.append(data[i])
        except Exception as e:
            print('异常数据', e, data[i][3])
    workbook.save(f'wechat_{wxidnum}.xlsx')
    input('导出完成,按任意建关闭...')


if __name__ == '__main__':
    wxids = get_wxid()
    for wx in wxids:
        all_data = get_data(wx)
        deal_over_data = deal_data(all_data, wx)
        write_excel(deal_over_data, wx)
