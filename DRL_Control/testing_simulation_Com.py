import traci
import numpy as np
import random
import timeit
import os
import time
# phase codes based on environment.net.xml
PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7


class Simulation:
    def __init__(self, Model,  sumo_cmd, max_steps, green_duration, yellow_duration, num_states, num_actions):
        self._Model = Model
        self._step = 0
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._num_states = num_states
        self._num_actions = num_actions
        self._reward_episode = []
        self._queue_length_episode = []


    def run(self, episode):
        """
        Runs the testing simulation
        """
        start_time = timeit.default_timer()

        # first, generate the route file for this simulation and set up sumo
        #self._TrafficGen.generate_routefile(seed=episode)
        traci.start(self._sumo_cmd)
        print("Simulating...")

        # inits
        self._step = 0
        self._waiting_times = {}
        old_total_wait = 0
        old_action = -1 # dummy init
        totalwaitingtime=0
        while self._step < self._max_steps:

            # get current state of the intersection
            current_state, c14,c2,c3= self._get_state()
            print(self._step)
            # calculate reward of previous action: (change in cumulative waiting time between actions)
            # waiting time = seconds waited by a car since the spawn in the environment, cumulated for every car in incoming lanes
            totalwaitingtime+=self._collect_waiting_times()
            current_total_wait = self._collect_waiting_times()
            reward = old_total_wait - current_total_wait

            # choose the light phase to activate, based on the current state of the intersection
            action = self._choose_action(current_state)

            # if the chosen phase is different from the last phase, activate the yellow phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duration,c14,c2,c3)

            # execute the phase selected before
            self._set_green_phase(action)
            self._simulate(self._green_duration,c14,c2,c3)

            # saving variables for later & accumulate reward
            old_action = action
            old_total_wait = current_total_wait

            self._reward_episode.append(reward)

        #print("Total reward:", np.sum(self._reward_episode))
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time,totalwaitingtime


    def _simulate(self, steps_todo,c14,c2,c3):
        """
        Proceed with the simulation in sumo
        """
        if (self._step + steps_todo) >= self._max_steps:  # do not do more steps than the maximum allowed number of steps
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1 # update the step counter
            steps_todo -= 1
            queue_length = self._get_queue_length() +c14+c2+c3
            self._queue_length_episode.append(queue_length)



    def _collect_waiting_times(self):
        """
        Retrieve the waiting time of every car in the incoming roads
        """
        incoming_roads = ["E2TL", "N2TL", "W2TL", "S2TL"]
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)  # get the road id where the car is located
            self._waiting_times[car_id] = wait_time
        pedestrian_ids = traci.person.getIDList()
        for pedestrian_id in pedestrian_ids:
            wait_time = traci.person.getWaitingTime(pedestrian_id)
            self._waiting_times[pedestrian_id] = wait_time
        total_waiting_time = sum(self._waiting_times.values())
        return total_waiting_time


    def _choose_action(self, state):
        """
        Pick the best action known based on the current state of the env
        """
        return np.argmax(self._Model.predict_one(state))


    def _set_yellow_phase(self, old_action):
        """
        Activate the correct yellow light combination in sumo
        """
        yellow_phase_code = old_action * 2 + 1 # obtain the yellow phase code, based on the old action (ref on environment.net.xml)
        traci.trafficlight.setPhase("cluster_49793670_9123357154_9123357155_9428447085", 1)


    def _set_green_phase(self, action_number):
        """
        Activate the correct green light combination in sumo
        """
        if action_number == 0:
            traci.trafficlight.setPhase("cluster_49793670_9123357154_9123357155_9428447085", 0)
        elif action_number == 1:
            traci.trafficlight.setPhase("cluster_49793670_9123357154_9123357155_9428447085", 3)
        elif action_number == 2:
            traci.trafficlight.setPhase("cluster_49793670_9123357154_9123357155_9428447085", 6)



    def _get_queue_length(self):
        """
        Retrieve the number of cars with speed = 0 in every incoming lane
        """
        edge1 = traci.edge.getLastStepHaltingNumber("-590598876#1")
        edge2 = traci.edge.getLastStepHaltingNumber("50799230#3")
        edge3 = traci.edge.getLastStepHaltingNumber("50799230#0")
        edge4 = traci.edge.getLastStepHaltingNumber("130285156#2")
        
        edge5 = traci.edge.getLastStepHaltingNumber("130285156#1")
        edge6 = traci.edge.getLastStepHaltingNumber("1120094388#1")
        queue_length = edge1+edge2+edge3+edge4+edge5+edge6
        return queue_length




    def _get_state(self, penetration_rate, message_frequency):
        """
        Retrieve the state of the intersection from OMNeT++ simulation, in the form of cell occupancy.
        Adjust the penetration rate of connected vehicles and the message sending frequency.
        """
        pick_elements = lambda lst, factor: random.sample(lst, int(len(lst) * factor))
        extract_before_underscore = lambda word: word.split('_')[0]

        state = np.zeros(self._num_states)
        start = time.time()

        # Adjust penetration rate and message frequency in OMNeT++

        # Simulate fetching pedestrian data from OMNeT++
        pedestrian_ids = self.get_pedestrian_ids_from_omnet()
        pedestrian_ids = pick_elements(pedestrian_ids, penetration_rate)
        pedestrian_ids= self.simulate_message_frequency(self, pedestrian_ids, message_frequency,minfrequency,maxfrequency)
        print(time.time() - start)

        c2, c3, c14 = 0, 0, 0
        for pedestrian_id in pedestrian_ids:
            movement = extract_before_underscore(pedestrian_id)
            if movement in ['ped1', 'ped3']:
                c14 += 1
            elif movement in ['ped2', 'ped4']:
                c2 += 1
            elif movement in ['ped5', 'ped6']:
                c3 += 1

        totalped = len(pedestrian_ids)

        id_to_index = lambda a, b: (a - 1) * 6 + (b - 1)
        sdic = {}

        # Simulate fetching vehicle data from OMNeT++
        car_list = self.get_vehicle_ids_from_omnet()
        car_list = pick_elements(car_list, penetration_rate)
        car_list= self.omnet_recieved_messages(car_list,message_frequency)
        for car_id in car_list:
            lane_pos = self.get_vehicle_lane_position_from_omnet(car_id)
            edge_name = self.get_vehicle_road_id_from_omnet(car_id)

            lane_cell = 101  # Default value if not found in any conditions
            if edge_name == '1120094388#0':
                lane_cell = 0
            elif edge_name == '1120094388#1':
                lane_cell = 1
            elif edge_name == '130285156#1':
                lane_cell = 2
            elif edge_name == '130285156#2':
                lane_cell = 3
            elif edge_name == '50799230#0':  # I street
                if lane_pos < 62.5:
                    lane_cell = 1
                elif lane_pos < 135:
                    lane_cell = 2
                else:
                    lane_cell = 3
            elif edge_name == '50799230#3':  # I street
                if lane_pos < 9:
                    lane_cell = 3
                else:
                    lane_cell = 4
            elif edge_name == '-590598876#1':
                if lane_pos < 25:
                    lane_cell = 1
                elif lane_pos < 50:
                    lane_cell = 2
                elif lane_pos < 75:
                    lane_cell = 3
                else:
                    lane_cell = 4

            movement = extract_before_underscore(car_id)
            movement_dict = {'veh1': 1, 'veh98': 2, 'veh0': 3, 'veh55': 4, 'veh51': 5, 'veh60': 6}
            movement_number = movement_dict.get(movement, None)

            if movement_number is not None and lane_cell != 101:
                id = id_to_index(lane_cell, movement_number)
                if id not in sdic:
                    sdic[id] = 0
                sdic[id] += 1

        # Update pedestrian data
        vehtopedratio = 1
        sdic[24] = c2 / vehtopedratio
        sdic[25] = c3 / vehtopedratio
        sdic[26] = c14 / vehtopedratio

        # Normalize and update the state
        total = sum(sdic.values())
        total = total if total != 0 else 1  # Avoid division by zero

        for id in sdic.keys():
            s = sdic[id] / total
            state[id] = s

        return state, c14, c2, c3

