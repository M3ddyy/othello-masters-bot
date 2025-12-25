# game.py
import random


class Othello:
    def __init__(self):
        self.board_size = 8
        self.player_black = '⚫️'
        self.player_white = '⚪️'
        self.empty_square = '\u200b'
        self.reset_board()

    def new_board(self):
        board = [[self.empty_square for _ in range(self.board_size)] for _ in range(self.board_size)]
        board[3][3] = self.player_white
        board[3][4] = self.player_black
        board[4][3] = self.player_black
        board[4][4] = self.player_white
        return board

    def reset_board(self):
        self.board = self.new_board()
        self.current_player = self.player_black

    def get_opponent(self, player):
        return self.player_white if player == self.player_black else self.player_black

    def is_valid_move(self, row, col, player):
        if not (0 <= row < self.board_size and 0 <= col < self.board_size and self.board[row][
            col] == self.empty_square):
            return False

        opponent = self.get_opponent(player)
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == opponent:
                r, c = r + dr, c + dc
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] == player:
                        return True
                    if self.board[r][c] == self.empty_square:
                        break
                    r, c = r + dr, c + dc
        return False

    def get_valid_moves(self, player):
        return [(r, c) for r in range(self.board_size) for c in range(self.board_size) if
                self.is_valid_move(r, c, player)]

    def make_move(self, row, col, player):
        if not self.is_valid_move(row, col, player):
            return False

        opponent = self.get_opponent(player)
        self.board[row][col] = player

        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            r, c = row + dr, col + dc
            tiles_to_flip = []
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] == self.empty_square:
                    break
                if self.board[r][c] == opponent:
                    tiles_to_flip.append((r, c))
                if self.board[r][c] == player:
                    for flip_r, flip_c in tiles_to_flip:
                        self.board[flip_r][flip_c] = player
                    break
                r, c = r + dr, c + dc

        self.current_player = self.get_opponent(player)
        return True

    def get_score(self):
        score = {self.player_black: 0, self.player_white: 0}
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r][c] in score:
                    score[self.board[r][c]] += 1
        return score

    def get_ai_move(self):
        valid_moves = self.get_valid_moves(self.player_white)
        if not valid_moves:
            return None
        return random.choice(valid_moves)
