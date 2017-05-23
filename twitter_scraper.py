import json, random, sys, time, traceback, twitter
data = json.load(open('twitter_creds.json'))
api = twitter.Api(**data)

username = sys.argv[1]
max_id = None

ts = []
ys = []
for i in range(20):
    tweets = api.GetUserTimeline(screen_name=username, max_id=max_id)
    for tweet in tweets:
        if not tweet.retweeted_status:
            print(tweet.created_at_in_seconds, tweet.retweet_count, tweet.favorite_count)
            ts.append(tweet.created_at_in_seconds)
            ys.append(tweet.retweet_count)
    max_id = tweets[-1].id - 1

from matplotlib import pyplot
pyplot.plot(ts, ys)
pyplot.show()
