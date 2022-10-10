import threading
import urllib.request
import urllib.parse
import http.cookiejar
import requests
import json


# get login cookie
# @return An authentic HTTP Headers,
def get_auth_header(login_name, password):
    token = {}
    cookie = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
    opener.open(
        'https://www.ulearning.cn/umooc/user/login.do',
        urllib.parse.urlencode({
            "name": login_name,
            "passwd": password
        }).encode("UTF-8")
    )
    for it in cookie:
        token[it.name] = urllib.parse.unquote(it.value)
    auth_header = {
        'UA-AUTHORIZATION': token['token'],
        'AUTHORIZATION': token['AUTHORIZATION'],
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.100 Safari/537.36 '
    }
    return auth_header


# 2 implementation functions down below
# func 1 : get course_list
def get_course_list(auth_header):
    res = requests.get(
        headers=auth_header,
        url='https://courseapi.ulearning.cn/courses/students?keyword=&publishStatus=1&type=1&pn=1&ps=15&lang=zh',
    )
    return json.loads(res.content.decode("UTF-8"))['courseList']


# func 2 : send 'likes' to all members in the comment area
def likes(auth_header, course_id_str, discussion_id_str):
    pageNum = "1"
    query_url = "https://courseapi.ulearning.cn/topic/topicInfo?pn=#PAGE_NUM#&ps=20&ocId=#COURSE_ID#&discussionId" \
                "=#DISCUSSION_ID#&teacherId=&classId=&orderType=&mine=false&keyword= ".replace("#COURSE_ID#", course_id_str).replace("#DISCUSSION_ID#", discussion_id_str)
    # get basic page INFO
    res = json.loads(requests.get(
        headers=auth_header,
        url=query_url.replace(
            "#PAGE_NUM#", pageNum
        )
    ).content.decode('UTF-8'))['result']
    comment_num = res['pageInfo']['total']
    page_size = res['pageInfo']['pageSize']
    for pageN in range(0, int(comment_num / page_size)):
        # get comment_id
        cur_url = query_url.replace("#PAGE_NUM#", str(pageN))
        student_list = json.loads(requests.get(
            headers=auth_header,
            url=cur_url
        ).content.decode('UTF-8'))['result']['pageInfo']['list']
        # handled with multi-thread
        threading.Thread(target=post_to_list, args=(auth_header, student_list)).start()


# aux func for likes()
def post_to_list(auth_header, student_list):
    post_url = "https://courseapi.ulearning.cn/post/agreeRating?postId=#POST_ID#&exist=1&rating=0"
    for student in student_list:
        # send 'like' to certain stu
        post_res = requests.post(
            headers=auth_header,
            url=post_url.replace("#POST_ID#", str(student['postID']))
        )
        print("postID:%s ---> %s" % (student['postID'], post_res.status_code))


# example for using login(login_name, password)
if __name__ == "__main__":
    # only required 2 args:
    LOGIN_NAME = ""
    PASSWORD = ""
    ah = get_auth_header(LOGIN_NAME, PASSWORD)

    # Case 1:
    # get course_id_list, each course may have multiple 'discussion_id's corresponding to different columns
    for course in get_course_list(ah):
        print("course_id: %s" % course['id'])

    # Case 2:
    # Suppose we've got a course_id
    # now get 'discussion_id's , send 'like's to all of them!
    COURSE_ID = ""
    discussion_list = json.loads(requests.get(
        headers=ah,
        url="https://courseapi.ulearning.cn/"
            "forum/studentForumList?ocId=#COURSE_ID#&pn=1&ps=10&lang=zh".replace("#COURSE_ID#", COURSE_ID)
    ).content.decode('UTF-8'))['result']['studentForumDiscussionList']
    for disc in discussion_list:
        likes(
            auth_header=ah,
            course_id_str=COURSE_ID,
            discussion_id_str=str(disc['discussionId'])
        )
