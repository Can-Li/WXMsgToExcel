import os
import traceback
import shutil

from script.msg_pb2 import MessageBytesExtra


root_path = './data/files/'
if not os.path.exists('./data'):
    os.mkdir('./data')
if not os.path.exists(root_path):
    os.mkdir(root_path)


class File:
    def __init__(self):
        self.open_flag = False


def get_file(bytes_extra, file_name, output_path, wxid, wx_dir) -> str:
    try:
        msg_bytes = MessageBytesExtra()
        msg_bytes.ParseFromString(bytes_extra)
        file_path = ''
        real_path = ''
        if len(msg_bytes.message2) > 0:
            for filed in msg_bytes.message2:
                if filed.field1 == 4:
                    file_original_path = filed.field2

                    file_path = os.path.join(output_path, file_name)
                    if os.path.exists(file_path):
                        # print('文件' + file_path + '已存在')
                        return file_path
                    if os.path.isabs(file_original_path):  # 绝对路径可能迁移过文件目录，也可能存在其他位置
                        if os.path.exists(file_original_path):
                            real_path = file_original_path
                        else:  # 如果没找到再判断一次是否是迁移了目录
                            if file_original_path.find(r"FileStorage") != -1:
                                real_path = wx_dir + file_original_path[
                                                            file_original_path.find("FileStorage") - 1:]
                    else:
                        if file_original_path.find(wxid) != -1:
                            real_path = wx_dir + file_original_path.replace(wxid, '')
                        else:
                            real_path = wx_dir + file_original_path
                    if real_path != "":
                        if os.path.exists(real_path):
                            shutil.copy2(real_path, file_path)
                        else:
                            file_path = ''
        return file_path
    except:
        print(traceback.format_exc(), end='', flush=True)
        return ""
