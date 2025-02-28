import numpy as np
import tkinter as tk
import copy
import pickle as pickle    # cPickle is available in Python 2.x only, otherwise use pickle

from qo import Game, HumanPlayer, QPlayer


Q = pickle.load(open("Q_epsilon_09_Nepisodes_10000.p", "rb"))

root = tk.Tk()
player1 = HumanPlayer(mark="X")
player2 = QPlayer(mark="O", epsilon=0)

game = Game(root, player1, player2, Q=Q)

game.play()
root.mainloop()