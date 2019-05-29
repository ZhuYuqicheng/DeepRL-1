import os
import inspect
import numpy
import torch
import torch.optim as optim
from copy import deepcopy
from algorithms import RLAlgorithm, HyperParameter
from utils.models import Policy, Value, QValue
from utils.helper import soft_target_update
from utils.memory import ReplayBuffer

class SAC(RLAlgorithm):
    def __init__(self, env):
        super(SAC,self).__init__(env)
        self.name = "SAC"

        parameters_file = os.path.dirname(inspect.getfile(self.__class__)) + '/parameters.json'
        self.param = HyperParameter(parameters_file)
        self.param.ARCHITECTURE[ 0 ] = self.state_dim
        self.param.ARCHITECTURE[-1 ] = self.action_dim
        architecture = self.param.ARCHITECTURE
        activation = self.param.ACTIVATION

        self.actor = Policy(architecture, activation, action_space=self.action_space)
        self.actor_optim = optim.Adam(self.actor.parameters(), lr=self.param.LEARNING_RATE)
        self.vcritic = Value(architecture, activation)
        self.vcritic_target = deepcopy(self.vcritic)
        self.vcritic_optim = optim.Adam(self.vcritic.parameters(), lr=self.param.LEARNING_RATE)
        self.qcritic1 = QValue(architecture, activation) 
        self.qcritic2 = QValue(architecture, activation) 
        self.qritics_optim = optim.Adam(list(self.qcritic1.parameters()) + list(self.qcritic2.parameters()), lr=self.param.LEARNING_RATE)
        
        self.replay_buffer = ReplayBuffer(int(self.param.MEMORY_SIZE), self.rng)
        self.steps = 0

    
    def act(self, state, exploit=False):
        policy = self.actor(torch.from_numpy(state).float())
        if exploit:
            action = policy.mean.detach()
        else:
            action = policy.sample()
        next_state, reward, done, _ = self.env.step(action.numpy()) 
        self.replay_buffer.push(state, action, reward, next_state, done)
        self.steps += 1
        if done:
            next_state = self.env.reset()
        return next_state, reward, done
    

    
    def learn(self):
        if len(self.replay_buffer) > 10000:
            transitions = self.replay_buffer.sample(self.param.BATCH_SIZE)
            state_batch = torch.Tensor(transitions.state)
            next_state_batch = torch.Tensor(transitions.next_state)
            action_batch = torch.Tensor(transitions.action)
            reward_batch = torch.Tensor(transitions.reward)
            mask_batch = torch.Tensor(transitions.mask)

            Q_target = reward_batch + self.param.GAMMA * mask_batch * self.vcritic_target(next_state_batch).squeeze()
            policy = self.actor(state_batch)
            actions = policy.rsample()
            entropy = 0.2 * policy.log_prob(actions).squeeze()
            Q1 = self.qcritic1(state_batch, actions.detach()).squeeze()
            Q2 = self.qcritic2(state_batch, actions.detach()).squeeze()
            V_target = torch.min(Q1, Q2) - entropy.detach()

            Q_loss = (self.qcritic1(state_batch, action_batch.unsqueeze(1)).squeeze() - Q_target).pow(2).mean() + \
                    (self.qcritic2(state_batch, action_batch.unsqueeze(1)).squeeze() - Q_target).pow(2).mean()
            self.qritics_optim.zero_grad()
            Q_loss.backward()
            self.qritics_optim.step()

            V_loss = (self.vcritic(state_batch).squeeze() - V_target).pow(2).mean()
            self.vcritic_optim.zero_grad()
            V_loss.backward()
            self.vcritic_optim.step()

            policy_loss = (entropy - self.qcritic1(state_batch, actions).squeeze()).mean()
            self.actor_optim.zero_grad()
            policy_loss.backward()
            self.actor_optim.step()

            soft_target_update(self.vcritic, self.vcritic_target, self.param.TAU)



    def seed(self, seed):
        pass

    def reset(self):
        pass