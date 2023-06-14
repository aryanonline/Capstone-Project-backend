import pymongo
from flask import Flask, render_template, request, jsonify
import os
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from datetime import datetime
import hashlib
from MatchMaking import Recommendation
from MatchMaking.DrawMap import DrawMap
from pymongo.errors import DuplicateKeyError

app = Flask(__name__)
username = os.getenv("SCOOP_DB_USERNAME")
password = os.getenv("SCOOP_DB_PASS")

client = pymongo.MongoClient(
    "mongodb+srv://{}:{}@scoop-db.y0ayfkl.mongodb.net/?retryWrites=true&w=majority".format(username, password))
db = client.scoop


@app.route("/api/map", methods=["GET"])
def getMap():
    ride_id = request.args.get("rideID")
    passenger_id = request.args.get("passengerID")

    ride = list(db.ride.find({"_id": ObjectId(ride_id)}))[0]
    destLoc = list(db.location.find({"_id": ride["destinationID"]}))[0]

    driver = {
        'start': (ride["driverStartLat"], ride["driverStartLong"]),
        'end': (destLoc["latitude"], destLoc["longitude"])
    }

    drawMap = DrawMap(640, 480, os.getenv('API_KEY'), driver['start'], driver['end'])

    # if passenger ID is passed show the map from driver loc to that particular passenger to the dest (passenger map)
    if passenger_id:
        for passenger in ride ['passengers']:
            if passenger['passengerID'] == ObjectId(passenger_id):
                pickUpID = passenger['pickupLocationID']
                pickUp = list(db.location.find({"_id": ObjectId(pickUpID)}))

                lat = pickUp[0]['latitude']
                lng = pickUp[0]['longitude']

                drawMap.drawFinalRouteMap([{'start': (lat, lng)}], driver)
                break
            else:
                return "Passenger not found", 400
    # else draw the whole map with all the passenger (driver map)
    else:
        passengers = ride['passengers']

        passengerLocs = []

        for passenger in passengers:
            pickUpID = passenger['pickupLocationID']

            pickUp = list(db.location.find({"_id": ObjectId(pickUpID)}))

            lat = pickUp[0]['latitude']
            lng = pickUp[0]['longitude']

            passengerLocs.append({'start': (lat, lng)})

        drawMap.drawFinalRouteMap(passengerLocs, driver)

    return render_template("map.html")


@app.route("/api/user", methods=["GET"])
def verifyUser():
    user_id = request.args.get("userID")

    if user_id:
        return dumps(list(db.user.find({"_id": ObjectId(user_id)})))

    user_name = request.args.get("username")
    user_pass = request.args.get("password")
    hashed_pass = hashlib.md5(user_pass.encode())

    user = list(db.user.find({"username": user_name, "password": hashed_pass.hexdigest()}, {"role", "firstName"}))
    if len(user) > 0:
        return dumps(user[0])
    else:
        return "Either username or password is incorrect.", 401


@app.route("/api/user", methods=["POST"])
def createUser():
    user_data = request.json

    # if required fields aren't filled return 400 error
    if user_data["username"] == "" or user_data["password"] == "" or user_data["firstName"] == "" or user_data[
        "lastName"] == "":
        return "Missing Fields", 400

    user_data["password"] = hashlib.md5(user_data["password"].encode()).hexdigest()
    birthday = user_data["birthday"].split("-")
    user_data["birthday"] = datetime(int(birthday[0]), int(birthday[1]), int(birthday[2]))

    try:
        inserted_user = db.user.insert_one(user_data)
        return dumps(list(db.user.find({"_id": inserted_user.inserted_id}, {"_id"})))

    # username already exists in database
    except DuplicateKeyError:
        return "Username already exists", 409


@app.route("/api/user/activeRide", methods=["GET"])
def getActiveRides():
    user_id = request.args.get("userID")
    active_ride_id = list(db.user.find({"_id": ObjectId(user_id)}, {"activeRide"}))[0]["activeRide"]
    active_ride = db.ride.find({"_id": active_ride_id})

    return dumps(list(active_ride))


@app.route("/api/user/acceptedRides", methods=["GET"])
def getAcceptedRides():
    user_id = request.args.get("userID")
    accepted_ride_ids = list(db.user.find({"_id": ObjectId(user_id)}, {"acceptedRides"}))[0]["acceptedRides"]

    accepted_rides = []
    for ride_id in accepted_ride_ids:
        accepted_rides.append(db.ride.find({"_id": ride_id["rideID"]}))

    return dumps(accepted_rides)


@app.route("/api/user/pastRides", methods=["GET"])
def getPastRides():
    user_id = request.args.get("userID")
    past_ride_ids = list(db.user.find({"_id": ObjectId(user_id)}, {"pastRides"}))[0]["pastRides"]

    past_rides = []
    for ride_id in past_ride_ids:
        past_rides.append(db.ride.find({"_id": ride_id["rideID"]}))

    return dumps(past_rides)


