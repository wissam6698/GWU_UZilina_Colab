
import xml.etree.ElementTree as ET
import xml.dom.minidom
import random

def create_passenger_trips(trips, distribution, total_duration=3600):
    routes = []
    vType = ET.Element('vType', id="veh_passenger", vClass="passenger")

    all_depart_times = []
    for trip_name, count in distribution.items():
        interval = total_duration / count
        for i in range(count):
            all_depart_times.append((trip_name, i * interval))

    random.shuffle(all_depart_times)

    for idx, (trip_name, depart_time) in enumerate(all_depart_times):
        trip_details = trips[trip_name]
        trip = ET.Element('vehicle', id=f"{trip_details['id']}_{idx}", type=trip_details['type'], 
                          depart=str(depart_time), departLane=trip_details['departLane'], 
                          departSpeed=trip_details['departSpeed'])
        ET.SubElement(trip, 'route', edges=trip_details['route'])
        routes.append((depart_time, trip))
    
    routes.sort(key=lambda x: x[0])
    return [vType] + [trip for _, trip in routes]

def create_pedestrian_trips(trips, distribution, total_duration=3600):
    routes = []
    vType = ET.Element('vType', id="ped_pedestrian", vClass="pedestrian")

    all_depart_times = []
    for ped_id, count in distribution.items():
        interval = total_duration / count
        for i in range(count):
            all_depart_times.append((ped_id, i * interval))

    random.shuffle(all_depart_times)

    for idx, (ped_id, depart_time) in enumerate(all_depart_times):
        edges = trips[ped_id]
        person = ET.Element('person', id=f"{ped_id}_{idx}", type="ped_pedestrian", depart=str(depart_time))
        ET.SubElement(person, 'walk', edges=edges)
        routes.append((depart_time, person))
    
    routes.sort(key=lambda x: x[0])
    return [vType] + [person for _, person in routes]

def save_routes_to_file(routes, file_path):
    root = ET.Element('routes')
    for element in routes:
        root.append(element)
    
    xml_str = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    try:
        with open(file_path, "w") as f:
            f.write(xml_str)
        print(f"Routing file '{file_path}' generated successfully.")
    except PermissionError as e:
        print(f"PermissionError: {e}")
        print(f"Failed to save routing file '{file_path}'. Please check your permissions or try a different directory.")

passenger_trips = {
    "south_to_north": {"id": "veh1", "type": "veh_passenger", "depart": "0.00", "departLane": "best", 
                       "departSpeed": "max", "route": "-590598876#1 -130285156#2 -130285156#1 -130285156#0 -1120094388#0"},
    "south_to_I": {"id": "veh98", "type": "veh_passenger", "depart": "1126.86", "departLane": "best", 
                   "departSpeed": "max", "route": "-590598876#1 -50799230#3 -50799230#2"},
    "north_to_south": {"id": "veh0", "type": "veh_passenger", "depart": "0.00", "departLane": "best", 
                       "departSpeed": "max", "route": "1120094388#0 1120094388#1 130285156#1 130285156#2 590598876#1"},
    "I_to_23N": {"id": "veh55", "type": "veh_passenger", "depart": "632.42", "departLane": "best", 
                 "departSpeed": "max", "route": "50799230#0 50799230#3 -130285156#2 -130285156#1 -130285156#0 -1120094388#0"},
    "I_to_23th_south": {"id": "veh51", "type": "veh_passenger", "depart": "586.43", "departLane": "best", 
                        "departSpeed": "max", "route": "50799230#0 50799230#3 590598876#1"},
    "N_to_I": {"id": "veh60", "type": "veh_passenger", "depart": "689.92", "departLane": "best", 
               "departSpeed": "max", "route": "1120094388#0 1120094388#1 130285156#1 130285156#2 -50799230#3 -50799230#2"},
}

pedestrian_trips = {
    "pedestrian1": "1034625746#0 1034625746#1 1197548851#1 232149477#1",
    "pedestrian2": "1197548851#1 1197548865#1 1104847359",
    "pedestrian3": "1104847359 1197548865#1 1197548868#2 1197548868#1 1197548868#0",
    "pedestrian4": "-50799230#3 1197548865#1 1104847359",
    "pedestrian5": "1197548868#2 1197548851#1 232149477#1 232149477#0 232149476#2",
    "pedestrian6": "1197548845#3 1120094388#1 -130285156#1 -130285156#2 1197548868#2",
}

vehicle_distribution = {
    "south_to_north": 251,
    "south_to_I": 15,
    "north_to_south": 474,
    "I_to_23N": 24,
    "I_to_23th_south": 55,
    "N_to_I": 65,
}

pedestrian_distribution = {
    "pedestrian1": 456,
    "pedestrian2": 694,
    "pedestrian3": 308,
    "pedestrian4": 330,
    "pedestrian5": 233,
    "pedestrian6": 99,
}

passenger_routes = create_passenger_trips(passenger_trips, vehicle_distribution)
pedestrian_routes = create_pedestrian_trips(pedestrian_trips, pedestrian_distribution)

save_routes_to_file(passenger_routes, r"C:\Users\Pedram\Downloads\mapnewcommunicationpaper\osm.passenger.trips.xml")
save_routes_to_file(pedestrian_routes, r"C:\Users\Pedram\Downloads\mapnewcommunicationpaper\osm.pedestrian.rou.xml")
