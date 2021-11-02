import random
import requests
import json
import datetime
import math
from datetime import timedelta
from datetime import datetime

# const for maximum ticket price
max_tkt = 280
# const for minimum ticket price
min_tkt = 45

response = requests.get("http://127.0.0.1:8080/lms/route/*")
# list of all existing routes
routes_available = response.json()

response = requests.get("http://127.0.0.1:8080/lms/airplane/*")
# list of all existing airplanes
airplanes_available = response.json()

response = requests.get("http://127.0.0.1:8080/lms/flight/*")
# list of already existing flights
existing_flights = response.json()


# create id that doesnt already exist
def get_id():
    ids = []
    for flight in existing_flights:
        ids.append(int(flight["id"]))
    ids = sorted(ids)
    # returns an id 1 greater than any existing id
    return ids[len(ids) - 1] + 1


# randomly select route
def get_route():
    route_index = random.randint(0, len(routes_available) - 1)
    return routes_available[route_index]["id"]


# randomly select airplane
def get_airplane():
    airplane_index = random.randint(1, len(airplanes_available) -1)
    return airplanes_available[airplane_index]


def departure_time(airplane_id):
    # make departure time -- will not be within 16 hours of a previous flight of this plane,
    # or 16 hours before an existing flight
    # will only schedule flights for the future
    delta = timedelta(hours=+16)
    eligible_flights = []
    for flight in existing_flights:
        if flight["airplane_ID"] == airplane_id:
            if datetime.fromisoformat(flight["departure_Time"]) + delta >= datetime.now():
                # list of flights for [airplane_id] departing from [16 or fewer hours ago] to any time in the future
                eligible_flights.append(flight)
    # sort dates from least to greatest
    eligible_flights = sorted(eligible_flights)
    # hour_diff represents intervals between flights already scheduled for this airplane.
    # Intervals of 32 or greater are eligible to have a flight scheduled into them, along with any period of time
    # 16+ hours after the last scheduled flight for this plane
    hour_diff = []
    slots_eligible = 1
    for i in range(len(eligible_flights) - 1):
        tdelta = datetime.fromisoformat(eligible_flights[i + 1]["departure_Time"]) - \
                 datetime.fromisoformat(eligible_flights[i]["departure_Time"])
        hour_diff.append(tdelta.total_seconds() / 3600)
        if tdelta.total_seconds() / 3600 >= 32:
            slots_eligible += 1

    # randomly select eligible slot
    selected_slot = random.randint(1, slots_eligible)
    this_slot = 0
    for i in range(len(hour_diff) - 1):
        if hour_diff[i] >= 32:
            this_slot += 1
            if this_slot == selected_slot:
                # fuzz time represents the period in which the plane could be scheduled to leave
                # for example, hour_diff[i] = 36, then fuzz_time = 4 as there are 4 hours in which the flight could be
                # scheduled to depart without being to near to ny other flight
                fuzz_time = hour_diff[i] - 32
                # make fuzz_time a timedelta in hours between 0 and floor(fuzz_time / 2.0)
                fuzz_time = timedelta(hours=+(math.floor(random.uniform(0.0, (fuzz_time / 2.0)))))
                # return datetime that is the datetime from eligible_flights[i] + 16 + fuzz_time
                fixed_interval = timedelta(hours=+16)
                return datetime.fromisoformat(eligible_flights[i]["departure_Time"]) + fixed_interval + fuzz_time
    # edge case where a plane has no entries in eligible_flights
    if len(eligible_flights) == 0:
        # create a flight of current time truncated to the hour, + a minimum of 2 hours + a fuzz time
        current_datetime = datetime.now()
        current_datetime = current_datetime.replace(minute=0, second=0, microsecond=0)
        fixed_interval = timedelta(hours=2)
        fuzz_time = timedelta(hours=+(random.randint(0, 5)))
        return current_datetime + fixed_interval + fuzz_time
    # edge case where slot selected is not an interval, but a timeslot after all existing flights
    # take last eligible flights departure time, add 16 hours, and a random fuzz time
    fixed_interval = timedelta(hours=+16)
    fuzz_time = timedelta(hours=+(random.randint(0,5)))
    return datetime.fromisoformat(eligible_flights[len(eligible_flights) - 1]["departure_Time"]) + fixed_interval + fuzz_time


def reserved_seats(airplane_id):
    # make number of reserved seats less than num seats on plane
    # get type_id of provided airplane
    response = requests.get("http://127.0.0.1:8080/lms/airplane/" + str(airplane_id))
    type_id = response.json()[0]["type_id"]
    # lookup number of seats for this type_id
    response = requests.get("http://127.0.0.1:8080/lms/airplane_type/" + str(type_id))
    num_seats = response.json()["max_capacity"]
    return random.randint(0, num_seats)


def seat_price():
    # simple random genertion for price, price moves in increments of 5 dollars
    return random.randint((min_tkt / 5), (max_tkt / 5)) * 5

# make a flight object
airplane = get_airplane()

flight = '{"id":' + str(get_id()) + ', "route_ID":' + str(get_route()) + ', "airplane_ID":' + str(airplane["id"]) +\
         ', "departure_Time":"' + str(departure_time(airplane["id"])) +\
         '", "reservedSeats":' + str(reserved_seats(airplane["id"])) + ', "seatPrice":'+ str(seat_price()) + '}'
print(flight)

json_flight = json.loads(flight)

# POST request
response = requests.post("http://127.0.0.1:8080/lms/flight/", json=json_flight)
print(str(response))
