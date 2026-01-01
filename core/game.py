class Othello:
    def __init__(self, player1_id=None, player1_name=None, player2_id=None, player2_name=None):
        self.board_size = 8
        self.player_black = '⚫️'
        self.player_white = '⚪️'
        self.empty_square = '🟩'
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_id = player1_id
        self.player2_id = player2_id
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

    def get_current_player_id(self):
        if self.current_player == self.player_black:
            return self.player1_id
        else:
            return self.player2_id

    def get_current_player_name(self):
        if self.current_player == self.player_black:
            return self.player1_name
        else:
            return self.player2_name

    def is_valid_move(self, row, col, player):
        if not (
            0 <= row < self.board_size and
            0 <= col < self.board_size and
            self.board[row][col] == self.empty_square
        ):
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
        return [
            (r, c)
            for r in range(self.board_size)
            for c in range(self.board_size)
            if self.is_valid_move(r, c, player)
        ]

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

    def evaluate_board(self, board, player):
        opponent = self.player_white if player == self.player_black else self.player_black

        weights = [
            [100, -20, 10, 5, 5, 10, -20, 100],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [10, -2, -1, -1, -1, -1, -2, 10],
            [5, -2, -1, -1, -1, -1, -2, 5],
            [5, -2, -1, -1, -1, -1, -2, 5],
            [10, -2, -1, -1, -1, -1, -2, 10],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [100, -20, 10, 5, 5, 10, -20, 100]
        ]

        score = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    score += weights[r][c]
                elif board[r][c] == opponent:
                    score -= weights[r][c]
        return score

    def get_ai_move(self):
        import copy

        def get_valid_moves_sim(board, player):
            moves = []
            opponent = self.player_white if player == self.player_black else self.player_black
            for r in range(8):
                for c in range(8):
                    if board[r][c] != self.empty_square: continue
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == opponent:
                            while 0 <= rr < 8 and 0 <= cc < 8:
                                rr += dr
                                cc += dc
                                if not (0 <= rr < 8 and 0 <= cc < 8): break
                                if board[rr][cc] == player:
                                    moves.append((r, c))
                                    break
                                if board[rr][cc] == self.empty_square: break
                    if (r, c) in moves: continue
            return list(set(moves))

        def simulate_move(board, move, player):
            new_board = copy.deepcopy(board)
            r, c = move
            new_board[r][c] = player
            opponent = self.player_white if player == self.player_black else self.player_black

            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                rr, cc = r + dr, c + dc
                tiles = []
                while 0 <= rr < 8 and 0 <= cc < 8 and new_board[rr][cc] == opponent:
                    tiles.append((rr, cc))
                    rr += dr
                    cc += dc
                if 0 <= rr < 8 and 0 <= cc < 8 and new_board[rr][cc] == player:
                    for tr, tc in tiles:
                        new_board[tr][tc] = player
            return new_board

        def minimax(board, depth, maximizing_player, current_turn_player):
            valid_moves = get_valid_moves_sim(board, current_turn_player)

            if depth == 0 or not valid_moves:
                return self.evaluate_board(board, self.player_white), None

            best_move = valid_moves[0]

            if maximizing_player:
                max_eval = -float('inf')
                for move in valid_moves:
                    new_board = simulate_move(board, move, current_turn_player)
                    eval_score, _ = minimax(new_board, depth - 1, False, self.player_black)
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = move
                return max_eval, best_move
            else:
                min_eval = float('inf')
                for move in valid_moves:
                    new_board = simulate_move(board, move, current_turn_player)
                    eval_score, _ = minimax(new_board, depth - 1, True, self.player_white)
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                return min_eval, best_move

        _, best_move = minimax(self.board, 3, True, self.player_white)
        return best_move
