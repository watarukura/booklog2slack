# -*- coding: utf-8 -*-
import urllib
import urllib2
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
import datetime
import dateutil.tz

BOOKLOG_TIMELINE_URL="http://booklog.jp/users/<your_account>/feed"
SLACK_API_END_POINT="https://slack.com/api/chat.postMessage?"
slack_token="<your_slack_token>"
slack_channel="<your_slack_channel"
slack_username="<your_username>"
slack_pretty="1"

# https://gist.github.com/shimarin/6066511
def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

def lambda_handler(event, context):
# if __name__ == "__main__":
    # Booklogからhandslabのタイムラインを取得する。
    booklog_timeline = urllib2.urlopen(BOOKLOG_TIMELINE_URL)
    # print booklog_timeline

    soup = BeautifulSoup(booklog_timeline, "html.parser")
    # print soup

    # 「本棚に登録しました」「レビュー書きました」と本棚へのURLを取得して、
    # 2次元配列に突っ込む
    booklog_timeline_posts = []
    for item in soup.find_all("item"):
        post_content = []
        for title in item.find("title"):
            post_content.append(title + u"を本棚に登録しました")
        for link in item.find("link"):
            post_content.append(link)
        for date in item.find("dc:date"):
            dt = parse_date(date)
            # print dt
            dt_fixed = dt.strftime('%Y/%m/%d %H:%M:%S')
            # print dt_fixed
            post_content.append(dt_fixed)
        booklog_timeline_posts.append(post_content)
    # print booklog_timeline_posts

    # 「直近1時間の更新」が入っていたらSlackに飛ばす
    # lambdaで1時間おきのScheduledEventで起動するので最新のものを取得するはず
    # まあちょっと重複が出たり、取れなかったりしても死にやしないしね！
    onehour_ago = datetime.datetime.now(tz=dateutil.tz.gettz('Asia/Tokyo')) + relativedelta(hours=-1)
    onehour_ago = onehour_ago.strftime('%Y/%m/%d %H:%M:%S')
    # print onehour_ago

    fixed_posts_1hour=[]
    for fixed_timeline in booklog_timeline_posts:
        if onehour_ago < fixed_timeline[2]:
            fixed_posts_1hour.append(fixed_timeline[0] + fixed_timeline[2])
            fixed_posts_1hour.append(fixed_timeline[1])
    # print fixed_posts_1hour

    # 空だったら終わる
    if len(fixed_posts_1hour) == 0:
        # exit
        return

    for fixed_post in fixed_posts_1hour:
        query_values = {
            'token': slack_token,
            'channel': slack_channel,
            'text': fixed_post,
            'username': slack_username,
            'pretty': slack_pretty
        }

        encoded_query = urllib.urlencode(encoded_dict(query_values))
        # print encoded_query

        response = urllib2.urlopen(SLACK_API_END_POINT + encoded_query)
        # TODO: lambdaの実行ログにresponseを出力させたい。うまく行ってるかどうかわからん
        print response
