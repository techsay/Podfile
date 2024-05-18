# -*- coding: utf-8 -*-

import os
import shutil
import glob

import re

lockfile_path = '../Podfile.lock'

# 创建空字典 name: index
my_dict = {}
list_dict = {}

# podfile_modules = ["PODS", "DEPENDENCIES", "SPEC REPOS", "EXTERNAL SOURCES", "SPEC CHECKSUMS", "PODFILE CHECKSUM", "COCOAPODS"]

def run_podfile():
    with open(lockfile_path, 'r') as a:
        lines_a = a.readlines()
        m_name = ""
        inPODS = 0
        depends_all_List = []
        depends_single_list = []
        depends_single_dics = {}
        # 搜索PODS模块内容
        for line in lines_a:
            if line.startswith("PODS:"):
                print("开始PODS:")
                inPODS = 1
            elif inPODS == 1 and line.startswith("  - "):
                # 同一层级模块可能存在subspec。需要累加
                next_m_name = get_file_name(line)
                if m_name == next_m_name:
                    continue
                else:
                    # 处理前一个模块
                    if len(m_name) > 0 and m_name not in depends_single_dics and len(depends_single_list) > 0:
                        depends_single_dics[m_name] = depends_single_list
                        

                    depends_single_list = []
                    # 处理前一个当前模块
                    update_file_name(m_name)

                    m_name = get_file_name(line)
                    # 同一模块可能存在subspec。需要累加
                    if len(m_name) > 0 and m_name in depends_single_dics:
                        depends_single_list = depends_single_dics[m_name]
            elif inPODS == 1 and line.startswith("    - "):
                name = get_file_name(line)
                if name == m_name:
                    continue
                if m_name not in list_dict:
                    list_dict[m_name] = [name]
                elif name not in list_dict[m_name]:
                    list_dict[m_name].append(name)
                # depends
                line_dep_s = "{}({})---> {}({})".format(m_name, m_name, name, name)
                # 整表single
                if line_dep_s not in depends_single_list:
                    depends_single_list.append("{}".format(line_dep_s))
                
                # 整表all
                if line_dep_s not in depends_all_List:
                    depends_all_List.append("{}".format(line_dep_s))


            elif inPODS == 1 and len(line) > 0 and line[0].isalpha():
                update_file_name(m_name)
                if m_name not in depends_single_dics and len(depends_single_list) > 0:
                    depends_single_dics[m_name] = depends_single_list
                depends_single_list = []
                break

        

        # 更新层级
        while len(list_dict.keys()) > 0:
            for key_l in list_dict.keys():
                update_value_name(key_l)

        # 遍历原字典
        list_sorted_dict = {}
        for key, value in my_dict.items():
            if value not in list_sorted_dict:
                list_sorted_dict[value] = [key]
            else:
                list_sorted_dict[value].append(key)

        # 按值从大到小排序
        sorted_keys = sorted(list_sorted_dict.keys(), reverse=True)
        # print('--------------list----------------')
        

        # 全局单个依赖表字符串
        depends_graph_singles = "" 
        # 全局层级关系列表
        depends_list_msg = ""
        # 全局依赖表字符串
        depends_all_msg = "```mermaid\n  graph LR\n"
        # 添加左侧依赖数据
        for line_info in depends_all_List:
            depends_all_msg += line_info
            depends_all_msg += "\n"

            last_open_bracket = line_info.rfind("(")
            last_close_bracket = line_info.rfind(")")

            # 提取括号内的信息
            right_name = ""
            if last_open_bracket != -1 and last_close_bracket != -1 and last_close_bracket > last_open_bracket:
                right_name = line_info[last_open_bracket + 1:last_close_bracket]
            if len(right_name) > 0 and right_name in depends_single_dics and len(depends_single_dics[right_name]) > 0:
                depends_single_dics[right_name].append(line_info)
        depends_all_msg += "\n```\n"

        depends_all_json = "let names_list = [\n"
        # 生成json index
        idx_json_total = 0

        for key in sorted_keys:
            m_list_names = list_sorted_dict[key]
            depends_list_msg += "模块层 {} ：{}\n\n".format(key, m_list_names)
            idx_json = 0
            for module_name in m_list_names:
                if module_name in depends_single_dics:
                    single_lsit = depends_single_dics[module_name]
                    single_lsit_str = "```mermaid\n  graph LR\n"
                    for single_lsit_name in single_lsit:
                        single_lsit_str += single_lsit_name
                        single_lsit_str += "\n"
                    single_lsit_str += "```\n"
                    depends_graph_singles += single_lsit_str

                # 生成json "SHMaasPassengerTravel":14,
                depends_all_json += "\"{}\":{},\n".format(module_name, idx_json_total + idx_json)
                idx_json += 1

            idx_json_total += 100

        depends_all_json += "]"
        print("全局单个依赖json生成...")
        with open("depends_graph_all_json.md", "w") as file:
            file.write(depends_all_json)


        print("全局单个依赖表生成...")
        with open("depends_graph_singles.md", "w") as file:
            file.write(depends_graph_singles)

        # 全局依赖表
        print("全局依赖表生成...")
        with open("depends_graph_all.md", "w") as file:
            file.write(depends_all_msg)
        

        # 全局层级关系列表
        print("全局层级关系列表生成...")
        with open("depends_hierarchical_relation.md", "w") as file:
            file.write(depends_list_msg)

        print("完成")


