import gmplot
import googlemaps
import gmaps
import os
from math import log, pi, radians, sin, cos, sqrt, atan2
from ipywidgets.embed import embed_minimal_html

from dotenv import load_dotenv

load_dotenv()

class DrawMap:

    def __init__(self, map_width_pixels, map_height_pixels, apiKey, start, end=None) -> None:
        self.start = start
        self.end = end
        if not end: self.end = start
        # self.gmp = gmplot.GoogleMapPlotter(start[0], start[1], self._zoom(self, start, end, map_width_pixels, map_height_pixels), apikey=apiKey)
        self.gmp = gmplot.GoogleMapPlotter(start[0], start[1], self.setZoomLevel(start, end, map_width_pixels, map_height_pixels), apikey=apiKey)
        self.gmaps = googlemaps.Client(key=apiKey)

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        # approximate radius of earth in km
        R = 6371.0

        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance
    
    def setZoomLevel(self, start, end, map_width_pixels, map_height_pixels):
        latitudes = (start[0], end[0])
        longitudes = (start[1], end[1])
        lat_diff = max(latitudes) - min(latitudes)
        lng_diff = max(longitudes) - min(longitudes)
        # calculate the diagonal distance between the two points
        diagonal_distance = (lat_diff ** 2 + lng_diff ** 2) ** 0.5
        # calculate the zoom level based on the map width, height, and diagonal distance
        zoom_level = int(
            round(
                log(
                    360.0 / (256.0 * max(map_width_pixels, map_height_pixels) * diagonal_distance * pi / 180.0),
                    2,
                )
            )
        )
        min_zoom = 14
        if zoom_level < min_zoom: return min_zoom
        return zoom_level # TODO: change minimum zoom level through trial and error
    
    # Draw a map showing the pick-up locations of the recommended passengers as pins, with 2 large pins representing the driver's start and end points
    def drawPinMap(self, recommendedPassengers, driver):
        passengerCoords = []
        passEndCoords = []
        for passenger in recommendedPassengers: 
            passengerCoords.append((passenger["start"][0],passenger["start"][1]))
            passEndCoords.append((passenger["end"][0], passenger["end"][1]))
        passengers_lats, passengers_lngs = zip(*passengerCoords)
        passEndLats, passEndLngs = zip(*passEndCoords)
        # print(passengers_lats)
        self.gmp.scatter(passengers_lats, passengers_lngs, color='#3B0B39', size=driver['radius']*1000, marker=False)
        # self.gmp.scatter(passEndLats, passEndLngs, color='#660000', size=100, marker=False) # Draws end locations
        self.gmp.marker(self.start[0], self.start[1], color='blue')
        self.gmp.marker(self.end[0], self.end[1], color='red')
        # self.gmp.draw('Drawmap.html')

    # Draw a map showing the final route, using the pick-up and drop-off locations of the selected passengers as stops
    def drawFinalRouteMap(self, selectedPassengers, driver): #TODO remove the comments below
        
        # origin = (37.769408, -122.510138)
        origin = driver['start']
        # destination = (37.766273,-122.451389)
        destination = driver['end']

        wpoints = []

        for passenger in selectedPassengers:
            wpoints.append(passenger['start'])
        
        #Different method - ignore 
        # gmaps.configure(api_key='AIzaSyBzQ9QaGzWhZDQ3ZxkMKRk4S-lxlZAWE5w')
        # fig = gmaps.figure()
        # layer = gmaps.directions.Directions(origin, destination, mode="driving", avoid="ferries")
        # fig.add_layer(layer)
        
        #using gmplot
        # gmp = gmplot.GoogleMapPlotter(origin[0], destination[0], 13, apikey = os.getenv("API_KEY"))

        self.gmp.directions(
            origin,
            destination,
            waypoints=wpoints
        )

        tempPath = os.path.join(os.getcwd(), 'Server\\templates')
        filePath = tempPath + '\\map.html'
        self.gmp.draw(filePath)

