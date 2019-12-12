#Veronica Tang
#12/12/19

import os
import json
import sys
from data import word_sentiments, load_tweets
from datetime import datetime
from geo import us_states, geo_distance, make_position, longitude, latitude
from maps import draw_state, draw_name, draw_dot, wait
from string import ascii_letters
from ucb import main, trace, interact, log_current_line


####################
# Parsing JSON data#
####################

def retrieve_tweets(path):
    """
    Reads in and processes all JSON data in folder given by file path.
    Filters out Tweets without location data and converts remaining Tweets
    into the preferred format.
    """
    all_data = []
    for filename in os.listdir(path):
        with open(path + filename) as read_file:
            data = json.load(read_file)
            all_data = all_data + data
    tweets = []        
    #map the ones with location data to Tweets
    for i in range(0, len(all_data)):
        tweet = data[i]
        #if time would like to accomodate tweet['place']['place_type'] == 'admin', but that means making a dictionary of full state name to state abbreviation
        if(tweet['place'] != None and tweet['place']['country_code'] == 'US' and tweet['place']['place_type'] == 'city'):
            user = tweet['user']['screen_name']
            non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
            text = (tweet['text']).translate(non_bmp_map) #to deal with emojis
            state = tweet['place']['full_name'][-2:]
            polygon = [] #want to construct a polygon that is a list of positions, with first = last
            for coord in tweet['place']['bounding_box']['coordinates'][0]:
                polygon.append(make_position(coord[1], coord[0]))
            first_coord = tweet['place']['bounding_box']['coordinates'][0][0]
            polygon.append(make_position(first_coord[1], first_coord[0]))
            position = find_centroid(polygon) #find the centroid of the bounding box
            tweets.append(make_tweet(user, text, state, position))
            #display_tweet(make_tweet(user, text, state, position))
    #print(len(tweets))
    return tweets


##########
# Tweets #
##########

def make_tweet(user, text, state, position):
    return {'user': user, 'text': text, 'state': state, 'position': position}

def tweet_user(tweet):
    return tweet['user']

def tweet_text(tweet):
    return tweet['text']

def tweet_state(tweet):
    return tweet['state']

def tweet_location(tweet):
    return tweet['position']

def display_tweet(tweet):
    print('User: ' + tweet_user(tweet) + ', Text: ' + tweet_text(tweet) + ', State: ' + tweet_state(tweet) + ', Tweet Location: ' + str(tweet_location(tweet)[0]) + ', ' + str(tweet_location(tweet)[1]) + '\n')
    
def group_tweets_by_state(tweets):
    """
    The keys of the returned dictionary are state names, and the values are
    lists of tweets from that state.
    """
    tweets_by_state = {}
    for tweet in tweets:
        tweets_by_state.setdefault(tweet_state(tweet),[]).append(tweet)
    return tweets_by_state

def print_num_tweets_per_state(tweets):
    #num = 0
    state_names = us_states.keys()
    tweets_by_state = group_tweets_by_state(tweets)
    for s in state_names:
        if s in tweets_by_state.keys():
            #num += len(tweets_by_state[s])
            print(s + ': ' + str(len(tweets_by_state[s])))
        else:
            print(s + ': 0')
    #print(num)

def filter_tweets(tweets, term):
    relevant_tweets = []
    for tweet in tweets:
        if(term.lower() in tweet_text(tweet).lower()):
            relevant_tweets.append(tweet)
    return relevant_tweets
            

######################
# "Sentiment" values #
######################

def tweet_words(tweet):
    return extract_words(tweet_text(tweet))

def next_not_ASCII(i, text):
    for index in range(i, len(text)):
        if not(text[index] in ascii_letters):
            return index
    return len(text)

def extract_words(text):
    """
    Returns the words in a tweet, not including punctuation and numbers.
    Split on whitespace and non-ascii characters
    """
    indexArr = []
    asciiSection = text[0] in ascii_letters
    if(asciiSection):
        indexArr.append(0)
    i = 0
    while(i < len(text)):
        if (text[i] in ascii_letters) and not(asciiSection):
            indexArr.append(i)
            asciiSection = True
        elif not(text[i] in ascii_letters) and asciiSection:
            asciiSection = False
        i = i + 1
    arr = []
    if(len(indexArr) == 0):
        if(asciiSection == True):
            arr.append(text)
        return arr
    m = 0
    x = indexArr[m]
    while(x < len(text) and m < len(indexArr)):
        arr.append(text[x: next_not_ASCII(x, text)])
        if(m < len(indexArr) - 1):
            m = m + 1
            x = indexArr[m]
        else:
            break
    return arr

def make_sentiment(value):
    """
    Returns a sentiment, which represents a value that may not exist.
    Assumes that sentiments range from -1 to 1.
    """
    assert value is None or (value >= -1 and value <= 1), 'Illegal value'
    return value

def has_sentiment(s):
    return s is not None

def sentiment_value(s):
    assert has_sentiment(s), 'No sentiment value'
    return s  

def get_word_sentiment(word):
    return make_sentiment(word_sentiments.get(word))

