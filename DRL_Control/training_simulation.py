import traci
import numpy as np
import random
import timeit
import os




class Simulation:
    def __init__(self, Model, Memory, sumo_cmd, gamma, max_steps, green_duration, yellow_duration, num_states, num_actions, training_epochs):
        self._Model = Model
        self._Memory = Memory
        self._gamma = gamma
        self._step = 0
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._num_states = num_states
        self._num_actions = num_actions
        self._reward_store = []
        self._cumulative_wait_store = []
        self._avg_queue_length_store = []
        self._training_epochs = training_epochs


    def run(self, episode, epsilon):
        """
        Runs an episode of simulation, then starts a training session
        """
        start_time = timeit.default_timer()

        # first, generate the route file for this simulation and set up sumo
        #self._TrafficGen.generate_routefile(seed=episode)
        traci.start(self._sumo_cmd)
        print("Simulating...")

        # inits
        self._step = 0
        self._waiting_times = {}
        self._sum_neg_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0
        old_total_wait = 0
        old_state = -1
        old_action = -1

        while self._step < self._max_steps:

            # get current state of the intersection
            current_state ,c14,c2,c3= self._get_state()

            # calculate reward of previous action: (change in cumulative waiting time between actions)
            # waiting time = seconds waited by a car since the spawn in the environment, cumulated for every car in incoming lanes
            current_total_wait = self._collect_waiting_times()
            reward = old_total_wait - current_total_wait

            # saving the data into the memory
            if self._step != 0:
                self._Memory.add_sample((old_state, old_action, reward, current_state))

            # choose the light phase to activate, based on the current state of the intersection
            action = self._choose_action(current_state, epsilon)

            # if the chosen phase is different from the last phase, activate the yellow phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duration,c14,c2,c3)

            # execute the phase selected before
            self._set_green_phase(action)
            self._simulate(self._green_duration,c14,c2,c3)

            # saving variables for later & accumulate reward
            old_state = current_state
            old_action = action
            old_total_wait = current_total_wait

            # saving only the meaningful reward to better see if the agent is behaving correctly
            if reward < 0:
                self._sum_neg_reward += reward

        self._save_episode_stats()
        print("Total reward:", self._sum_neg_reward, "- Epsilon:", round(epsilon, 2))
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        print("Training...")
        start_time = timeit.default_timer()
        for _ in range(self._training_epochs):
            self._replay()
        training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time


    def _simulate(self, steps_todo,c14,c2,c3):
        """
        Execute steps in sumo while gathering statistics
        """
        if (self._step + steps_todo) >= self._max_steps:  # do not do more steps than the maximum allowed number of steps
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1 # update the step counter
            steps_todo -= 1
            queue_length = self._get_queue_length()
            self._sum_queue_length += queue_length+c14+c2+c3
            self._sum_waiting_time += queue_length+c14+c2+c3 # 1 step while wating in queue means 1 second waited, for each car, therefore queue_lenght == waited_seconds


    def _collect_waiting_times(self):
        """
        Retrieve the waiting time of every car in the incoming roads
        """
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


    def _choose_action(self, state, epsilon):
        """
        Decide wheter to perform an explorative or exploitative action, according to an epsilon-greedy policy
        """
        if random.random() < epsilon:
            return random.randint(0, self._num_actions - 1) # random action
        else:
            return np.argmax(self._Model.predict_one(state)) # the best action given the current state


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


    def _get_state(self):
        """
        Retrieve the state of the intersection from sumo, in the form of cell occupancy
        """
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()
        c2=0
        c3=0
        c14=0
        extract_before_underscore = lambda word: word.split('_')[0]

        pedestrian_ids = traci.person.getIDList()
        for pedestrian_id in pedestrian_ids:
            #print(pedestrian_id)
            movement=extract_before_underscore(pedestrian_id)
            #print(movement)
            if movement=='pedestrian1' or movement=='pedestrian3':
                c14+=1
            elif movement=='pedestrian2' or movement=='pedestrian4':
                c2+=1
            elif movement=='pedestrian5' or movement=='pedestrian6':
                c3+=1
            '''
            if traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w2':
                c2+=1
            elif traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w1':
                c3+=1
            elif traci.person.getRoadID(pedestrian_id)==':cluster_49793670_9123357154_9123357155_9428447085_w0':
                c14+=1
            '''
        totalped=len(pedestrian_ids)

        id_to_index = lambda a, b: (a - 1) * 6 + (b - 1)
        sdic={}
        for car_id in car_list:
            lane_pos = traci.vehicle.getLanePosition(car_id)
            #lane_id = traci.vehicle.getLaneID(car_id)
            edge_name=traci.vehicle.getRoadID(car_id)
            #lane_pos = 750 - lane_pos  # inversion of lane pos, so if the car is close to the traffic light -> lane_pos = 0 --- 750 = max len of a road
            weird_road=['1120094388#0' '1120094388#1' '130285156#1' '130285156#2 ']
            if edge_name=='1120094388#0':
                lane_cell=0
            elif edge_name=='1120094388#1':
                lane_cell=1
            elif edge_name=='130285156#1':
                lane_cell=2
            elif edge_name=='130285156#2':
                lane_cell=3
            elif edge_name=='50799230#0':#I street
                if lane_pos<62.5:
                    lane_cell=1
                elif lane_pos<135:
                    lane_cell=2
                else:
                    lane_cell=3
            elif edge_name=='50799230#3':#I street
                if lane_pos<9:
                    lane_cell=3
                else:
                    lane_cell=4
            elif edge_name=='-590598876#1':
                if lane_pos<25:
                    lane_cell=1
                elif lane_pos<50:
                    lane_cell=2
                elif lane_pos<75:
                    lane_cell=3
                else:
                    lane_cell=4
            else:
                lane_cell=101
            movement=extract_before_underscore(car_id)
            if movement=='veh1':
                movement_number=1
            
            elif movement=='veh98':
                movement_number=2

            elif movement=='veh0':
                movement_number=3

            elif movement=='veh55':
                movement_number=4

            elif movement=='veh51':
                movement_number=5
            elif movement=='veh60':
                
                movement_number=6
            #print(edge_name)
            if lane_cell!=101:
                id=id_to_index (lane_cell,movement_number)
                if id not in sdic.keys():
                    sdic[id]=0
                sdic[id]+=1
        vehtopedratio=1
        sdic[24]=c2/vehtopedratio
        sdic[25]=c3/vehtopedratio
        sdic[26]=c14/vehtopedratio
        for id in sdic.keys():
            total=sum(sdic.values())
            if total==0:
                total=1
        
            s=sdic[id]/total
            #print(s)
            state[id] = s 
            #print(state) # write the position of the car car_id in the state array in the form of "cell occupied"
        #state[24]=c2/totalped#/20 if c2<20 else 1
        #state[25]=c3/totalped#/40 if c3<40 else 1
        #state[26]=c14/totalped#/40 if c14<40 else 1
        '''
        if c2>10:
            state[24]==1
        elif c3>15:
            state[25]==1
        elif c14>15:
            state[26]==1
            '''
        return state,c14,c2,c3


    def _replay(self):
        """
        Retrieve a group of samples from the memory and for each of them update the learning equation, then train
        """
        batch = self._Memory.get_samples(self._Model.batch_size)

        if len(batch) > 0:  # if the memory is full enough
            states = np.array([val[0] for val in batch])  # extract states from the batch
            next_states = np.array([val[3] for val in batch])  # extract next states from the batch

            # prediction
            q_s_a = self._Model.predict_batch(states)  # predict Q(state), for every sample
            q_s_a_d = self._Model.predict_batch(next_states)  # predict Q(next_state), for every sample

            # setup training arrays
            x = np.zeros((len(batch), self._num_states))
            y = np.zeros((len(batch), self._num_actions))

            for i, b in enumerate(batch):
                state, action, reward, _ = b[0], b[1], b[2], b[3]  # extract data from one sample
                current_q = q_s_a[i]  # get the Q(state) predicted before
                current_q[action] = reward + self._gamma * np.amax(q_s_a_d[i])  # update Q(state, action)
                x[i] = state
                y[i] = current_q  # Q(state) that includes the updated action value

            self._Model.train_batch(x, y)  # train the NN


    def _save_episode_stats(self):
        """
        Save the stats of the episode to plot the graphs at the end of the session
        """
        self._reward_store.append(self._sum_neg_reward)  # how much negative reward in this episode
        self._cumulative_wait_store.append(self._sum_waiting_time)  # total number of seconds waited by cars in this episode
        self._avg_queue_length_store.append(self._sum_queue_length / self._max_steps)  # average number of queued cars per step, in this episode


    @property
    def reward_store(self):
        return self._reward_store


    @property
    def cumulative_wait_store(self):
        return self._cumulative_wait_store


    @property
    def avg_queue_length_store(self):
        return self._avg_queue_length_store

