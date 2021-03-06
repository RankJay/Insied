import os
import requests
import json
import tweepy
import time
import datetime

import TwitterAPI
import ERC721Interface

APISession = TwitterAPI.DeveloperKeyConfigurations()
NFTSession = ERC721Interface
PARENT_TWEET_DETAILS = '{}'
PARENT_USER_DETAILS = '{}'
RETWEETERS_DETAILS = '{}'
SOURCE = {'Twitter from Android': 1, 'Twitter from Web': 1.3, 'Twitter from iPhone': 2.1}
VERIFIED = {'true': 1, 'false': 0}

PRECEDENCE_LIST = '{}'

def InsidrAlgorithm(instanceTweet, instanceUser):
    # global RETWEETERS_DETAILS
    # global PARENT_TWEET_DETAILS
    # global PARENT_USER_DETAILS  
    global SOURCE
    global VERIFIED

    # print(json.dumps(PARENT_TWEET_DETAILS, indent=4, sort_keys=True))
    # print(json.dumps(PARENT_USER_DETAILS, indent=4, sort_keys=True))
    # print(json.dumps(scrappedTweetMetrics, indent=4, sort_keys=True))
    # print(json.dumps(scrappedUserMetrics, indent=4, sort_keys=True))
    # instanceTweet = PARENT_TWEET_DETAILS
    # instanceUser = PARENT_USER_DETAILS

    nowTime = int(time.time())
    tweetValue = ((nowTime - instanceTweet['data'][0]['created_at']) / nowTime) * ((instanceTweet['data'][0]['organic_metrics']['like_count'] / instanceTweet['data'][0]['organic_metrics']['impression_count']) * ( (instanceTweet['data'][0]['organic_metrics']['reply_count'] / instanceUser['followers_count']) + (instanceTweet['data'][0]['organic_metrics']['retweet_count'] / instanceTweet['data'][0]['organic_metrics']['impression_count'])) * instanceTweet['data'][0]['organic_metrics']['user_profile_clicks'])
    userValue = (instanceUser['followers_count'] / (nowTime - instanceUser['data'][0]['created_at'])) * ((instanceUser['favourites_count'] + instanceUser['statuses_count']) / (nowTime - instanceUser['data'][0]['created_at'])) + (SOURCE[instanceTweet['data'][0]['source']] * VERIFIED[str(instanceUser['data'][0]['verified'])])

    return tweetValue, userValue

def Collectibles(retweetersID):
    global RETWEETERS_DETAILS

    TweetMetricValue, UserMetricValue = { RETWEETERS_DETAILS[itr]['id']: tweetMetricComponent(retweetersID[itr][0]) for itr in range(len(RETWEETERS_DETAILS)) }, { RETWEETERS_DETAILS[itr]['user']['id']: userMetricComponent(RETWEETERS_DETAILS[itr],retweetersID[itr][1]) for itr in range(len(RETWEETERS_DETAILS)) }
    # UserMetricValue = { retweeter['user']['id']: [{"created_at": retweeter['user']['created_at']}, {"screen_name": retweeter['user']['screen_name']}, {"favourites_count": retweeter['user']['favourites_count']}, {"followers_count": retweeter['user']['followers_count']}, {"location": retweeter['user']['location']}, {"statuses_count": retweeter['user']['statuses_count']}] for retweeter in RETWEETERS_DETAILS }
    # print(TweetMetricValue, UserMetricValue)

    return TweetMetricValue, UserMetricValue

def userMetricComponent(userID_Details, userID):
    global RETWEETERS_DETAILS
    global PARENT_USER_DETAILS
    PARENT_USER_DETAILS["favourites_count"] = RETWEETERS_DETAILS[0]['retweeted_status']['user']['favourites_count']
    PARENT_USER_DETAILS["followers_count"] = RETWEETERS_DETAILS[0]['retweeted_status']['user']['followers_count']
    PARENT_USER_DETAILS["friends_count"] = RETWEETERS_DETAILS[0]['retweeted_status']['user']['friends_count']
    PARENT_USER_DETAILS["listed_count"] = RETWEETERS_DETAILS[0]['retweeted_status']['user']['listed_count']
    PARENT_USER_DETAILS["statuses_count"] = RETWEETERS_DETAILS[0]['retweeted_status']['user']['statuses_count']

    unscrappedInfo = TwitterAPI.userMetrics(userID)
    scrappedValues = unscrappedInfo
    # scrappedValues = [{"created_at": userID_Details['user']['created_at'], "name": userID_Details['user']['name'], "username": userID_Details['user']['screen_name'], "public_metrics": {"favourites_count": userID_Details['user']['favourites_count'], "followers_count": userID_Details['user']['followers_count'], "friends_count": userID_Details['user']['friends_count'], "listed_count": userID_Details['user']['listed_count'], "statuses_count": userID_Details['user']['statuses_count']}}]
    
    return scrappedValues

