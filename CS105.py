#Veronica Tang
#12/08/19

import json
from data import word_sentiments, load_tweets
from datetime import datetime
from geo import us_states, geo_distance, make_position, longitude, latitude
from maps import draw_state, draw_name, draw_dot, wait
from string import ascii_letters
from ucb import main, trace, interact, log_current_line


####################
# Parsing JSON data#
####################
'''
TO DO - write a function that processes the JSON objects and turns them into tweets
for now, just check if either "place" not = null or "coord" not = null
if so, make tweet - handle, content, state, coord
take "full_name" field and extract the state abreviation for state
if "coordinates" not null, take exact long and lat, assign to state based on centroids
else if place not null, find centroid of "bounding box" and assign that to long/lat
add tweets to list
return list

Note that we unfortunately cannot use the loctions of the users since this seems like
a field they fill out themselves - it does not always have the same information and is
not formatted in any particular (or sometimes) understandable way
'''
#to manually find viable tweets: place": {"id"

##########
# Tweets #
##########

def make_tweet(user, text, state, lat, lon):
    return {'user': user, 'text': text, 'state': state, 'latitude': lat, 'longitude': lon}

def tweet_user(user):
    return tweet['user']

def tweet_text(tweet):
    return tweet['text']

def tweet_state(tweet):
    return tweet['state']

def tweet_location(tweet):
    return make_position(tweet['latitude'], tweet['longitude'])


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
    The center is the average position of centroids of the polygons in polygons,
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


##################
# Main program!! #
##################

#plot tweets on map by bastardizing the sentiment stuff in trends
#enumerate tweets per state?