@app.route("/api/liveLocation", methods=["PUT"])
def updateLiveLocation():
    user_id = request.args.get("userID")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    user_loc_id = list(db.user.find({"_id": ObjectId(user_id)}, {"locationID"}))[0]["locationID"]

    db.location.update({
        "_id": user_loc_id
    },
        {
            "$set": {
                "latitude": int(latitude),
                "longitude": int(longitude)
            }
        })

    return dumps(list(db.location.find({"_id": user_loc_id})))


@app.route("/api/driver", methods=["GET"])
def getDriver():
    user_id = request.args.get("userID")
    driver_id = request.args.get("driverID")

    if user_id:
        return dumps(list(db.driver.find({"userID": ObjectId(user_id)})))
    elif driver_id:
        return dumps(list(db.driver.find({"_id": ObjectId(driver_id)})))


@app.route("/api/driver", methods=["POST"])
def createDriver():
    driver_data = request.json
    driver_data["userID"] = ObjectId(driver_data["userID"])
    inserted_driver = db.driver.insert_one(driver_data)

    return dumps(list(db.driver.find({"_id": inserted_driver.inserted_id})))


@app.route("/api/passenger", methods=["GET"])
def getPassenger():
    user_id = request.args.get("userID")
    passenger_id = request.args.get("passengerID")

    if user_id:
        return dumps(list(db.passenger.find({"userID": ObjectId(user_id)})))
    elif passenger_id:
        return dumps(list(db.passenger.find({"_id": ObjectId(passenger_id)})))


@app.route("/api/passenger", methods=["POST"])
def createPassenger():
    passenger_data = request.json
    passenger_data["userID"] = ObjectId(passenger_data["userID"])
    inserted_passenger = db.passenger.insert_one(passenger_data)

    return dumps(list(db.passenger.find({"_id": inserted_passenger.inserted_id})))


@app.route("/api/location", methods=["GET"])
def getLocation():
    location_id = request.args.get("locationID")

    return dumps(list(db.location.find({"_id": ObjectId(location_id)})))


@app.route("/api/location", methods=["POST"])
def createLocation():
    latitude = float(request.args.get("latitude"))
    longitude = float(request.args.get("longitude"))
    loc = db.location.insert_one(
        {
            "latitude": latitude,
            "longitude": longitude
        }
    )
    return dumps(list(db.location.find({"_id": loc.inserted_id})))


@app.route("/api/requests", methods=["GET"])
def getRequests():
    driver_id = request.args.get("driverID")
    start_lat = request.args.get("startLat")
    start_long = request.args.get("startLong")
    destination_loc_id = request.args.get("destinationID")
    # this includes the date and time of the departure
    departure_date = request.args.get("departureDate")
    arrival_time = request.args.get("arrivalTime")

    driver = list(db.driver.find({"_id": ObjectId(driver_id)}, {"isModuleComplete", "maxRadius"}))[0]
    destination_loc = list(db.location.find({"_id": ObjectId(destination_loc_id)}))[0]
    date = departure_date.split("-")
    time = arrival_time.split(":")

    driver_info = {
        "module_completed": driver["isModuleComplete"],
        "start": (float(start_lat), float(start_long)),
        "end": (destination_loc["latitude"], destination_loc["longitude"]),
        "departure_date": datetime(int(date[0]), int(date[1]), int(date[2])),
        "arrival_time": datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2])),
        "radius": float(driver["maxRadius"]),
    }

    open_requests = list(db.request.find())
    passengers = []
    for req in open_requests:
        passenger_info = list(db.passenger.find({"_id": req["passengerID"]}, {"impairments"}))[0]
        start = list(db.location.find({"_id": req["pickupLocationID"]}))[0]
        end = list(db.location.find({"_id": req["destinationID"]}))[0]

        passenger = {
            "request_id": req["_id"],
            "id": req["passengerID"],
            "has_impairments": True if len(passenger_info["impairments"]) > 0 else False,
            "departure_date": req["departureDate"],
            "arrival_time": req["arrivalTime"],
            "start": (start["latitude"], start["longitude"]),
            "end": (end["latitude"], end["longitude"])
        }

        passengers.append(passenger)

    recommendations = Recommendation.find_passengers_on_route(driver_info, passengers)
    return dumps(recommendations)


@app.route("/api/request", methods=["GET"])
def getRequest():
    request_id = request.args.get("requestID")

    return dumps(list(db.request.find({"_id": ObjectId(request_id)})))


