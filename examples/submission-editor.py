# -*- coding: utf-8 -*-
"""API 实例 - 稿件修改

附加依赖：

    inquirer

除【删除稿件】限 PC端 API 外，其余 API 不限版本,
"""

from inquirer.shortcuts import confirm, list_input
from bilibili_toolman import __version__
from bilibili_toolman.bilisession.common.submission import Submission
from bilibili_toolman.bilisession.client import BiliSession
from inquirer import text
import sys

sess = None


def print_usage_and_quit():
    print("usage : python submission-editor.py 登陆凭据")
    print("        详情见 README / 准备凭据")


if len(sys.argv) > 1:
    try:
        sess = BiliSession.from_base64_string(sys.argv[1])
    except Exception as e:
        print(e)
        print_usage_and_quit()
else:
    print_usage_and_quit()


def to_yymmdd(ts):
    from datetime import datetime

    ts = datetime.fromtimestamp(ts)
    return ts.strftime("%Y/%m/%d %H:%M:%S")


def add_indent(s: str, indent):
    return "".join("%s%s\n" % (indent, i) for i in s.split("\n"))


def build_dict(by_key, from_list: list):
    return {getattr(i, by_key): i for i in from_list}


def register(key, calltable):
    def wrapper(func):
        calltable[key] = func
        return func

    return wrapper


def select_and_execute(from_calltable):
    choices = {**from_calltable, "退出": lambda: False}
    choice = list_input("", choices=choices)
    try:
        result = choices[choice]()
    except Exception as e:
        print("[!] %s" % e)
        result = False
    except KeyboardInterrupt:
        result = False
    return result == None or result


routines = {}


@register("选择作品", routines)
def main_entrance():
    bvid = text("BVid 号 [留空进入选择页面]")
    if not bvid:
        subs = sess.ListSubmissions(limit=10)
        bvid = list_input("选择视频", choices=[f"{sub.title}" for sub in subs])
        bvid = build_dict("title", subs)[bvid].bvid
    sub = sess.ViewSubmission(bvid)
    print(
        f"""[-] {sub.title}：
        - BV号     ： {sub.bvid}
        - 状态     :  {sub.state_desc}
        - 上传时间  :  {to_yymmdd(sub.stat['ptime'])}
        - 标签     :  {','.join(sub.tags)}
        - 活动     :  {sub.topic_name} ({sub.topic_id})
        - 描述     :  
        {add_indent(sub.description,'      ')[3:]}"""
    )
    routines = {}

    @register("编辑描述", routines)
    def edit_title():
        sub.description = text("输入新标题")

    @register("编辑标题", routines)
    def edit_title():
        sub.title = text("输入新标题")

    @register("编辑标签", routines)
    def edit_tags():
        new_tags = text("输入新标签（逗号隔开）")
        sub.tags = new_tags.split(",")

    @register("编辑话题", routines)
    def edit_topics():
        topic_id = text("话题 ID (见 search-topics.py)")
        topic_name = text("话题名 (见 search-topics.py)")
        sub.topic_id = topic_id
        sub.topic_name = topic_name
        if not topic_name in sub.tags:
            sub.tags.add(topic_name)

    @register("编辑子视频", routines)
    def edit_sub_archive():
        routines = {}

        @register("修改已有子视频", routines)
        def select_by_sub():
            v = list_input("选择子视频", choices=[v for v in sub.videos])
            routines = {}

            @register("修改子视频标题", routines)
            def edit_sub_title():
                v.title = text("新标题")

            @register("修改子视频结点", routines)
            def overwrite_sub_video():
                ep = text("新视频结点")
                v.video_endpoint = ep

            @register("上传并修改子视频内容", routines)
            def upload_and_overwrite_sub_video():
                path = text("新视频路径")
                ep, bid = sess.UploadVideo(path)
                print("新结点：", ep)
                if bid:
                    v.biz_id = bid
                v.video_endpoint = ep

            while select_and_execute(routines):
                print(v)
            return True

        @register("创建新子视频", routines)
        def create_sub():
            routines = {}

            @register("以结点创建", routines)
            def overwrite_sub_video():
                sub.videos.append(
                    {
                        "filename": text("新视频结点"),
                        "title": text("新视频标题"),
                    }
                )
                return True

            @register("上传并修改子视频内容", routines)
            def upload_and_overwrite_sub_video():
                path = text("新视频路径")
                ep, bid = sess.UploadVideo(path)
                print("新结点：", ep)
                sub.videos.append(
                    {"title": text("新视频标题"), "filename": ep, "biz_id": bid}
                )
                return True

            while select_and_execute(routines):
                pass
            return True

        while select_and_execute(routines):
            pass

    @register("提交更改", routines)
    def submit_sub_video():
        print(sess.EditSubmission(sub))
        return False

    @register("删除作品", routines)
    def delete_archive():
        assert type(sess) == BiliSession, "限 PC 客户端"
        if confirm("该操作不可逆，确定？"):
            print(sess.DeleteArchive(sub.bvid))
            return False

    while select_and_execute(routines):
        pass

@register("删除所有稿件", routines)
def hiroshima():
    assert type(sess) == BiliSession, "限 PC 客户端"
    subs = sess.ListSubmissions()    
    if confirm("该操作不可逆，确定？") and confirm("【所有稿件】将被删除，并扣除相关硬币，确定？"):
        for sub in subs:
            print('删除 - %s' % sub.title)
            sess.DeleteArchive(sub.bvid)  

if __name__ == "__main__":
    while select_and_execute(routines):
        pass
