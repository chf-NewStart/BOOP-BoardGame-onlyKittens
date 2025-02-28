import numpy as np
import tkinter as tk
import copy
import pickle as pickle    # cPickle is for Python 2.x only; in Python 3, simply "import pickle" and the accelerated version will be used automatically if available

class Game:
    def __init__(self, master, player1, player2, Q_learn=None, Q={}, alpha=0.3, gamma=0.9):
        frame = tk.Frame()
        frame.grid()
        self.master = master
        master.title("Tic Tac Toe")

        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.other_player = player2
        self.empty_text = ""
        self.board = Board()

        self.buttons = [[None for _ in range(6)] for _ in range(6)]
        for i in range(6):
            for j in range(6):
                self.buttons[i][j] = tk.Button(frame, height=2, width=4, text=self.empty_text, command=lambda i=i, j=j: self.callback(self.buttons[i][j]))
                self.buttons[i][j].grid(row=i, column=j)

        self.reset_button = tk.Button(text="Reset", command=self.reset)
        self.reset_button.grid(row=3)

        self.Q_learn = Q_learn
        if self.Q_learn:
            self.Q = Q
            self.alpha = alpha          # Learning rate
            self.gamma = gamma          # Discount rate
            self.share_Q_with_players()

    @property
    def Q_learn(self):
        if self._Q_learn is not None:
            return self._Q_learn
        if isinstance(self.player1, QPlayer) or isinstance(self.player2, QPlayer):
            return True

    @Q_learn.setter
    def Q_learn(self, _Q_learn):
        self._Q_learn = _Q_learn

    def share_Q_with_players(self):             # The action value table Q is shared with the QPlayers to help them make their move decisions
        if isinstance(self.player1, QPlayer):
            self.player1.Q = self.Q
        if isinstance(self.player2, QPlayer):
            self.player2.Q = self.Q

    def callback(self, button):
        if self.board.over():
            pass                # Do nothing if the game is already over
        else:
            if isinstance(self.current_player, HumanPlayer) and isinstance(self.other_player, HumanPlayer):
                if self.empty(button):
                    move = self.get_move(button)
                    self.handle_move(move)
            elif isinstance(self.current_player, HumanPlayer) and isinstance(self.other_player, ComputerPlayer):
                computer_player = self.other_player
                if self.empty(button):
                    human_move = self.get_move(button)
                    self.handle_move(human_move)
                    if not self.board.over():               # Trigger the computer's next move
                        computer_move = computer_player.get_move(self.board)
                        self.handle_move(computer_move)

    def empty(self, button):
        return button["text"] == self.empty_text

    def get_move(self, button):
        info = button.grid_info()
        move = (int(info["row"]), int(info["column"]))                # Get move coordinates from the button's metadata
        return move

    def handle_move(self, move):
        if self.Q_learn:
            self.learn_Q(move)
        i, j = move         # Get row and column number of the corresponding button
        self.buttons[i][j].configure(text=self.current_player.mark)     # Change the label on the button to the current player's mark
        self.board.place_mark(move, self.current_player.mark)           # Update the board
        self.push_adjacent(i, j, self.current_player.mark)

        if self.board.over():
            self.declare_outcome()
        else:
            self.switch_players()

    def push_adjacent(self, row, col, mark):
        """Push adjacent marks one step in the same direction. If at edge, push off the board."""
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Up, Down, Left, Right
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        ]

        for dr, dc in directions:
            new_r, new_c = row + dr, col + dc  # Check adjacent cell

            if 0 <= new_r < 6 and 0 <= new_c < 6:  # Ensure within bounds
                if not np.isnan(self.board.grid[new_r, new_c]):  # If there's a piece
                    push_r, push_c = new_r + dr, new_c + dc  # Where to push it

                    if 0 <= push_r < 6 and 0 <= push_c < 6:
                        if np.isnan(self.board.grid[push_r, push_c]):  # If space is empty, push
                            self.board.grid[push_r, push_c] = self.board.grid[new_r, new_c]
                            self.buttons[push_r][push_c].configure(text=self.buttons[new_r][new_c]["text"])
                            
                            # clear original piece
                            self.board.grid[new_r, new_c] = np.nan
                            self.buttons[new_r][new_c].configure(text=self.empty_text)  # Clear button UI
                    
                    # If pushing off the board (out of bounds)
                    else:
                        self.board.grid[new_r, new_c] = np.nan
                        self.buttons[new_r][new_c].configure(text=self.empty_text)  # Clear button UI


    def declare_outcome(self):
        if self.board.winner() is None:
            print("Cat's game.")
        else:
            print(("The game is over. The player with mark {mark} won!".format(mark=self.current_player.mark)))

    def reset(self):
        print("Resetting...")
        for i in range(6):
            for j in range(6):
                self.buttons[i][j].configure(text=self.empty_text)
        self.board = Board(grid=np.ones((6,6))*np.nan)
        self.current_player = self.player1
        self.other_player = self.player2
        # np.random.seed(seed=0)      # Set the random seed to zero to see the Q-learning 'in action' or for debugging purposes
        self.play()

    def switch_players(self):
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.other_player = self.player1
        else:
            self.current_player = self.player1
            self.other_player = self.player2

    def play(self):
        if isinstance(self.player1, HumanPlayer) and isinstance(self.player2, HumanPlayer):
            pass        # For human vs. human, play relies on the callback from button presses
        elif isinstance(self.player1, HumanPlayer) and isinstance(self.player2, ComputerPlayer):
            pass
        elif isinstance(self.player1, ComputerPlayer) and isinstance(self.player2, HumanPlayer):
            first_computer_move = self.player1.get_move(self.board)      # If player 1 is a computer, it needs to be triggered to make the first move.
            self.handle_move(first_computer_move)
        elif isinstance(self.player1, ComputerPlayer) and isinstance(self.player2, ComputerPlayer):
            while not self.board.over():        # Make the two computer players play against each other without button presses
                self.play_turn()

    def play_turn(self):
        move = self.current_player.get_move(self.board)
        self.handle_move(move)

    def learn_Q(self, move):                        # If Q-learning is toggled on, "learn_Q" should be called after receiving a move from an instance of Player and before implementing the move (using Board's "place_mark" method)
        state_key = QPlayer.make_and_maybe_add_key(self.board, self.current_player.mark, self.Q)
        next_board = self.board.get_next_board(move, self.current_player.mark)
        reward = next_board.give_reward()
        next_state_key = QPlayer.make_and_maybe_add_key(next_board, self.other_player.mark, self.Q)
        if next_board.over():
            expected = reward
        else:
            next_Qs = self.Q[next_state_key]             # The Q values represent the expected future reward for player X for each available move in the next state (after the move has been made)
            if self.current_player.mark == "X":
                expected = reward + (self.gamma * min(next_Qs.values()))        # If the current player is X, the next player is O, and the move with the minimum Q value should be chosen according to our "sign convention"
            elif self.current_player.mark == "O":
                expected = reward + (self.gamma * max(next_Qs.values()))        # If the current player is O, the next player is X, and the move with the maximum Q vlue should be chosen
        change = self.alpha * (expected - self.Q[state_key][move])
        self.Q[state_key][move] += change