def update_file_name(m_name):
    if len(m_name) == 0:
        return
    if m_name not in my_dict and m_name not in list_dict:
        my_dict[m_name] = 1


def update_value_name(m_name):
    list_item = list_dict[m_name]
    
    del list_dict[m_name]
    tmp_list = []
    max_name = ""
    for key in list_item:
        if key in my_dict:
            # if "SCShare" == key:
            #     print('SCShare:{}'.format(my_dict[key]))
            if len(max_name) > 0 and my_dict[max_name] < my_dict[key]:
                max_name = key
            elif len(max_name) <= 0:
                max_name = key
        elif key not in tmp_list:
            tmp_list.append(key)

    # 遍历结束后处理
    if len(max_name) > 0 and len(tmp_list) > 0 and max_name not in tmp_list:
        tmp_list.append(max_name)
    elif len(max_name) > 0 and len(tmp_list) == 0:
        my_dict[m_name] = my_dict[max_name] + 1

    if len(tmp_list) > 0:
        if m_name in my_dict:
            del my_dict[m_name]
        list_dict[m_name] = tmp_list
        # if "SAICScout" == m_name:
        # print(m_name)
        # print(tmp_list)

    
    # if "SaicRouterKit" == m_name and "SaicRouterKit" in list_dict:
    #     print('--------------SaicRouterKit list ----------------')
    #     print(list_dict["SaicRouterKit"])
    #     if "SCShare" in my_dict:
    #         print('SCShare:{}'.format(my_dict["SCShare"]))
    # elif "SaicRouterKit" == m_name and "SaicRouterKit" in my_dict:
    #     print('--------------SaicRouterKit value ----------------')
    #     print(my_dict["SaicRouterKit"])


def get_file_name(line):
    line = line.strip()
    name = line.split(' ')[1]
    file_name = name.split('/')[0]
    return file_name

# 图表内容
def podfile_graph_msg(in_list_dic):
    # 打印结果
    graph_content = ""
    max_idx = 0
    for key in sorted_keys:
        if max_idx < key:
            max_idx = key + 1
        # print("值为 {} 的键：{}".format(key, list_sorted_dict[key]))
        list_names = list_sorted_dict[key]
        idx_n = 0
        content = "```mermaid\n  graph TB\n subgraph "
        content += "{}\n".format(max_idx-key)
        for name_f in list_names:
            if idx_n > 4:
                idx_n = 0
                content += "\nend\n```\n"
                graph_content += content
                content = "```mermaid\n  graph TB\n subgraph "
                content += "{}\n".format(max_idx-key)
            content += "{}({})\n".format(name_f, name_f)
            idx_n += 1
        # 在结尾插入一行文本
        content += "\nend\n```\n"
        graph_content += content


    # 打开 aa.txt 文件以读取和写入模式
    with open("graph_sh.md", "w") as file:
        file.write(graph_content)


run_podfile()
exit()


