import matplotlib
matplotlib.use('agg')
import pickle
import matplotlib.pyplot as plt
# from scipy.optimize import minimize
import numpy as np
# project imports
from dice_eval import Dice2007cjl as Dice
import numpy as np
import torch
import argparse
import os

import utils
from model import Actor, Critic
import numpy as np
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
import sys
# from demo import *

# make sure this is the same as t_max in dice2007cjl
MAXSTEPS = 600


def var(tensor, volatile=False):
	return Variable(tensor, volatile=volatile)

	# if torch.cuda.is_available():
	# 	return Variable(tensor, volatile=volatile).cuda()
	# else:
	# 	return Variable(tensor, volatile=volatile)

def test_policy(model, critic):
	env = Dice()
	state = env.reset()
	rewards = []
	actions = []
	Q_values = []
	for t in range(MAXSTEPS):
		state = np.float32(state)
		state = Variable(torch.from_numpy(state.reshape(1, 7)))
		action_temp = model.forward(state).detach()
		action = action_temp.data.numpy().reshape(1)
		Q_value = critic.forward(state, action_temp)
		Q_values.append(float(Q_value))
		new_state, reward, done  = env.step(action[0])
		state = new_state
		actions.append(action[0])
		rewards.append(reward)

	plt.figure()
	x = list(range(0, len(Q_values)))
	plt.plot(x, Q_values)
	plt.savefig("Q_values")
	plt.close()
	return rewards, actions

def test_policy_DP(DP_actions):
	env = Dice()
	state = env.reset()
	rewards = []
	counter = 0
	actions = []
	K_list = []
	M_AT_list = []
	M_UP_list = []
	M_LO_list = []
	T_AT_list = []
	T_LO_list = []
	time_list = []
	for step in range(len(DP_actions)):
		# 10 is the stepsize
		for t in range(10):
			if t > 0:
				if step == len(DP_actions)-1:
					action = DP_actions[step] + t * ((DP_actions[step] - DP_actions[step - 1])/10)
				else:
					action = DP_actions[step] + t * ((DP_actions[step + 1] - DP_actions[step])/10)
			else:
				action = DP_actions[step]
			new_state, reward, done  = env.step(action)
			state = new_state
			(K, M_AT, M_UP, M_LO, T_AT, T_LO, time) = new_state
			K_list.append(K)
			M_AT_list.append(M_AT)
			M_UP_list.append(M_UP)
			M_LO_list.append(M_LO)
			T_AT_list.append(T_AT)
			T_LO_list.append(T_LO)
			time_list.append(time)
			actions.append(action)
			rewards.append(reward)
			counter += 1
	# print("K mean/std: ", np.mean(K_list), np.std(K_list))
	# print("M_AT mean/std: ", np.mean(M_AT_list), np.std(M_AT_list))
	# print("M_UP mean/std: ",np.mean(M_UP_list), np.std(M_UP_list))
	# print("M_LO mean/std: ",np.mean(M_LO_list), np.std(M_LO_list))
	# print("T_AT mean/std: ",np.mean(T_AT_list), np.std(T_AT_list))
	# print("T_LO mean/std: ",np.mean(T_LO_list), np.std(T_LO_list))
	# print("time mean/std: ",np.mean(time_list), np.std(time_list))
	return rewards, actions

def random_policy():
	env = Dice()
	state = env.reset()
	rewards = []
	actions = []
	for t in range(MAXSTEPS):
		action = np.random.uniform()
		new_state, reward, done  = env.step(action)
		state = new_state
		rewards.append(reward)
		actions.append(action)
	return rewards, actions

def make_stats(policy_rewards, policy_actions, random_rewards, random_actions, DP_rewards, DP_actions, dp=False):
	print("The sum of rewards of the TRAINED policy is: ", sum(policy_rewards))
	print("The sum of rewards of the RANDOM policy is: ", sum(random_rewards))
	print("The sum of rewards of the DP policy is: ", sum(DP_rewards))

	timevec = list(range(2005, 2005+MAXSTEPS))
	plt.figure()

	plt.subplot(3,2,1)
	random_difference = [random_rewards[i] - DP_rewards[i] for i in range(len(policy_rewards))]

	plt.plot(timevec, random_difference)
	plt.title("Reward for random policy minus DP policy")

	plt.subplot(3,2,2)
	plt.plot(timevec, random_actions)
	plt.title('Mu (action) for random policy')


	plt.subplot(3,2,3)
	policy_difference = [policy_rewards[i] - DP_rewards[i] for i in range(len(policy_rewards))]
	plt.plot(timevec, policy_difference)
	plt.title("Rewards for trained policy minus DP rewards")

	plt.subplot(3,2,4)
	plt.plot(timevec, policy_actions)
	plt.title('Mu (action) for trained policy')

	if dp == True:
		plt.subplot(3,2,5)
		plt.plot(timevec, DP_rewards)
		plt.title("Rewards for DP policy")


		plt.subplot(3,2,6)
		plt.plot(timevec, DP_actions)
		plt.title('Mu (action) for DP policy')

	filename_reward = "test_figure"
	plt.tight_layout()
	plt.savefig(filename_reward)
	plt.close()


if __name__ == '__main__':
	evaluate_episode_number = sys.argv[1]
	# show results of dp, works only for t_max=600
	dp = True
	model = Actor(7, 1, 1)
	critic = Critic(7, 1)

	# Adjust model to load:
	# model.load_state_dict(torch.load('Models/' + str(evaluate_episode_number) + '_actor.pt'))

	model_name = 'actor_RUN-8_user-bestmodel_MEps-100_Bsize-128_LRac-1e-05_LRcr-0.006_Tau-0.001_maxBuf-20000_explRt-0.2.pt'
	model.load_state_dict(torch.load('Models/' +model_name))
	model.eval()

	# model_name = '140_critic_user-hyperLR_MEps-200_Bsize-128_LRac-0.001_LRcr-0.001_Tau-0.001_maxBuf-20000_explRt-0.2.pt'
	model_name = model_name.replace('actor', 'critic')
	# critic.load_state_dict(torch.load('Models/' + str(evaluate_episode_number) + '_critic.pt'))
	critic.load_state_dict(torch.load('Models/' + model_name))
	critic.eval()
	# random model, does not need actor model since policy is random
	random_rewards, random_actions = random_policy()

	# test policy with trained actor model
	policy_rewards, policy_actions = test_policy(model, critic)
	DP_rewards = []
	DP_actions = []
	if dp == True:
		f = open('results.pckl', 'rb')
		DP_actions = pickle.load(f)
		f.close()
		DP_rewards, DP_actions = test_policy_DP(DP_actions.x)
		# print("The mean and variance for normalizing the rewards")
		# print(np.mean(DP_rewards), np.std(DP_rewards))
	make_stats(policy_rewards, policy_actions, random_rewards, random_actions, DP_rewards, DP_actions, dp)
