import os
import requests
import pandas as pd
from numerize import numerize
from statistics import median

CSV_FOLDER = "csvfiles"
with open("api-key.txt") as file:
    API_KEY = file.read()
HTML_TEMPLATE = "html_template.html"
HTML_OUTPUT = "output_map.html"


def geocode(url):
    response = requests.get(url).json()
    loc = {}
    if response["status"] == "OK":
        loc = response["results"][0]["geometry"]["location"]
        loc["city"] = response["results"][0]["address_components"][2]["long_name"]
    return loc


output_arr = []
lats = []
longs = []
for filename in os.listdir(CSV_FOLDER):
    print(filename)
    csv_file = pd.read_csv(f"{CSV_FOLDER}/{filename}")

    for i, row in csv_file.iterrows():
        try:
            simple_address = row["Full Address"]
        except KeyError:
            continue
        simple_address = simple_address.replace("  ", " ").lower().title()  # Remove weird formatting and ensure proper capitalization
        address = simple_address
        if "Zip" in row.keys():
            address += f" {row["Zip"]}"

        status = row["Status"]
        if status == "SOLD":
            price = row["Sold Price"]
        else:
            price = row["ListPrice"]
        dom = row["DOMLS"]
        price = price.split("-")
        for x in range(len(price)):
            price[x] = price[x].strip().replace(",", "").replace("$", "")
            price[x] = numerize.numerize(int(price[x]))
        if len(price) > 1:
            price = f"{price[0]} - {price[1]}"
        else:
            price = price[0]

        address = address.replace(" ", "+") + "+CA"
        print(simple_address)
        address_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
        print(address_url)
        location = geocode(address_url)
        if "lat" not in location.keys():
            continue
        lat = location["lat"]
        long = location["lng"]
        city = location["city"]
        lats.append(lat)
        longs.append(long)
        output_arr.append(f"\t\t[\"{simple_address}\", \"{status}\", \"{dom}\", \"{city}\", \"{price}\", {lat}, {long}],\n")

output_arr[len(output_arr) - 1] = output_arr[len(output_arr) - 1].strip(",\n")

output_lines = ""
with open(HTML_TEMPLATE) as html:
    for line in html:
        if "center: " in line:
            line = f"\t  center: new google.maps.LatLng({median(lats)}, {median(longs)}),\n"
        output_lines += line
        if "var locations = [" in line:
            for addr in output_arr:
                output_lines += addr

with open(HTML_OUTPUT, "w") as output:
    output.writelines(output_lines)