class Board:
    def __init__(self, grid=np.ones((6,6))*np.nan):
        self.grid = grid

    def winner(self):
        def check_three_consecutive(arr):
            """Check if there are three consecutive identical marks in a row."""
            for i in range(len(arr) - 2):  # Check consecutive groups of 3
                if np.all(arr[i:i+3] == 1):  # Player X wins
                    return "X"
                elif np.all(arr[i:i+3] == 0):  # Player O wins
                    return "O"
            return None

        # Check rows and columns
        for i in range(6):
            row_winner = check_three_consecutive(self.grid[i, :])  # Check each row
            col_winner = check_three_consecutive(self.grid[:, i])  # Check each column
            if row_winner:
                return row_winner
            if col_winner:
                return col_winner

        # Check diagonals (6x6 grid can have multiple diagonals)
        diagonals = []
        for offset in range(-3, 4):  # Get diagonals for different offsets
            diagonals.append(np.diagonal(self.grid, offset=offset))  # Top-left to bottom-right
            diagonals.append(np.diagonal(np.fliplr(self.grid), offset=offset))  # Top-right to bottom-left

        for diag in diagonals:
            if len(diag) >= 3:  # Only check diagonals with at least 3 elements
                diag_winner = check_three_consecutive(diag)
                if diag_winner:
                    return diag_winner

        return None  # No winner yet


    def over(self):             # The game is over if there is a winner or if no squares remain empty (cat's game)
        return self.winner() is not None or not np.any(np.isnan(self.grid))

    def place_mark(self, move, mark):       # Place a mark on the board
        num = Board.mark2num(mark)
        self.grid[tuple(move)] = num

    @staticmethod
    def mark2num(mark):         # Convert's a player's mark to a number to be inserted in the Numpy array representing the board. The mark must be either "X" or "O".
        d = {"X": 1, "O": 0}
        return d[mark]

    def available_moves(self):
        return [(i,j) for i in range(6) for j in range(6) if np.isnan(self.grid[i][j])]

    def get_next_board(self, move, mark):
        next_board = copy.deepcopy(self)
        next_board.place_mark(move, mark)
        return next_board

    def make_key(self, mark):          # For Q-learning, returns a 10-character string representing the state of the board and the player whose turn it is
        fill_value = 9
        filled_grid = copy.deepcopy(self.grid)
        np.place(filled_grid, np.isnan(filled_grid), fill_value)
        return "".join(map(str, (list(map(int, filled_grid.flatten()))))) + mark

    def give_reward(self):                          # Assign a reward for the player with mark X in the current board position.
        if self.over():
            if self.winner() is not None:
                if self.winner() == "X":
                    return 1.0                      # Player X won -> positive reward
                elif self.winner() == "O":
                    return -1.0                     # Player O won -> negative reward
            else:
                return 0.5                          # A smaller positive reward for cat's game
        else:
            return 0.0                              # No reward if the game is not yet finished