def analyze_tweet_sentiment(tweet):
    """
    Returns a sentiment representing the degree of positive or negative
    sentiment in the given tweet by averaging over all the words in the tweet
    that have a sentiment value. Returns None if no words in the tweet has
    a sentiment value.
    """
    average_sentiment = make_sentiment(None)
    arr_words = tweet_words(tweet)
    total_sentiment = 0
    num_sentiments = 0
    for w in arr_words:
        sentiment = get_word_sentiment(w)
        if has_sentiment(sentiment):
            total_sentiment += sentiment_value(sentiment)
            num_sentiments += 1
    if(total_sentiment == 0):
        return average_sentiment
    average = total_sentiment/num_sentiments
    average_sentiment = make_sentiment(average)
    return average_sentiment

def average_sentiments(tweets_by_state):
    """
    Calculates the average sentiment of the states by averaging over all
    the tweets from each state. Returns the result as a dictionary from state
    names to average sentiment values.
    """
    averaged_state_sentiments = {}
    totalSentiment = 0
    count = 0
    for state, tweets in tweets_by_state.items():
        for tweet in tweets:
            sentiment = analyze_tweet_sentiment(tweet)
            if not ((sentiment == 0) or (sentiment == None)):
                totalSentiment += sentiment
                count += 1
        if not(totalSentiment == 0):
            averaged_state_sentiments[state] = (totalSentiment/count)
        totalSentiment = 0
        count = 0
    return averaged_state_sentiments


#################
# Some Geometry #
#################

def find_centroid(polygon):
    """
    Finds the centroid of a polygon.
    http://en.wikipedia.org/wiki/Centroid#Centroid_of_polygon
    polygon -- A list of positions, in which the first and last are the same
    Returns: 3 numbers; centroid latitude, centroid longitude, and polygon area
    """
    area = 0
    x = 0
    y = 0
    for index in range (0, len(polygon)-1):
        area += (latitude(polygon[index]) * longitude(polygon[index + 1])) - (latitude(polygon[index + 1]) * longitude(polygon[index]))
    if(area == 0):
        return latitude(polygon[0]), longitude(polygon[0]),0
    for index in range (0, len(polygon)-1):
        x += (latitude(polygon[index]) + latitude(polygon[index + 1])) * ((latitude(polygon[index])*longitude(polygon[index + 1])) - (latitude(polygon[index + 1])*longitude(polygon[index])))
        y += (longitude(polygon[index]) + longitude(polygon[index + 1])) * ((latitude(polygon[index])*longitude(polygon[index + 1])) - (latitude(polygon[index + 1])*longitude(polygon[index])))
    area = area/2
    x = x/(6*area)
    y = y/(6*area)
    return (x, y, abs(area))

def find_state_center(polygons):
    """
    Computes the geographic center of a state, averaged over its polygons.
    The center is the average position of centroids of the polygons in 'polygons',
    weighted by the area of those polygons.
    Arguments: polygons -- a list of polygons
    """
    cenArea = []
    for index in range(len(polygons)):
        cenArea.append(find_centroid(polygons[index]))
    cenx = 0
    ceny = 0
    totalArea = 0
    for i in range (0, len(cenArea)):
        cenx += (cenArea[i])[0] * (cenArea[i])[2]
        ceny += (cenArea[i])[1] * (cenArea[i])[2]
        totalArea += (cenArea[i])[2]
    return make_position(cenx/totalArea, ceny/totalArea)

############
# Graphics #
############
# draw_centered_map, draw_state_sentiments, and part of draw_map_for_query taken from UC Berkeley's starter code

def draw_centered_map(center_state='TX', n=10):
    """Draw the n states closest to center_state."""
    us_centers = {n: find_state_center(s) for n, s in us_states.items()}
    center = us_centers[center_state.upper()]
    dist_from_center = lambda name: geo_distance(center, us_centers[name])
    for name in sorted(us_states.keys(), key=dist_from_center)[:int(n)]:
        draw_state(us_states[name])
        draw_name(name, us_centers[name])
    draw_dot(center, 1, 10)  # Mark the center state with a red dot
    wait()

def draw_state_sentiments(state_sentiments):
    """Draw all U.S. states in colors corresponding to their sentiment value.

    Unknown state names are ignored; states without values are colored grey.

    state_sentiments -- A dictionary from state strings to sentiment values
    """
    for name, shapes in us_states.items():
        sentiment = state_sentiments.get(name, None)
        draw_state(shapes, sentiment)
    for name, shapes in us_states.items():
        center = find_state_center(shapes)
        if center is not None:
            draw_name(name, center)

def draw_map_for_query(tweets, term='my job'):
    """
    Draw the sentiment map corresponding to the tweets that contain term.
    """
    relevant_tweets = filter_tweets(tweets, term)
    tweets_by_state = group_tweets_by_state(relevant_tweets)
    state_sentiments = average_sentiments(tweets_by_state)
    draw_state_sentiments(state_sentiments)
    for tweet in relevant_tweets:
        s = analyze_tweet_sentiment(tweet)
        if has_sentiment(s):
            display_tweet(tweet)
            draw_dot(tweet_location(tweet), sentiment_value(s))
    wait()


##################
# Main program!! #
##################

tweets = retrieve_tweets("C:/Veronica - 2/Harvard Stuff/Sophomore Year/CS 105/CS105 Twitter/JSON Files/")

'''
for t in tweets:
    display_tweet(t)
   
print_num_tweets_per_state(tweets)
'''
draw_map_for_query(tweets, 'trump')
