import requests
import json
import csv



def getIntersectionCoords(street_1, street_2):
    global addressResults

    # This is to solve a stupid problem with badly formatted street names
    if "/" in street_1:
        street_1 = street_1[0:street_1.index("/")]
    if "/" in street_2:
        street_2 = street_2[0:street_2.index("/")]
        
    address = f"{street_1} and {street_2} CO".replace(" ", "+")

    # There are a lot of duplicate intersections in the data, this will save the results and not re-call the api for 
    # the same exact intersection
    if addressResults.get(address, False) != False:
        log_file.write(f"{address} DUPLICATE\n")
        print(f"{address} DUPLICATE")
        return addressResults[address]

    #https://maps.googleapis.com/maps/api/geocode/json?address=US+40+and+Steele+St,+CO&key=AIzaSyD13cNGFmT_BCpyk0LCoOOEriUms7BF39c
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    key = "AIzaSyD13cNGFmT_BCpyk0LCoOOEriUms7BF39c"

    request_url = f'{url}?address={address}&key={key}'

    response = requests.get(request_url)
    results = response.json()['results']

    # sometimes the results are empty, not quite sure why
    if type(results) != list or len(results) < 1:
        log_file.write(f"ERROR: Invalid response for {address}\n")
        print(f"ERROR: Invalid response for {address}")
        log_file.write(str(results) + "\n")
        print(str(results))
        log_file.write(f"{address} Unable to find intersection\n")
        print(f"{address} Unable to find intersection")
        addressResults[address] = None
        return None

    result = response.json()['results'][0]
    address_components = result['address_components']

    # Check if geocoding response return an intersection match
    didFindIntersection = False
    for i in address_components:
        if "intersection" in i['types']:
            didFindIntersection = True

    geometry = result['geometry']
    latitude = geometry['location']['lat']
    longitude = geometry['location']['lng']

    # Write geocoding response to file
    with open(f'../sample files/geocoder_results/{address}.json', 'w') as outfile:
        json.dump(response.json(), outfile, indent=4)
    
    if didFindIntersection:
        log_file.write(f"{address} Found Intersection!! Coords are {latitude}, {longitude}\n")
        print(f"{address} Found Intersection!! Coords are {latitude}, {longitude}")
        addressResults[address] = [latitude, longitude]
        return [latitude, longitude]
    else:
        log_file.write(f"{address} Unable to find intersection\n")
        print(f"{address} Unable to find intersection")
        addressResults[address] = None
        return None


csv_data = list(csv.DictReader(open('../sample files/navjoy_work_zone_closure.csv')))
countTotal = 0
countFound = 0
addressResults = {}
log_file = open('geocoder_logs.txt', 'a')
for line in enumerate(csv_data):
    line = line[1]
    if line["streetNameTo"]:
        countTotal += 1
        resp = getIntersectionCoords(line["routeName"], line["streetNameTo"])
        if resp:
            countFound += 1
    if line["streetNameFrom"]:
        countTotal += 1
        resp = getIntersectionCoords(line["routeName"], line["streetNameFrom"])
        if resp:
            countFound += 1
    if countTotal != 0:
        log_file.write(f"Found {countFound} out of {countTotal} intersections, or {100*round(countFound/countTotal, 2)}%\n")
        print(f"Found {countFound} out of {countTotal} intersections, or {100*round(countFound/countTotal, 2)}%")

log_file.close()