import xml.etree.ElementTree as ET
import xml.dom.minidom
import random

def create_vehicle_types():
    vehicle_types = [
        {"id": "veh_type_0", "T": "2.415", "a": "3.119", "b": "5.824", "v0": "21.882", "so": "4.061", "delta": "4.000"},
        {"id": "veh_type_1", "T": "2.113", "a": "3.468", "b": "5.915", "v0": "22.476", "so": "4.012", "delta": "4.000"},
        {"id": "veh_type_2", "T": "2.205", "a": "3.708", "b": "5.752", "v0": "22.191", "so": "4.262", "delta": "4.000"},
        {"id": "veh_type_3", "T": "2.407", "a": "3.837", "b": "5.517", "v0": "21.614", "so": "3.898", "delta": "4.000"},
        {"id": "veh_type_4", "T": "2.892", "a": "3.395", "b": "5.633", "v0": "22.443", "so": "5.752", "delta": "4.000"},
    ]
    elements = []
    for v_type in vehicle_types:
        v = ET.Element('vType', id=v_type["id"], carFollowModel="IDM", T=v_type["T"], a=v_type["a"], 
                       b=v_type["b"], v0=v_type["v0"], so=v_type["so"], delta=v_type["delta"])
        elements.append(v)
    return elements

def create_pedestrian_types():
    pedestrian_types = [
        {"id": "ped_type_0", "r_alpha": "0.349", "lambda_alpha": "0.344", "A_alpha": "1.603", "B_alpha": "0.312"},
        {"id": "ped_type_1", "r_alpha": "0.338", "lambda_alpha": "0.343", "A_alpha": "1.663", "B_alpha": "0.324"},
        {"id": "ped_type_2", "r_alpha": "0.349", "lambda_alpha": "0.346", "A_alpha": "1.747", "B_alpha": "0.336"},
        {"id": "ped_type_3", "r_alpha": "0.366", "lambda_alpha": "0.352", "A_alpha": "1.675", "B_alpha": "0.323"},
        {"id": "ped_type_4", "r_alpha": "0.400", "lambda_alpha": "0.355", "A_alpha": "1.740", "B_alpha": "0.315"},
    ]
    elements = []
    for p_type in pedestrian_types:
        p = ET.Element('vType', id=p_type["id"], r_alpha=p_type["r_alpha"], lambda_alpha=p_type["lambda_alpha"],
                       A_alpha=p_type["A_alpha"], B_alpha=p_type["B_alpha"], vClass="pedestrian")
        elements.append(p)
    return elements

def create_passenger_trips(trips, distribution, total_duration=3600):
    routes = []
    vehicle_types = create_vehicle_types()
    vehicle_type_ids = [v.get('id') for v in vehicle_types]

    all_depart_times = []
    for trip_name, count in distribution.items():
        interval = total_duration / count
        for i in range(count):
            all_depart_times.append((trip_name, i * interval))

    random.shuffle(all_depart_times)

    for idx, (trip_name, depart_time) in enumerate(all_depart_times):
        trip_details = trips[trip_name]
        vehicle_type = vehicle_type_ids[idx % len(vehicle_type_ids)]
        trip = ET.Element('vehicle', id=f"{trip_details['id']}_{idx}", type=vehicle_type, 
                          depart=str(depart_time), departLane=trip_details['departLane'], 
                          departSpeed=trip_details['departSpeed'])
        ET.SubElement(trip, 'route', edges=trip_details['route'])
        routes.append((depart_time, trip))
    
    routes.sort(key=lambda x: x[0])
    return vehicle_types + [trip for _, trip in routes]

def create_pedestrian_trips(trips, distribution, total_duration=3600):
    routes = []
    pedestrian_types = create_pedestrian_types()
    pedestrian_type_ids = [p.get('id') for p in pedestrian_types]

    all_depart_times = []
    interval_duration = 900  # 15 minutes in seconds
    num_intervals = total_duration // interval_duration

    for ped_id, counts in distribution.items():
        for interval_idx, count in enumerate(counts):
            for i in range(count):
                depart_time = interval_idx * interval_duration + (i * interval_duration / count)
                all_depart_times.append((ped_id, depart_time))

    random.shuffle(all_depart_times)

    for idx, (ped_id, depart_time) in enumerate(all_depart_times):
        trip_details = trips[ped_id]
        pedestrian_type = pedestrian_type_ids[idx % len(pedestrian_type_ids)]
        person = ET.Element('person', id=f"{ped_id}_{idx+1}", type=pedestrian_type, depart=str(depart_time))
        walk = ET.SubElement(person, 'walk')
        walk.set('from', trip_details['from'])
        walk.set('to', trip_details['to'])
        routes.append((depart_time, person))
    
    routes.sort(key=lambda x: x[0])
    return pedestrian_types + [person for _, person in routes]

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
    "ped1": {"from": "1197548845#0", "to": "232149477#0"},
    "ped2": {"from": "-130285156#2", "to": "130285156#2"},
    "ped3": {"from": "590598876#1", "to": "-590598876#1"},
    "ped4": {"from": "1197548869", "to": "1034625747#1"},
    "ped5": {"from": "-50799230#3", "to": "50799230#3"},
    "ped6": {"from": "-130285156#2", "to": "-50799230#3"},
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
    "ped1": [105, 114, 120, 117],
    "ped2": [152, 169, 194, 179],
    "ped3": [85, 91, 64, 68],
    "ped4": [75, 92, 77, 86],
    "ped5": [59, 77, 53, 44],
    "ped6": [31, 21, 24, 23],
}

passenger_routes = create_passenger_trips(passenger_trips, vehicle_distribution)
pedestrian_routes = create_pedestrian_trips(pedestrian_trips, pedestrian_distribution)

save_routes_to_file(passenger_routes, r"C:\Users\Pedram\Desktop\GWU_UZilina_Colab\Network\foggy.vehicle.trips.xml")
save_routes_to_file(pedestrian_routes, r"C:\Users\Pedram\Desktop\GWU_UZilina_Colab\Network\foggy.pedestrian.rou.xml")
