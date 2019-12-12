#Veronica Tang
#12/08/19

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
        if(tweet['place'] != None):
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
    

#################
# Some geometry #
#################

def findClosestState(tweet, cenArr):
    best = None
    closestState = None
    pos = tweet_location(tweet)
    first = True
    for state, cen in cenArr.items():
        if first:
            best = geo_distance(cen, pos)
            closestState = state
            first = False
        else:
            distance = geo_distance(cen, pos)
            if distance<best:
                best = distance
                closestState = state
    return closestState

#TODO some of this functionality will go into the data processing
#this function will change a lot to accomodate new representation of tweets
def group_tweets_by_state(tweets):
    """
    The keys of the returned dictionary are state names, and the values are
    lists of tweets that appear closer to that state center than any other.
    """
    tweets_by_state = {}
    USA = {}
    for n, s in us_states.items():
        USA[n] = find_state_center(s)#USA becomes a dictionary of all states and their respective centers
    for tweet in tweets:
        stateName = findClosestState(tweet, USA)#we need to determine which state the tweet is from.... and I'm lazy and I hate nasty code so I'm making another method
        tweets_by_state.setdefault(stateName,[]).append(tweet)#if there isn't a list already there, make one... if there is then append the tweet
    return tweets_by_state


#TODO check that Baby Veronica did the math correctly
def find_centroid(polygon):
    """Find the centroid of a polygon.
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

#TODO check that Baby Veronica did the math correctly
def find_state_center(polygons):
    """Compute the geographic center of a state, averaged over its polygons.
    The center is the average position of centroids of the polygons in 'polygons',
    weighted by the area of those polygons.
    Arguments:
    polygons -- a list of polygons

    >>> ca = find_state_center(us_states['CA'])  # California
    >>> round(latitude(ca), 5)
    37.25389
    >>> round(longitude(ca), 5)
    -119.61439

    >>> hi = find_state_center(us_states['HI'])  # Hawaii
    >>> round(latitude(hi), 5)
    20.1489
    >>> round(longitude(hi), 5)
    -156.21763
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


#################
# Miscellaneous #
#################

'''
#map the ones with location data to Tweets
coord = 0
place = 0
both = 0
for i in range(0, len(all_data)):
    tweet = data[i]
    if(tweet['place'] != None):
        place += 1
    elif(tweet['coordinates'] != None):
        both += 1
        print(tweet['coordinates'])
    if(tweet['coordinates'] != None):
        coord += 1
print(coord)
print(place)
print(both)
'''
#proves stuff only has place

##################
# Main program!! #
##################

tweets = retrieve_tweets("C:/Veronica - 2/Harvard Stuff/Sophomore Year/CS 105/CS105 Twitter/JSON Files/")

for t in tweets:
    display_tweet(t)

#plot tweets on map by bastardizing the sentiment stuff in trends
#enumerate tweets per state?