class Player(object):
    def __init__(self, mark):
        self.mark = mark

    @property
    def opponent_mark(self):
        if self.mark == 'X':
            return 'O'
        elif self.mark == 'O':
            return 'X'
        else:
            print("The player's mark must be either 'X' or 'O'.")

class HumanPlayer(Player):
    pass

class ComputerPlayer(Player):
    pass

class RandomPlayer(ComputerPlayer):
    @staticmethod
    def get_move(board):
        moves = board.available_moves()
        if moves:   # If "moves" is not an empty list (as it would be if cat's game were reached)
            return moves[np.random.choice(len(moves))]    # Apply random selection to the index, as otherwise it will be seen as a 2D array

class THandPlayer(ComputerPlayer):
    def __init__(self, mark):
        super(THandPlayer, self).__init__(mark=mark)

    def get_move(self, board):
        moves = board.available_moves()
        if moves:
            for move in moves:
                if THandPlayer.next_move_winner(board, move, self.mark):
                    return move
                elif THandPlayer.next_move_winner(board, move, self.opponent_mark):
                    return move
            else:
                return RandomPlayer.get_move(board)

    @staticmethod
    def next_move_winner(board, move, mark):
        return board.get_next_board(move, mark).winner() == mark


class QPlayer(ComputerPlayer):
    def __init__(self, mark, Q={}, epsilon=0.2):
        super(QPlayer, self).__init__(mark=mark)
        self.Q = Q
        self.epsilon = epsilon

    def get_move(self, board):
        if np.random.uniform() < self.epsilon:              # With probability epsilon, choose a move at random ("epsilon-greedy" exploration)
            return RandomPlayer.get_move(board)
        else:
            state_key = QPlayer.make_and_maybe_add_key(board, self.mark, self.Q)
            Qs = self.Q[state_key]

            if self.mark == "X":
                return QPlayer.stochastic_argminmax(Qs, max)
            elif self.mark == "O":
                return QPlayer.stochastic_argminmax(Qs, min)

    @staticmethod
    def make_and_maybe_add_key(board, mark, Q):     # Make a dictionary key for the current state (board + player turn) and if Q does not yet have it, add it to Q
        default_Qvalue = 1.0       # Encourages exploration
        state_key = board.make_key(mark)
        if Q.get(state_key) is None:
            moves = board.available_moves()
            Q[state_key] = {move: default_Qvalue for move in moves}    # The available moves in each state are initially given a default value of zero
        return state_key

    @staticmethod
    def stochastic_argminmax(Qs, min_or_max):       # Determines either the argmin or argmax of the array Qs such that if there are 'ties', one is chosen at random
        min_or_maxQ = min_or_max(list(Qs.values()))
        if list(Qs.values()).count(min_or_maxQ) > 1:      # If there is more than one move corresponding to the maximum Q-value, choose one at random
            best_options = [move for move in list(Qs.keys()) if Qs[move] == min_or_maxQ]
            move = best_options[np.random.choice(len(best_options))]
        else:
            move = min_or_max(Qs, key=Qs.get)
        return move



# if __name__ == '__main__':
#     root = tk.Tk()
#     player1 = HumanPlayer(mark="X")
#     player2 = HumanPlayer(mark="O")


#     game = Game(root, player1, player2)

#     game.play()
#     root.mainloop()

