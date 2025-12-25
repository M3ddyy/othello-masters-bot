DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

class Game:
    def __init__(self):
        self.board = [[' ' for _ in range(8)] for _ in range(8)]
        self.board[3][3] = 'W'
        self.board[3][4] = 'B'
        self.board[4][3] = 'B'
        self.board[4][4] = 'W'
        self.current_player = 'B'

    def print_board(self):
        print('  0 1 2 3 4 5 6 7')
        for i, row in enumerate(self.board):
            print(i, ' '.join(row))

    def is_on_board(self, x, y):
        return 0 <= x < 8 and 0 <= y < 8

    def is_valid_move(self, x, y):
        if not self.is_on_board(x, y) or self.board[x][y] != ' ':
            return False

        other_player = 'W' if self.current_player == 'B' else 'B'

        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            found_opponent = False

            while self.is_on_board(nx, ny) and self.board[nx][ny] == other_player:
                nx += dx
                ny += dy
                found_opponent = True

            if found_opponent and self.is_on_board(nx, ny) and self.board[nx][ny] == self.current_player:
                return True

        return False

    def make_move(self, x, y):
        if not self.is_valid_move(x, y):
            return False

        self.board[x][y] = self.current_player
        other_player = 'W' if self.current_player == 'B' else 'B'

        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            path = []

            while self.is_on_board(nx, ny) and self.board[nx][ny] == other_player:
                path.append((nx, ny))
                nx += dx
                ny += dy

            if path and self.is_on_board(nx, ny) and self.board[nx][ny] == self.current_player:
                for px, py in path:
                    self.board[px][py] = self.current_player

        self.switch_player()
        return True

    def switch_player(self):
        self.current_player = 'W' if self.current_player == 'B' else 'B'
