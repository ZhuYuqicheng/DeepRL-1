import torch
import torch.distributions as dist
import torch.nn.functional as F
import numpy as np
from algorithms import OffPolicy, BaseRL
from models import CrossEntropyGuidedPolicy, DeterministicPolicy, ActionValueFunction

class CGP(BaseRL, OffPolicy):
    def __init__(self, env, param=None):
        super(CGP, self).__init__(env, param=param)        
        self.name = "CGP"
        self.Q = ActionValueFunction(self.param.qvalue, self.device)
        self.actor_cem = CrossEntropyGuidedPolicy(self.Q.Q1, self.param.policy, self.device)
        self.actor_target = CrossEntropyGuidedPolicy(self.Q.Q1_target, self.param.policy, self.device)
        self.actor = DeterministicPolicy(self.param.policy, self.device)
        self.steps = 0

    def act(self, state, deterministic=False):
        self.steps += 1
        with torch.no_grad():
            if deterministic:
                action = self.actor(torch.from_numpy(state).float().to(self.device)).cpu().numpy()
            else:    
                action = self.actor_cem(state)
                # if self.param.POLICY_EXPLORATION_NOISE != 0:
                #     action += torch.randn(action.shape).to(self.device) * self.param.POLICY_EXPLORATION_NOISE 
                #     action = action.cpu().numpy()
                #     action = np.clip(action, self.env.action_space.low, self.env.action_space.high)
                # else:
                    # action = action.cpu().numpy()
                    # action = np.clip(action, self.env.action_space.low, self.env.action_space.high)
        next_state, reward, done, _ = self.env.step(action)
        self.memory.store(state, action, reward, next_state, done) 
        return next_state, reward, done


    @OffPolicy.loop
    def learn(self):
        batch = self.offPolicyData 

        # Target Policy Smoothing
        noise = torch.randn(batch['actions'].shape).to(self.device) * self.param.POLICY_UPDATE_NOISE
        noise = torch.clamp(noise, -self.param.POLICY_CLIP, self.param.POLICY_CLIP)
        next_actions = self.actor_target(batch['next_states'].numpy()) + noise

        # Update Q-Function
        with torch.no_grad():
            q1_next, q2_next = self.Q.target(batch['next_states'], next_actions) 
            q_targets = batch['rewards'] + self.param.GAMMA * torch.min(q1_next, q2_next)
        q1, q2 = self.Q(batch['states'], batch['actions'])
        critic_loss = F.mse_loss(q1, q_targets) + F.mse_loss(q2, q_targets) 
        self.Q.optimize(critic_loss)

        # Actor Step
        if self.steps % self.param.POLICY_UPDATE_FREQ == 0:
            actions = self.actor(batch['states'])
            targets = self.actor_cem(batch['states'].numpy())
            actor_loss = F.mse_loss(actions, targets)
            self.actor.optimize(actor_loss)

        # Return Metrics
        metrics = dict()
        # if self.steps % 5000 == 0:
            # data = self.memory.sample(5000)
            # states = data['states']
            # actions = self.actor(states)
            # q, _ = self.Q(states, actions)
            # metrics['value'] = q.mean().item()
        return metrics