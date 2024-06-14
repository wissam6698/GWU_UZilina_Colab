import traci
import traci.constants as tc
import time

def run_sumo_simulation(cfg_file, simulation_time_step=1.0):
   
    try:
        traci.start(["sumo-gui", "-c", cfg_file]) #remove -gui if simulation needed in the background
        print("SUMO started successfully.")
    except Exception as e:
        print(f"Failed to start SUMO: {e}")
        return

    # Simulation loop
    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()  # Advance the simulation by one time step
            
            vehicle_ids = traci.vehicle.getIDList()
            print(f"Number of vehicles in the simulation: {len(vehicle_ids)}")
            
            # Example interaction: Print positions of all vehicles
            for vehicle_id in vehicle_ids:
                position = traci.vehicle.getPosition(vehicle_id)
                print(f"Vehicle {vehicle_id} position: {position}")

           
            time.sleep(simulation_time_step)

    except Exception as e:
        print(f"Error during simulation: {e}")

    finally:
        traci.close()
        print("SUMO simulation ended.")

if __name__ == "__main__":
   
    cfg_file = r"C:\Users\12028\Downloads\GWUUZilinaColab\map.sumo.cfg"  # Update path
    simulation_time_step = 1.0  # Time step in seconds
    run_sumo_simulation(cfg_file, simulation_time_step)