def tweetMetricComponent(tweetID):
    global RETWEETERS_DETAILS

    unscrappedInfo = TwitterAPI.tweetMetrics(tweetID)
    scrappedValues = unscrappedInfo
    # scrappedValues = [{"author_id": unscrappedInfo['data'][0]['author_id'], "created_at": unscrappedInfo['data'][0]['created_at'], "source": unscrappedInfo['data'][0]['source']}]

    return scrappedValues




class Utility():

    def __init__(self, PARENT_TWEET_ID):
        self.PARENT_TWEET_ID = PARENT_TWEET_ID


    def parentDetailsFromTwitterAPI(self):
        global PARENT_USER_DETAILS
        global PARENT_TWEET_DETAILS

        PARENT_TWEET_DETAILS = TwitterAPI.tweetMetrics(self.PARENT_TWEET_ID)
        PARENT_USER_DETAILS = TwitterAPI.userMetrics(PARENT_TWEET_DETAILS['data'][0]['author_id'])
        # print(json.dumps(PARENT_TWEET_DETAILS, indent=4, sort_keys=True))
        # print(json.dumps(PARENT_TWEET_DETAILS, indent=4, sort_keys=True))

    
    def retweetersScraping(self):
        global RETWEETERS_DETAILS

        tweet_id = self.PARENT_TWEET_ID
        key = APISession.consumer_key
        secret = APISession.consumer_secret

        authenticationURL = "https://api.twitter.com/oauth2/token"
        data = {'grant_type': 'client_credentials'}
        authenticationResponse = requests.post(authenticationURL, auth=(key, secret), data=data)
        bearerToken = authenticationResponse.json()['access_token']


        url = 'https://api.twitter.com/1.1/statuses/retweets/%s.json?count=1' % tweet_id
        headers = {'Authorization': 'Bearer %s' % bearerToken}
        retweetsResponse = requests.get(url, headers=headers)


        retweets = retweetsResponse.json()
        RETWEETERS_DETAILS = retweets
        retweeters = [[r['id'], r['user']['id'], r['user']['screen_name']] for r in retweets]

        # with open('retweeters-ids-%s.txt' % (tweet_id), 'w') as fileWriter:
        #     for r, i in retweeters:
        #         fileWriter.write('%s,%s\n' % (r, i))

        return retweeters
    

    def ERC721Scrapper(self, platform, itemID, assetContractAddress):
        ERC721Parser = NFTSession.ERC721AssetInfoClient(itemID)
        NFTMetric = '{}'

        if platform.lower() == 'rarible' and assetContractAddress.lower() == 'null':
            NFTMetric = ERC721Parser.RaribleFetchingSchema()
        elif platform.lower() == 'foundation' and assetContractAddress.lower() == 'null':
            NFTMetric = ERC721Parser.FoundationAppFetchingSchema()
        else:
            NFTMetric = ERC721Parser.OpenSeaFetchingSchema(assetContractAddress)

        return NFTMetric




def createInstance(PARENT_TWEET_ID):
    utilityInstance = Utility(PARENT_TWEET_ID)
    utilityInstance.parentDetailsFromTwitterAPI()
    scrappedTweetMetrics, scrappedUserMetrics = Collectibles(utilityInstance.retweetersScraping())

    InsidrAlgorithm(scrappedTweetMetrics, scrappedUserMetrics)

    # print(json.dumps(PARENT_USER_DETAILS, indent=4, sort_keys=True))
    # print(json.dumps(PARENT_TWEET_DETAILS, indent=4, sort_keys=True))

createInstance(1404663795616677889)
