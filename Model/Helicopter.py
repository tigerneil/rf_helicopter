# Purpose: Class that Controls the Movement of the Agent
#
#   Info: Main Function for linking classes togeather
#
#   Developed as part of the Software Agents Course at City University
#
#   Dev: Dan Dixey and Enrico Lopedoto
#
#
import logging
from random import sample

import numpy as np

import Q_Learning_Agent as Q
from Agent import agent_controls


class helicopter(agent_controls):
    """

    Class that Controls, interacts and links all the other classes togeather

        Q-Learning, Agent Movements, World

    """

    def __init__(self, world, settings):
        agent_controls.__init__(self)
        self.ai = None
        self.model_version = settings['model']
        self.world = world
        self.settings = settings
        # Load in the Agent
        self._create_agent()
        # Agent Metrics
        self.crashed = 0
        self.completed = 0
        # Storing States
        self.lastState = None
        self.current_state = None
        # Storing Locations
        self.origin = (world.st_x, world.st_y)
        self.current_location = self.origin
        self.previous_location = None
        # Storing Actions
        self.lastAction = None
        # Agents Info
        self.final_location = []
        self.q_matrix = []  # Q-Matrix state(p) vs state(c) - Q-Value
        self.r_matrix = []  # R_Matrix state(c) vs Action  - Reward
        self.trial_n = 1
        # Recording States
        self.state_record = []
        # Reward Functions
        self.reward_completed = settings['completed']
        self.reward_crashed = settings['crashed']
        self.reward_no_obstacle = settings['open']
        self.reward_sum = 0
        self.prev_reward = None
        self.new_state = None
        self.vals = [int(self.world.track_width * 0.92),
                     int(self.world.track_width * 0.4),
                     int(self.world.track_width * 0.5),
                     int(self.world.track_width * 0.98),
                     int(self.world.track_width * 0.6),
                     int(self.world.track_width * 0.7),
                     int(self.world.track_width * 0.8),
                     int(self.world.track_width * 0.95),
                     int(self.world.track_width * 0.2),
                     int(self.world.track_width * 0.1),
                     int(self.world.track_width * 0.99)]

    def _create_agent(self):
        """
        Loads the Respective Model
        """
        if self.model_version == 1:
            self.ai = Q.Q_Learning_Algorithm(settings=self.settings)

        elif self.model_version == 2:
            self.ai = Q.Q_Learning_Epsilon_Decay(settings=self.settings)

        elif self.model_version == 3:
            self.ai = Q.Q_Neural_Network(settings=self.settings,
                                         track_height=self.world.track_height)

    def update(self):
        """
        Increment the Agent in the World by one

        :return: Boolean
        """
        # Get the Current State
        location = self.current_location
        world_val = self.world.check_location(location[0],
                                              location[1])
        state = self.find_states(self.current_location)
        # Record State
        self.state_record.append(state)

        # Is Current State Obstacle?
        if world_val == -1:
            logging.debug(
                "------------Helicopter Crashed on the Course-----------")
            self.crashed += 1
            self.reward_sum += self.reward_crashed
            self.prev_reward = self.reward_crashed

            if self.model_version == 3:  # Neural Network
                self.ai.update_train(p_state=self.lastState,
                                     action=self.lastAction,
                                     p_reward=self.reward_no_obstacle,
                                     new_state=state,
                                     terminal=[self.reward_completed,
                                               self.reward_crashed])

            if self.lastState is not None and self.model_version != 3:
                self.ai.learn(
                    self.lastState,
                    self.lastAction,
                    self.reward_crashed,
                    state)

            self.final_location.append([self.current_location[0],
                                        self.trial_n,
                                        self.current_location[1],
                                        self.reward_sum])
            self.r_matrix.append([self.lastState,
                                  self.lastAction,
                                  self.reward_crashed])
            self.q_matrix.append([self.lastState,
                                  state,
                                  self.reward_crashed])
            self.trial_n += 1
            # Agent Crashed - Reset the world
            return False

        # Is the Current State on the Finish Line?
        if world_val == 10:
            logging.debug("-----------Helicopter Completed Course-----------")
            self.completed += 1
            self.reward_sum += self.reward_completed
            self.prev_reward = self.reward_completed

            if self.model_version == 3:  # Neural Network
                self.ai.update_train(p_state=self.lastState,
                                     action=self.lastAction,
                                     p_reward=self.reward_no_obstacle,
                                     new_state=state,
                                     terminal=[self.reward_completed,
                                               self.reward_crashed])

            if self.lastState is not None and self.model_version != 3:
                self.ai.learn(self.lastState,
                              self.lastAction,
                              self.reward_completed,
                              state)

            self.final_location.append([self.current_location[0],
                                        self.trial_n,
                                        self.current_location[1],
                                        self.reward_sum])
            self.r_matrix.append([self.lastState,
                                  self.lastAction,
                                  self.reward_completed])
            self.trial_n += 1
            # Agent Completed Course - Reset the world
            return False

        # Is the Current in the Open - Continue Journey
        self.reward_sum += self.reward_no_obstacle
        self.prev_reward = self.reward_no_obstacle

        if self.lastState is not None and self.model_version != 3:
            self.ai.learn(self.lastState,
                          self.lastAction,
                          self.reward_no_obstacle,
                          state)

        # Select an Action
        if self.model_version < 3:
            action = self.ai.choose_Action(state)
        else:
            action = self.ai.choose_Action(state=state,
                                           pstate=self.lastState,
                                           paction=self.lastAction,
                                           preward=self.reward_no_obstacle)

        self.r_matrix.append([self.lastState,
                              self.lastAction,
                              self.reward_no_obstacle])
        self.q_matrix.append([self.lastState,
                              state,
                              self.reward_no_obstacle])
        self.lastState = state
        self.lastAction = action
        # Move Depending on the Wind at the current location
        self.current_location = self.action_wind(world_val,
                                                 self.current_location)

        if self.current_location is None:
            return False

        # Move Depending on the Action from Q-Learning
        self.current_location = self.action_move(action,
                                                 self.current_location)
        self.new_state = state

        if self.model_version == 3:  # Neural Network
            self.ai.update_train(p_state=self.lastState,
                                 action=self.lastAction,
                                 p_reward=self.reward_no_obstacle,
                                 new_state=state,
                                 terminal=[self.completed,
                                           self.crashed])
        return True

    def reset(self):
        """
        If the Agents requires a restart then reload parameters

        """
        if self.settings['train']:
            self.current_location = (
                self.origin[0] + sample(self.vals, 1)[0],
                self.origin[1])
        else:
            self.current_location = self.origin

        self.previous_location = None
        self.lastAction = None
        self.lastState = None
        self.current_state = None
        self.reward_sum = 0

    def find_states(self, location):
        """
        Find the State given the Agents current location

        :param location: tuple(int, int)
        :return: tuple(int,....)
        """
        x, y = location[0], location[1]
        state_space = list()

        # Increase from 1 to 0
        for i in range(0, 3):

            for j in range(-2, 3):
                value = self.world.check_location(x=x + i,
                                                  y=y + j)
                state_space.append(value)

        # Add the current height into the state space.
        # state_space.append(y)
        return tuple(state_space)

    def return_q_view(self):
        """
        Function to retrieve the Q-Values of the Current Location

        :return: (int, np.array)
        """
        qw_mat = self.model_view()
        start = int(self.current_location[1])
        array1 = np.zeros(shape=(1, self.world.track_height + 3))
        array3 = np.array(qw_mat)
        array2 = np.ma.masked_array(array3, mask=[5])

        # Dealing with Edge Plotting
        lower = max(start - 2, 0)
        upper = min(start + 3, self.world.track_height + 1)
        array1[0, lower:upper] = array2[:upper - lower]

        return min(self.current_location[0], self.world.track_width), \
            array1[0, :self.world.track_height]

    def model_view(self):
        """
        Get the Q-Values of the Current Location

        :return: list/np.array
        """
        view_current = self.q_matrix[- 1][1]
        qw_mat = []

        if self.model_version < 3:

            for i in range(self.settings['nb_actions']):
                key = (view_current, i + 1)

                if key not in list(self.ai.q.keys()):
                    qw_mat.append(0)
                else:
                    qw_mat.append(self.ai.q[key])
        else:
            state = np.concatenate(
                (list(
                    self.lastState), [
                    self.lastAction], [
                    self.ai.reward_change[
                        self.prev_reward]], list(
                        self.new_state))) + 1
            state = np.asarray(state).reshape(1, self.ai.input_dim)
            qw_mat = self.ai.model.predict(state, batch_size=1)

        return qw_mat