def simulate_message_frequency(self, ids, frequency_hz, min_frequency, max_frequency):
    """
    Simulate the message sending frequency for a given list of IDs (e.g., pedestrians or vehicles).
    The frequency is given in Hz and mapped to a probability based on the min and max frequency.
    """
    # Map frequency to a probability
    if frequency_hz < min_frequency:
        probability = 0.0
    elif frequency_hz > max_frequency:
        probability = 1.0
    else:
        probability = (frequency_hz - min_frequency) / (max_frequency - min_frequency)

    filtered_ids = []
    for id in ids:
        if random.random() < probability:
            filtered_ids.append(id)
    return filtered_ids

    # Placeholder functions for OMNeT++ integration
    def get_pedestrian_ids_from_omnet(self):
        # Replace this with actual code to get pedestrian IDs from OMNeT++
        return traci.person.getIDList()

    def get_vehicle_ids_from_omnet(self):
        # Replace this with actual code to get vehicle IDs from OMNeT++
        return traci.vehicle.getIDList()

    def get_vehicle_lane_position_from_omnet(self, car_id):
        # Replace this with actual code to get vehicle lane position from OMNeT++
        return traci.vehicle.getLanePosition(car_id)

    def get_vehicle_road_id_from_omnet(self, car_id):
        # Replace this with actual code to get vehicle road ID from OMNeT++
        return traci.vehicle.getRoadID(car_id)

    def omnet_recieved_messages(self,car_list,frequency):
        return car_list #the cars that were able to send the message 

    def set_message_frequency_in_omnet(self, message_frequency):
        # Replace this with actual code to set message frequency in OMNeT++
        pass
