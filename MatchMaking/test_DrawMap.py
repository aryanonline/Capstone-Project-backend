from DrawMap import DrawMap
import Recommendation as rcm
from dotenv import load_dotenv
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2, log, pi, ceil
import os

load_dotenv()

apikey = os.getenv("API_KEY")


def test_calc_dist1():

    driver1 = {'module_completed': False , 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'radius': 3.0, 'start': (43.945758650189426, -78.89674368655093), 'end':(43.890407448236104, -78.87961839670852)}
    
    dm = DrawMap(640, 480, apikey, driver1['start'], driver1['end'])

    a = dm._calculate_distance(43.945758650189426, -78.89674368655093, 43.890407448236104, -78.87961839670852) # Distance from OTU to Oshawa Center

    a = ceil(a*1000)/1000

    assert a >= 6.305 and a <= 6.307 # The actual distance was calculated by hand using the Haversine formula. The answer calculated was 6.306 km. The assertion accounts for precision errors.


def test_calc_dist2():

    driver1 = {'module_completed': False , 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'radius': 3.0, 'start': (43.945758650189426, -78.89674368655093), 'end':(43.890407448236104, -78.87961839670852)}
    
    dm = DrawMap(640, 480, apikey, driver1['start'], driver1['end'])

    a = dm._calculate_distance(43.945758650189426, -78.89674368655093, 43.945758650189426, -78.87961839670852) # Distance for Horizontal Line

    a = ceil(a*1000)/1000

    assert a >= 1.360 and a <= 1.380

def test_calc_dist3():

    driver1 = {'module_completed': False , 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'radius': 3.0, 'start': (43.945758650189426, -78.89674368655093), 'end':(43.890407448236104, -78.87961839670852)}
    
    dm = DrawMap(640, 480, apikey, driver1['start'], driver1['end'])

    a = dm._calculate_distance(43.945758650189426, -78.89674368655093, 43.890407448236104, -78.89674368655093) # Distance for Vertical Line

    a = ceil(a*1000)/1000

    assert a >= 6.140 and a <= 6.156


def test_calc_dist4():

    driver1 = {'module_completed': False , 'departure_date': datetime.now(), 'arrival_time': datetime.now()+timedelta(minutes=30), 'radius': 3.0, 'start': (43.945758650189426, -78.89674368655093), 'end':(43.890407448236104, -78.87961839670852)}
    
    dm = DrawMap(640, 480, apikey, driver1['start'], driver1['end'])

    a = dm._calculate_distance(43.945758650189426, -78.89674368655093, 43.945758650189426, -78.89674368655093) # Distance for two same points

    a = ceil(a*1000)/1000

    assert a == 0