@app.route("/api/request", methods=["POST"])
def createRequest():
    request_data = request.json
    request_data["passengerID"] = ObjectId(request_data["passengerID"])
    request_data["pickupLocationID"] = ObjectId(request_data["pickupLocationID"])
    request_data["destinationID"] = ObjectId(request_data["destinationID"])
    request_data["offers"] = []

    departureDate = request_data["departureDate"].split("-")
    request_data["departureDate"] = datetime(int(departureDate[0]), int(departureDate[1]), int(departureDate[2]))

    arrivalTime = request_data["arrivalTime"].split(":")
    request_data["arrivalTime"] = datetime(int(departureDate[0]), int(departureDate[1]), int(departureDate[2]),
                                           int(arrivalTime[0]), int(arrivalTime[1]), int(arrivalTime[2]))

    inserted_request = db.request.insert_one(request_data)

    db.passenger.update_one({"_id": request_data["passengerID"]}, {"$push": {"requests": inserted_request.inserted_id}},
                            upsert=True)
    return dumps(list(db.request.find({"_id": inserted_request.inserted_id})))


@app.route("/api/request/deleteRequest", methods=["POST"])
def deleteRequest():
    request_id = request.args.get("requestID")
    passenger_id = request.args.get("passengerID")

    db.passenger.update_one({"_id": ObjectId(passenger_id)}, {"$pull": {"requests": ObjectId(request_id)}})
    db.request.delete_one({"_id": ObjectId(request_id)})
    return "removed"


@app.route("/api/request/acceptRequest", methods=["PUT"])
def acceptRequest():
    offer_id = request.args.get("offerID")
    request_id = request.args.get("requestID")

    db.request.update_one({"_id": ObjectId(request_id)}, {"$set": {"offers.$[offer].isAccepted": True}}, upsert=False,
                          array_filters=[{"offer._id": ObjectId(offer_id)}])

    return dumps(list(db.request.find({"_id": ObjectId(request_id)}, {"offers"})))


@app.route("/api/request/offer", methods=["GET"])
def getOffer():
    requestID = request.args.get("requestID")
    driverID = request.args.get("driverID")

    offer = list(db.request.find({"_id": ObjectId(requestID)}, {"offers": {"$elemMatch": {"driverID": ObjectId(driverID)}}}))

    return dumps(offer)


@app.route("/api/request/offer", methods=["POST"])
def createOffer():
    offer_data = request.json
    request_id = ObjectId(offer_data["requestID"])
    offer_data["_id"] = ObjectId()
    offer_data.pop("requestID")
    offer_data["driverID"] = ObjectId(offer_data["driverID"])
    offer_data["isAccepted"] = False
    driverArrivalTime = offer_data["driverArrivalTime"].split(":")

    arrival_date = list(db.request.find({"_id": request_id}, {"arrivalTime"}))[0]["arrivalTime"]
    arrival_date = arrival_date.replace(hour=int(driverArrivalTime[0]), minute=int(driverArrivalTime[1]))
    offer_data["driverArrivalTime"] = arrival_date

    db.request.update_one({"_id": request_id}, {"$push": {"offers": offer_data}}, upsert=True)
    return dumps(offer_data["_id"])


@app.route("/api/request/deleteOffer", methods=["PUT"])
def deleteOffer():
    request_id = request.args.get("requestID")
    offer_id = request.args.get("offerID")

    db.request.update_one({"_id": ObjectId(request_id)}, {"$pull": {"offers": {"_id": ObjectId(offer_id)}}})
    return dumps(list(db.request.find({"_id": ObjectId(request_id)}, {"offers"})))


@app.route("/api/ride", methods=["GET"])
def getRide():
    ride_id = request.args.get("rideID")
    return dumps(list(db.ride.find({"_id": ObjectId(ride_id)})))


