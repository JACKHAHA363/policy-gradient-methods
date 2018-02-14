import sys
import torch
from collections import namedtuple

# is this efficient?
Transition = namedtuple('Transition', 'state action reward next_state')
MultiTransition = namedtuple('MultiTransition', 'state action reward next_state')

class Trajectory(object):
    """
    Holds a trajectory that is currently being sampled from the environment.
    """
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.transitions = []
        self.dones = []

    def append(self, state_t, action, reward, baseline, log_prob, state_tp1, done=False):
        self.transitions.append(Transition(state_t, action, reward, state_tp1))
        
        if len(self.states) == 0:
            self.states.extend(state_t.data.tolist())

        self.states.extend(state_tp1.data.tolist())
        self.actions.append(action.data.tolist())
        self.rewards.append(reward)
        self.values.append(float(baseline))
        self.log_probs.append(log_prob)
        self.dones.append([done])

    def torchify(self):
        
        trajectory_length = len(self.actions)
        self.actions = torch.FloatTensor(self.actions).view(trajectory_length, -1)
        self.states = torch.FloatTensor(self.states).view(trajectory_length+1, -1)
        self.rewards = torch.FloatTensor(self.rewards).view(trajectory_length, -1)
        self.values = torch.FloatTensor(self.values).view(trajectory_length, -1)
        self.log_probs = torch.stack(self.log_probs).view(trajectory_length, -1)
        self.dones = torch.IntTensor(self.dones).view(trajectory_length, -1)
        self.masks = 1 - self.dones

    def __str__(self):
        return "Trajectory({})".format(self.transitions)

class MultiTrajectory(Trajectory):
    """
    This will store the result of 
    multiple executions of actions in an environment 
    """
    def __init__(self, n_envs):
        """
        :param n_envs: the number of environments
        :param n_steps: the number of steps that a policy is executed for
        """
        self.n_envs = n_envs # does it matter which environment you came from?
        super().__init__()
        self.dones = []
        self.values = []

    def append(self, state_t, action, reward, value_pred, action_log_probs, state_tp1, dones):

        if len(self.states) == 0:
            self.states.append(state_t)
        
        self.dones.append(dones)
        self.states.append(state_tp1)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value_pred)
        self.log_probs.append(action_log_probs)

    def torchify(self):
        trajectory_length = len(self.actions)
        self.actions = torch.stack(self.actions).view(trajectory_length, self.n_envs, -1)
        self.states = torch.stack(self.states).view(trajectory_length+1, self.n_envs, -1)
        self.rewards = torch.stack(self.rewards).view(trajectory_length, self.n_envs, -1)
        self.values = torch.stack(self.values).view(trajectory_length, self.n_envs, -1)
        self.log_probs = torch.stack(self.log_probs).view(trajectory_length, self.n_envs, -1)
        self.dones = torch.stack(self.dones).view(trajectory_length, self.n_envs, -1)
        self.masks = 1 - self.dones