import DrawMap
from datetime import datetime, timedelta
import googlemaps
import os
import gmplot
from dotenv import load_dotenv
from math import radians, sqrt, sin, cos, atan2, tan
import geopy.distance
from Recommendation import manhattanDistance, find_passengers_on_route, get_steps, make_recommendation

load_dotenv()

apikey = os.getenv("API_KEY")

driver1 = {'module_completed': False , 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'radius': 2.0, 'start': (43.918683857081774, -78.9601633498575), 'end':(43.94576637491968, -78.8967758730565)}
driver2 = {'module_completed': True, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=30), 'radius': 10,'start': (44.01209027944891, -78.8724033415611), 'end': (43.86969261141762, -78.85822176578796)}

passengers = [{'id': 'P1', 'has_impairments': False, 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'start': (43.90932051834358, -78.95352285076547), 'end':(43.94576637491968, -78.8967758730565)},
                {'id': 'P2','has_impairments': False, 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'start': (43.91777654339378, -78.95010120586258), 'end':(43.94576637491968, -78.8967758730565)},
                {'id': 'P3','has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=10), 'start': (43.910204697669975, -78.92758843086312),'end': (43.94375793366965, -78.89697535962003)},
                {'id': 'P4', 'has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() +timedelta(minutes=5), 'start': (43.91847108683052, -78.92376813942725),'end': (43.94375793366965, -78.89697535962003)},
                {'id': 'P5', 'has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=30), 'start': (43.94503708622363, -78.90590784532289),'end': (43.94576637491968, -78.8967758730565)},
                {'id': 'P6', 'has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=20), 'start': (43.93601547031219, -78.86591015900733),'end': (43.94375793366965, -78.89697535962003)},
                {'id': 'P7', 'has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=10), 'start': (43.95056107911553, -78.88502572397991),'end': (43.94576637491968, -78.8967758730565)},
                {'id': 'P8', 'has_impairments': False, 'departure_date': datetime.now(),'arrival_time': datetime.now() + timedelta(minutes=5), 'start': (43.96283097754987, -78.92378085910967),'end': (43.94375793366965, -78.89697535962003)}
                ]



def get_steps(start, end):
    step_loc = []
    maps = googlemaps.Client(key=os.getenv("API_KEY"))
    # get the directions from start to end
    directions_ans = maps.directions(start, end, mode="driving", departure_time=datetime.now())
    steps = directions_ans[0]['legs'][0]['steps']
    # extract the start location of each step
    for step in steps:
        step_loc.append((step['start_location']['lat'], step['start_location']['lng']))

    return step_loc

# steps = []
# steps.append(driver1['start'])
# steps.append(get_steps(driver1['start'], driver1['end']))
# steps.append(driver1['end'])

steps = get_steps(driver1['start'], driver1['end'])

print(steps)

zipSteps = zip(*steps)


gmp = gmplot.GoogleMapPlotter(steps[0][0], steps[0][1], 10, apikey=apikey)

gmp.plot(*zipSteps, edge_width=2)

gmp.draw("testMap.html")

def calcDistance(start_lat, start_long, end_lat, end_long):
   
    R = 6371.0

    lat1 = radians(start_lat)
    lon1 = radians(start_long)
    lat2 = radians(end_lat)
    lon2 = radians(end_long)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance


# print(vecDist((43.918683857081774, -78.9601633498575),(43.94576637491968, -78.8967758730565)))

print(geopy.distance.geodesic((43.918683857081774, -78.9601633498575), (43.94576637491968, -78.8967758730565)).kilometers)
print(manhattanDistance(driver1['start'][0], driver1['start'][1], driver1['end'][0], driver1['end'][1]))



def latlngToKm(coord):

    lat = coord[0]
    lng = coord[1]

    latKm = lat * 110.574
    lngKm = lng * 111.329 * cos(radians(lat))

    return (latKm, lngKm)


startLoc = latlngToKm((43.918683857081774, -78.9601633498575))
endLoc = latlngToKm((43.94576637491968, -78.8967758730565))

def vecDist(point1, point2):

    ax = point1[1]
    ay = point1[0]

    bx = point2[1]
    by = point2[0]

    xDiff = bx - ax
    yDiff = by - ay

    oppAdj = yDiff/xDiff

    theta = tan(oppAdj)

    theta = abs(theta)

    hyp = calcDistance(point1[0], point1[1], point2[0], point2[1])

    xComp = hyp*cos(theta)
    yComp = hyp*sin(theta)

    dist = sqrt(xComp**2 + yComp**2)

    return dist, theta

print(vecDist((43.918683857081774, -78.9601633498575), (43.94576637491968, -78.8967758730565)))