@app.route("/api/ride", methods=["POST"])
def createRide():
    ride_data = request.json
    # get the drivers ID
    ride_data["driverID"] = ObjectId(ride_data["driverID"])
    ride_data["driverStartLat"] = float(ride_data["driverStartLat"])
    ride_data["driverStartLong"] = float(ride_data["driverStartLong"])

    # get the departure date and convert to datetime object
    departureDate = ride_data["departureDate"].split("/")
    arrivalTime = ride_data["arrivalTime"].split(":")
    ride_data["arrivalDateTime"] = datetime(int(departureDate[2]), int(departureDate[0]), int(departureDate[1]),
                                            int(arrivalTime[0]), int(arrivalTime[1]))

    ride_data.pop("departureDate")
    ride_data.pop("arrivalTime")

    for i in range(len(ride_data["passengers"])):
        ride_data["passengers"][i]["passengerID"] = ObjectId(ride_data["passengers"][i]["passengerID"])
        ride_data["passengers"][i]["pickupLocationID"] = ObjectId(ride_data["passengers"][i]["pickupLocationID"])

    # get the drivers user ID
    driver_uid = list(db.driver.find({"_id": ride_data["driverID"]}, {"userID"}))[0]["userID"]

    # get all the drivers accepted rides
    driver_rides = list(db.user.find({"_id": driver_uid}))[0]["acceptedRides"]

    closest_arrival = None
    closest_arrival_ride_id = None
    # check each ride if the passenger can be added to it
    for ride_id in driver_rides:
        ride_arrival_date = list(db.ride.find({"_id": ride_id["rideID"]}, {"arrivalDateTime"}))[0]["arrivalDateTime"]

        if ride_arrival_date.date() == ride_data["arrivalDateTime"].date():
            # check if there exits a ride of the driver before the requested time
            if ride_arrival_date.time() < ride_data["arrivalDateTime"].time():
                if closest_arrival is None:
                    closest_arrival = ride_arrival_date
                    closest_arrival_ride_id = ride_id["rideID"]
                # put the passenger in the ride closest to the time they'd like to get there
                elif ride_arrival_date > closest_arrival:
                    closest_arrival = ride_arrival_date
                    closest_arrival_ride_id = ride_id["rideID"]

    if closest_arrival is not None and closest_arrival_ride_id is not None:
        ride = list(db.ride.find({"_id": closest_arrival_ride_id}, {"passengers", "driverID"}))[0]
        driver_id = ride["driverID"]
        # check if the passenger is already apart of the ride
        for passenger in ride["passengers"]:
            for new_passenger in ride_data["passengers"]:
                if passenger["passengerID"] == new_passenger["passengerID"]:
                    return "You are already apart of the a ride on this day with this driver", 401

        curr_num_passengers = len(ride["passengers"])
        total_num_seats = list(db.driver.find({"_id": driver_id}, {"vehicle"}))[0]["vehicle"]["availableSeats"]

        # the # of passengers in the car much be less than or equal to the available seats in the car
        if curr_num_passengers < int(total_num_seats):
            db.ride.update_one({"_id": closest_arrival_ride_id}, {"$push": {
                "passengers": {"passengerID": ObjectId(ride_data["passengers"][0]["passengerID"]),
                               "pickupLocationID": ObjectId(ride_data["passengers"][0]["pickupLocationID"])}}},
                               upsert=True)
            return dumps(list(db.ride.find({"_id": closest_arrival_ride_id})))
        else:
            return "No available seats", 401
    else:
        ride_data["destinationID"] = ObjectId(ride_data["destinationID"])
        inserted_ride = db.ride.insert_one(ride_data)

        db.user.update_one({"_id": driver_uid}, {"$push": {"acceptedRides": {"rideID": inserted_ride.inserted_id}}},
                           upsert=True)

        for i in range(len(ride_data["passengers"])):
            passenger_uid = list(db.passenger.find({"_id": ride_data["passengers"][i]["passengerID"]},
                                                   {"userID"}))[0]["userID"]
            db.user.update_one({"_id": passenger_uid},
                               {"$push": {"acceptedRides": {"rideID": inserted_ride.inserted_id}}},
                               upsert=True)
        return dumps(list(db.ride.find({"_id": inserted_ride.inserted_id})))


@app.route("/api/profile", methods=["PUT"])
def updateProfile():
    user_id = request.args.get("userID")

    username = request.args.get("username")
    firstName = request.args.get("firstName")
    lastName = request.args.get("lastName")
    email = request.args.get("email")
    phoneNumber = request.args.get("phoneNumber")
    make = request.args.get("make")
    model = request.args.get("model")
    year = request.args.get("year")
    licencePlate = request.args.get("licencePlate")
    availableSeats = request.args.get("availableSeats")
    maxRadius = request.args.get("maxRadius")
    isModuleComplete = request.args.get("isModuleComplete")

    driver_len = db.driver.find_one({"_id": ObjectId(user_id)})

    if driver_len:
        # update user params
        driver_user_id = db.user.find_one({"_id": ObjectId(driver_len.get("userID"))})
        db.user.update_one({"_id": ObjectId(driver_user_id.get("_id"))}, {"$set": {
            "username": username,
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phoneNumber": phoneNumber,
        }})

        # update driver params
        db.driver.update_one({"_id": ObjectId(user_id)}, {"$set": {
            "vehicle.make": make,
            "vehicle.model": model,
            "vehicle.year": year,
            "vehicle.licencePlate": licencePlate,
            "vehicle.availableSeats": availableSeats,
            "maxRadius": maxRadius,
            "isModuleComplete": isModuleComplete,
        }})

    return dumps(list(db.driver.find({"_id": ObjectId(user_id)})))


app.run(host="0.0.0.0", port=3001)
