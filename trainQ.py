import numpy as np
import tkinter as tk
import copy
import pickle
from qo import Game, QPlayer     # Classes used for BOOP

root = tk.Tk()
epsilon = 0.9
player1 = QPlayer(mark="X",epsilon = epsilon)
player2 = QPlayer(mark="O",epsilon = epsilon)
game = Game(root, player1, player2)

N_episodes = 100000
for episodes in range(N_episodes):
    game.play()
    game.reset()

Q = game.Q

filename = "Q_epsilon_09_Nepisodes_{}.p".format(N_episodes)
pickle.dump(Q, open(filename, "wb"))