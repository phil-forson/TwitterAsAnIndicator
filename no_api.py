import snscrape.modules.twitter as sntwitter
import pandas as pd



def get_tweets(query, limit):
    tweets = []
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if len(tweets) == limit:
            break
        else:
            tweets.append([tweet.date, tweet.user.username, tweet.content])
            
            
    df = pd. DataFrame(tweets, columns = ['Date', 'User','Tweets'])
    return df
  
