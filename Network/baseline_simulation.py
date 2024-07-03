import traci
import sumolib
import csv

def run_simulation(step_limit, output_interval, output_file):
    # Start SUMO simulation
    sumo_cmd = ["sumo-gui", "-c", r"C:\Users\Pedram\Downloads\finalversion_DRL\Network\foggybottommetro.sumocfg"]
    traci.start(sumo_cmd)

    step = 0
    total_waiting_time = 0
    total_travel_time = 0
    total_stops = 0
    vehicle_count = 0
    total_fuel_consumption = 0
    total_emissions = {"CO": 0, "CO2": 0, "HC": 0, "NOx": 0, "PMx": 0}
    total_queue_length = 0
    max_queue_length = 0
    vehicle_ids_set = set()
    intersection_utilization = 0

    # Edge IDs of the intersection
    intersection_edges = ["-590598876#1", "-50799230#2", "1120094388#0", "130285156#0", "130285156#1", "130285156#2"]

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['step', 'total_waiting_time', 'total_travel_time', 'total_stops', 'total_fuel_consumption', 
                      'CO_emission', 'CO2_emission', 'HC_emission', 'NOx_emission', 'PMx_emission', 
                      'current_queue_length', 'max_queue_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        while step < step_limit:
            traci.simulationStep()
            c2=0
            c3=0
            c14=0
            pedestrian_ids = traci.person.getIDList()
            for pedestrian_id in pedestrian_ids:
                print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                print(f"Pedestrian ID: {pedestrian_id}")
                print(f"Lane Position: {traci.person.getLanePosition(pedestrian_id)}")
                print(traci.person.getRoadID(pedestrian_id))
                if traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w2':
                    c2+=1
                elif traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w1':
                    c3+=1
                elif traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w0':
                    c14+=1

            print ('c14 is ' +str(c14))
            print ('c2 is ' +str(c2))
            print ('c3 is ' +str(c3))

            vehicle_ids = traci.vehicle.getIDList()
            vehicle_count += len(vehicle_ids)
            
            for vehicle_id in vehicle_ids:
                #print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                #print(str(vehicle_id))
                ##print(traci.vehicle.getLanePosition(vehicle_id))
                #print(traci.vehicle.getRoadID(vehicle_id))
                vehicle_ids_set.add(vehicle_id)
                total_waiting_time += traci.vehicle.getWaitingTime(vehicle_id)
                total_travel_time += traci.vehicle.getAccumulatedWaitingTime(vehicle_id)
                total_stops += traci.vehicle.getStopState(vehicle_id)
                total_fuel_consumption += traci.vehicle.getFuelConsumption(vehicle_id)
                
                total_emissions["CO"] += traci.vehicle.getCOEmission(vehicle_id)
                total_emissions["CO2"] += traci.vehicle.getCO2Emission(vehicle_id)
                total_emissions["HC"] += traci.vehicle.getHCEmission(vehicle_id)
                total_emissions["NOx"] += traci.vehicle.getNOxEmission(vehicle_id)
                total_emissions["PMx"] += traci.vehicle.getPMxEmission(vehicle_id)
            
            step_queue_length = 0
            for lane_id in traci.lane.getIDList():
                step_queue_length += traci.lane.getLastStepHaltingNumber(lane_id)
            total_queue_length += step_queue_length
            if step_queue_length > max_queue_length:
                max_queue_length = step_queue_length

            #for edge_id in intersection_edges:
            #    intersection_utilization += traci.edge.getLastStepVehicleNumber(edge_id)
            
            step += 1

            if step % output_interval == 0:
                writer.writerow({
                    'step': step,
                    'total_waiting_time': total_waiting_time,
                    'total_travel_time': total_travel_time,
                    'total_stops': total_stops,
                    'total_fuel_consumption': total_fuel_consumption,
                    'CO_emission': total_emissions["CO"],
                    'CO2_emission': total_emissions["CO2"],
                    'HC_emission': total_emissions["HC"],
                    'NOx_emission': total_emissions["NOx"],
                    'PMx_emission': total_emissions["PMx"],
                    'current_queue_length': step_queue_length,
                    'max_queue_length': max_queue_length
                    # 'intersection_utilization': intersection_utilization
                })

    traci.close()

    avg_waiting_time = total_waiting_time / vehicle_count if vehicle_count else 0
    avg_travel_time = total_travel_time / vehicle_count if vehicle_count else 0
    avg_queue_length = total_queue_length / step if step else 0
    throughput = len(vehicle_ids_set) / (step_limit / 3600)  # vehicles per hour

    metrics = {
        "Average Waiting Time": avg_waiting_time,
        "Average Travel Time": avg_travel_time,
        "Average Queue Length": avg_queue_length,
        "Maximum Queue Length": max_queue_length,
        "Throughput (vehicles per hour)": throughput,
        "Total Fuel Consumption": total_fuel_consumption,
        "Total Emissions": total_emissions,
        # "Intersection Utilization": avg_intersection_utilization,
    }

    for metric, value in metrics.items():
        print(f"{metric}: {value}")

if __name__ == "__main__":
    # Run the simulation for 3600 steps (1 hour), output metrics every 600 steps
    run_simulation(3600, 60, r"C:\Users\Pedram\Downloads\mapnewcommunicationpaper\simulation_metrics.csv")
