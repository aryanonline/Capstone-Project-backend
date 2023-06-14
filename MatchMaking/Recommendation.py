import googlemaps
import os
from datetime import datetime, timedelta
from .DrawMap import DrawMap
from math import radians, sin, cos, sqrt, atan2
import gmplot
import itertools

from dotenv import load_dotenv

load_dotenv()


# def manhattanDistance(start_lat, start_long, end_lat, end_long):
def manhattanDistance(start, end):
    R = 6371.0

    lat1 = radians(start[0])
    lon1 = radians(start[1])
    lat2 = radians(end[0])
    lon2 = radians(end[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance


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


apikey = os.getenv("API_KEY")
gmap = googlemaps.Client(key=apikey)


def getPoints(start, end):  # TODO: Need to refactor this function

    y1 = start[0]  # lat
    x1 = start[1]  # long
    y2 = end[0]  # lat
    x2 = end[1]  # long

    points = []
    points.append((start))

    if (x2 == x1):  # line is vertical
        slope = "undef"
    else:
        rise = (y2 - y1)
        run = (x2 - x1)
        slope = rise / run

    # print(slope, " ", x1)

    if (slope == 0 and x2 > x1):  # horizontal line - left to right
        newX = x1
        while (newX < x2):
            newX += 0.0020000000000
            if (newX < x2):
                points.append((y1, newX))
        # points.append(end)
        return points

    if (slope == 0 and x2 < x1):  # horizontal line - right to left
        newX = x1
        while (newX > x2):
            newX -= 0.0020000000000
            if (newX > x2):
                points.append((y1, newX))
        # points.append(end)
        return points

    if (slope == "undef" and y2 > y1):  # vertical line - upwards
        newY = y1
        while (newY < y2):
            newY += 0.0020000000000
            if (newY < y2):
                points.append((newY, x1))
        # points.append(end)
        return points

    if (slope == "undef" and y2 < y1):  # vertical line - downwards
        newY = y1
        while (newY > y2):
            newY -= 0.0020000000000
            if (newY > y2):
                points.append((newY, x1))
        # points.append(end)
        return points

    if (slope > 0 and x2 > x1):  # line like "/" - going from bot-left to top-right
        newY = y1
        newX = x1

        while (newX < x2):
            newX += 0.0020000000000
            if (newX < x2):
                newY += (rise * 0.002) / run

                points.append((newY, newX))

        # points.append(end)
        return points

    if (slope > 0 and x2 < x1):  # line like "/" - going from top-right to bot-left
        newY = y1
        newX = x1

        while (newX > x2):
            newX -= 0.0020000000000
            if (newX > x2):
                newY -= (rise * 0.002) / run
                points.append((newY, newX))

        # points.append(end)
        return points

    if (slope < 0 and x2 > x1):  # line like "\" going downhill
        newX = x1
        newY = y1

        while (newX < x2):
            newX += 0.0020000000000
            if (newX < x2):
                newY -= -1 * (rise * 0.002) / run
                points.append((newY, newX))

        # points.append(end)
        return points

    if (slope < 0 and x2 < x1):  # line like "\" going uphill
        newX = x1
        newY = y1

        while (newX > x2):
            newX -= 0.0020000000000
            if (newX > x2):
                newY += -1 * (rise * 0.002) / run
                points.append((newY, newX))
        # points.append(end)
        return points

    return "none"


def getAllPoints(steps):
    totalSteps = len(steps)

    totalPoints = []

    for i, step in enumerate(steps):

        if (i > totalSteps - 2):
            break

        totalPoints += getPoints(steps[i], steps[i + 1])

    return totalPoints


def make_recommendation(driver, passengers):
    steps = get_steps(driver['start'], driver['end'])

    routePoints = getAllPoints(steps)

    recommendedPass = []
    currPass = passengers

    # print(currPass)

    for point in routePoints:
        for passenger in currPass:
            if ('beingScooped' not in passenger.keys()):
                dist = manhattanDistance(passenger['start'], point)
                # print(dist, " ", passenger['id'])
                if (dist <= driver['radius']):
                    recommendedPass.append(passenger)
                    passenger['beingScooped'] = 1

    return recommendedPass


def find_passengers_on_route(driver, passengers):
    # filter passengers based on depature date then filter passenger based on arrival time
    filter_passengers = []
    new_filter_passengers = []
    for passenger in passengers:
        if passenger['departure_date'] == driver['departure_date'] and passenger['arrival_time'] >= driver[
            "arrival_time"] and passenger['end'] == driver['end']:
            filter_passengers.append(passenger)
    # If driver is not trained filter passengers for only passengers that do not have impairments
    if not driver['module_completed']:
        for passenger in filter_passengers:
            if not passenger['has_impairments']:
                new_filter_passengers.append(passenger)

    # all_steps = get_steps((str(driver['start'][0]) + ',' + str(driver['start'][1])), (str(driver['end'][0]) + ',' + str(driver['end'][1])))

    if len(new_filter_passengers) == 0:
        # print(filter_passengers)
        return make_recommendation(driver, filter_passengers)
    else:
        # print(new_filter_passengers)
        return make_recommendation(driver, new_filter_passengers)


def driveDist(start, end):
    dirAPI = gmap.directions(start, end)

    dist = dirAPI[0]['legs'][0]['distance']['value']

    return dist


def optimalOrder(recommendedPassengers, driver):
    best = None
    shortestDist = None

    for permutation in itertools.permutations(recommendedPassengers.keys()):
        routeDist = 0
        prevLoc = driver['start']

        for passengerName in permutation:
            routeDist += driveDist(prevLoc, recommendedPassengers[passengerName])
            prevLoc = recommendedPassengers[passengerName]
            routeDist += driveDist(recommendedPassengers[passengerName], driver['end'])

        if shortestDist is None or routeDist < shortestDist:
            shortestDist = routeDist
            best = permutation

    # ordered = [recommendedPassengers[i][2] for i in best]

    return best


if __name__ == "__main__":
    time = datetime.now()
    driver1 = {'module_completed': False, 'departure_date': datetime.now(),
               'arrival_time': datetime.now() + timedelta(minutes=30), 'radius': 1.0,
               'start': (43.918683857081774, -78.9601633498575), 'end': (43.94576637491968, -78.8967758730565)}
    driver2 = {'module_completed': True, 'departure_date': datetime.now(),
               'arrival_time': datetime.now() + timedelta(minutes=30), 'radius': 10,
               'start': (44.01209027944891, -78.8724033415611), 'end': (43.86969261141762, -78.85822176578796)}

    passengers = [{'id': 'P1', 'has_impairments': False, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.90932051834358, -78.95352285076547), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P2', 'has_impairments': False, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.91777654339378, -78.95010120586258), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P3', 'has_impairments': False, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.910204697669975, -78.92758843086312), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P4', 'has_impairments': False, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.91847108683052, -78.92376813942725), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P5', 'has_impairments': True, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.94455562658264, -78.90559288780365), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P6', 'has_impairments': True, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.93601547031219, -78.86591015900733), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P7', 'has_impairments': True, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.95056107911553, -78.88502572397991), 'end': (43.94576637491968, -78.8967758730565)},
                  {'id': 'P8', 'has_impairments': True, 'departure_date': datetime.now(),
                   'arrival_time': datetime.now() + timedelta(minutes=30),
                   'start': (43.96283097754987, -78.92378085910967), 'end': (43.94576637491968, -78.8967758730565)}
                  ]

    # a = getPoints((43.910204697669975, -78.92758843086312), (43.91777654339378, -78.95010120586258))

    # steps = get_steps(driver1['start'], driver1['end'])

    # routePoints = getAllPoints(steps)

    # filteredPass = filterPassengers(passengers)

    recommendPass = find_passengers_on_route(driver1, passengers)

    print("Recommended Passengers are: ")
    for p in recommendPass:
        print(p['id'])

    passDict = {}
    for passenger in recommendPass:
        passDict[passenger['id']] = passenger['start']

    optOrder = optimalOrder(passDict, driver1)

    optPass = []

    for i in optOrder:
        for p in recommendPass:
            if (i == p['id']):
                optPass.append(p)

    print("The optimal order to pick up is: ", optPass)

    # drawMap = DrawMap(640, 480, os.getenv('API_KEY'), driver1['start'], driver1['end'])
    #
    # drawMap.drawPinMap(recommendPass, driver1)
    #
    # drawMap.drawFinalRouteMap(optPass, driver1)

    # print(recommendPass)

    # gmap = gmplot.GoogleMapPlotter(43.90932051834358, -78.95352285076547, 13, apikey=apikey)

    # linePath = zip(*steps)

    # gmap.plot(*linePath)

    # path = zip(*routePoints)

    # gmap.scatter(*path)

    # gmap.draw("pathTest.html")
