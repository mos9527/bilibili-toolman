from bilibili_toolman.bilisession.common import JSONResponse
from bilibili_toolman import __version__
from bilibili_toolman.bilisession.common.submission import Submission
from bilibili_toolman.bilisession.web import BiliSession
from inquirer import text
from inquirer.shortcuts import confirm, list_input
import sys

sess = None

def print_usage_and_quit():
    print("usage : python search-topics.py 登陆凭据")
    print("        详情见 README / 准备凭据")

if len(sys.argv) > 1:
    try:
        sess = BiliSession.from_base64_string(sys.argv[1])
    except Exception as e:
        print(e)
        print_usage_and_quit()
else:
    print_usage_and_quit()

@JSONResponse
def list_topics(thread_id,limit=1000):
    return sess.get(
        "https://member.bilibili.com/x/vupre/web/topic/type",
        params={
            'type_id' : thread_id,
            'pn' : 0,
            'ps' : limit
        }
    )
from difflib import SequenceMatcher
if __name__ == "__main__":
    thread_id = input('分区 ID：')
    topics = list_topics(thread_id)["data"]["topics"]
    while True:
        keyword = input('搜索关键字：')
        def sort_by_similarity(topic):            
            return SequenceMatcher(None,keyword,topic["topic_name"]).ratio()
        topics = sorted(topics,key=sort_by_similarity,reverse=True)        
        for topic in topics[:5]:
            print('[id={topic_id}] {topic_name} : {description}'.format_map(topic))
    print(topics)