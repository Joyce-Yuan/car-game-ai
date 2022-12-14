import torch 
import random 
import numpy as np
from collections import deque
from car_gameai import CarGameAI,Direction,BLOCK_SIZE
from model import Linear_QNet,QTrainer
from Helper import plot
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_game = 0
        self.epsilon = 0 # Randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(7,256,5) 
        self.trainer = QTrainer(self.model,lr=LR,gamma=self.gamma)
        # for n,p in self.model.named_parameters():
        #     print(p.device,'',n) 
        # self.model.to('cuda')   
        # for n,p in self.model.named_parameters():
        #     print(p.device,'',n)         
        # TODO: model,trainer

    # state (7 Values)
    #[ main car x, main car y, main car speed
    # 
    # car in front
    # car 1 x, car 1 y
    # 
    # car opposing
    # car 2 x, car 2 y]
    def get_state(self,game):
        state = [
            game.main.x,
            game.main.y,
            game.main.speed,

            game.car1.x,
            game.car1.y,

            game.car2.x,
            game.car2.y,
        ]

        return np.array(state,dtype=int)

    def remember(self,state,action,reward,next_state,done):
        self.memory.append((state,action,reward,next_state,done)) # popleft if memory exceed

    def train_long_memory(self):
        if (len(self.memory) > BATCH_SIZE):
            mini_sample = random.sample(self.memory,BATCH_SIZE)
        else:
            mini_sample = self.memory
        states,actions,rewards,next_states,dones = zip(*mini_sample)
        self.trainer.train_step(states,actions,rewards,next_states,dones)

    def train_short_memory(self,state,action,reward,next_state,done):
        self.trainer.train_step(state,action,reward,next_state,done)

    def get_action(self,state):
        # random moves: tradeoff explotation / exploitation
        self.epsilon = 80 - self.n_game
        final_move = 0
        if(random.randint(0,200)<self.epsilon):
            final_move = random.randint(0,4)
        else:
            state0 = torch.tensor(state,dtype=torch.float) #.cuda()
            prediction = self.model(state0) #.cuda() # prediction by model 
            move = torch.argmax(prediction).item()
            final_move = move
        print(f'move= {final_move}')
        return final_move

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = CarGameAI()
    while True:
        # Get Old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old,final_move,reward,state_new,done)

        #remember
        agent.remember(state_old,final_move,reward,state_new,done)

        if done:
            # Train long memory,plot result
            game.start_over()
            agent.n_game += 1
            agent.train_long_memory()
            if(score > reward): # new High score 
                reward = score
                agent.model.save()
            print('Game:',agent.n_game,'Score:',score,'Record:',record)
            
            plot_scores.append(score)
            total_score+=score
            mean_score = total_score / agent.n_game
            plot_mean_scores.append(mean_score)
            plot(plot_scores,plot_mean_scores)


if(__name__=="__main__"):
    train()