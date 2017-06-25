import tweepy 
import sys
import os
import logging
import argparse
import jsonpickle
import json
import re

with open(os.path.join(os.environ['HOME'],'.twitterapi.key')) as apikey:
	API_KEY = apikey.readline().rstrip()

with open(os.path.join(os.environ['HOME'],'.twitterapi.sec')) as apisec:
	API_SECRET = apisec.readline().rstrip()

logger = logging.getLogger(name=__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fh = logging.FileHandler('./log/fatweets.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


auth = tweepy.AppAuthHandler(API_KEY, API_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, 
	wait_on_rate_limit_notify=True)


#search_query = '#nbafreeagency'  # this is what we're searching for
#max_tweets = 1000 # Some arbitrary large number
#tweets_per_query = 100  # this is the max the API permits
#outfile = './data/tweets/freeagency_tweets.txt' # We'll store the tweets in a text file.


# If results from a specific ID onwards are reqd, set since_id to that ID.
# else default to no lower limit, go as far back as API allows
#since_id = None

# If results only below a specific ID are, set max_id to that ID.
# else default to no upper limit, start from the most recent tweet matching the search query.
#max_id = -1L



def get_tweets(search_query, outfile, max_tweets=100000, tweets_per_query=100, 
	most_recent_only=True, get_unseen_tweets=False):
	tweet_count = 0
	logger.info("Downloading max {0} tweets".format(max_tweets))
	since_id = None
	max_id=-1		
	if  os.path.exists(outfile):
		with open(outfile, 'r') as f:
			if most_recent_only:
				twt = f.readline().rstrip()
				try:
					twt = json.loads(twt)
					since_id = int(twt['id'])
					logger.info('Restarting query from id: ' + str(since_id))
				except Exception as e:
					logger.warning("Couldn't read from {} (probably empty): {}".format(outfile, e))

			if get_unseen_tweets:
				for line in f:
					pass
				try:
					lasttwt = json.loads(line)
					max_id = int(lasttwt['id'])
					logger.info('Fetching previously unseen tweets up to id:' + str(max_id))
				except Exception as e:
					logger.warning("""Couldn't read last line from {} 
						(probably empty): {}""".format(outfile, e))

	
	with open(outfile, 'a') as f:
		while tweet_count < max_tweets:
			try:
				if max_id <= 0:
					if (not since_id):
						new_tweets = api.search(q=search_query, count=tweets_per_query)
					else:
						new_tweets = api.search(q=search_query, count=tweets_per_query,
							since_id=since_id)
				else:
					if not since_id:
						new_tweets = api.search(q=search_query, count=tweets_per_query,
								max_id=str(max_id - 1))
					else:
						new_tweets = api.search(q=search_query, count=tweets_per_query,
								max_id=str(max_id - 1),
								since_id=since_id)
				if not new_tweets:
					logger.info("No more tweets found")
					break
				for tweet in new_tweets:
					f.write(jsonpickle.encode(tweet._json, unpicklable=False) +
						'\n')
				tweet_count += len(new_tweets)
				logger.info("Downloaded {0} tweets".format(tweet_count))
				max_id = new_tweets[-1].id
			except tweepy.TweepError as e:
				logger.error('Error :' + str(e))
				break

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='make a twitter search request')
	parser.add_argument('--query', metavar='query', type=str,
		nargs=1, help='query string (hashtag or free text)')
	parser.add_argument('--out', metavar='outputfile', type=str,
		nargs=1, help='output textfile to append or overwrite')
	args = parser.parse_args()
	query = args.query
	outputfile = args.out[0]
	logger.info('Requesting tweets answering the following query: ' + query[0])
	#outputfile = re.sub('[^0-9a-zA-Z]+', '', query[0]) + '_tweets.txt'
	outputfile = os.path.join('data', 'tweets', outputfile)
	get_tweets(search_query=query, outfile=outputfile)


