

import xml.etree.ElementTree as ET
import xml.dom.minidom

def generate_vehicle_routes(vehicle_counts, routes, total_duration):
    vehicles = []
    total_vehicles = sum(vehicle_counts.values())
    depart_interval = total_duration / total_vehicles

    vehicle_id = 0
    current_time = 0

    while any(count > 0 for count in vehicle_counts.values()):
        for route_key in vehicle_counts:
            if vehicle_counts[route_key] > 0:
                vehicle_counts[route_key] -= 1
                vehicle = ET.Element('vehicle', {
                    'id': f"vehicle_{vehicle_id}",
                    'type': 'type1',
                    'depart': f"{current_time:.2f}",
                    'color': '1,0,0'
                })
                ET.SubElement(vehicle, 'route', {'edges': routes[route_key]})
                vehicles.append(vehicle)
                vehicle_id += 1
                current_time += depart_interval
    return vehicles

vehicle_routes = {
    "south_to_north": 251,
    "south_to_I": 15,
    "north_to_south": 474,
    "I_to_23N": 24,
    "I_to_23th_south": 55,
    "N_to_I": 65,
}

routes = {
    "south_to_north": "-590598876#1 -590598876#0 -130285156#3 -130285156#2 -130285156#1 -130285156#0 -1120094388",
    "south_to_I": "-590598876#1 -590598876#0 -50799230#3 -50799230#2 -50799230#1 -50799230#0",
    "north_to_south": "1120094388 130285156#0 130285156#1 130285156#2 130285156#3 590598876#0 590598876#1",
    "I_to_23N": "50799230#0 50799230#1 50799230#2 50799230#3 -130285156#3 -130285156#2 -130285156#1 -130285156#0 -1120094388",
    "I_to_23th_south": "50799230#1 50799230#2 50799230#3 590598876#0 590598876#1",
    "N_to_I": "1120094388 130285156#0 130285156#1 130285156#2 130285156#3 -50799230#3 -50799230#2 -50799230#1 -50799230#0",
}

total_duration = 3600 
root = ET.Element('routes')

vtype = ET.SubElement(root, 'vType', {
    'id': 'type1',
    'accel': '0.8',
    'decel': '4.5',
    'sigma': '0.5',
    'length': '5',
    'maxSpeed': '70'
})

vehicles = generate_vehicle_routes(vehicle_routes, routes, total_duration)
for vehicle in vehicles:
    root.append(vehicle)

xml_str = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

with open(r"C:\Users\12028\Downloads\GWUUZilinaColab\3to4pm.route.xml", "w") as f:
    f.write(xml_str)

print("Routing file generated successfully.")
