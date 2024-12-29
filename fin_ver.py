import pygame
import chess
import time

SQUARE_SIZE = 80
BOARD_SIZE = 8
WIDTH = HEIGHT = SQUARE_SIZE * BOARD_SIZE
RIGHT_PANEL_WIDTH = 250
FPS = 30

WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
LIGHT_SQUARE_COLOR = (240, 217, 181)
DARK_SQUARE_COLOR = (181, 136, 99)
SELECTED_SQUARE_COLOR = (0, 255, 0)
HIGHLIGHT_COLOR = (255, 255, 0)
RIGHT_PANEL_BG_COLOR = (240, 240, 240)

HISTORY_WIDTH = RIGHT_PANEL_WIDTH - 40
HISTORY_HEIGHT = HEIGHT - 150
HISTORY_START_Y = 50

PIECES_IMAGES = {}


def load_images():
    pieces = ['bK', 'bN', 'bB', 'bQ', 'bR', 'bP', 'wK', 'wN', 'wB', 'wQ', 'wR', 'wP']
    for piece in pieces:
        PIECES_IMAGES[piece] = pygame.transform.scale(pygame.image.load(f'images/{piece}.png'),
                                                      (SQUARE_SIZE, SQUARE_SIZE))


def evaluate_board(board):
    piece_value = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    center_control = {
        chess.E4: 1, chess.E5: 1,
        chess.D4: 1, chess.D5: 1,
        chess.C4: 0.5, chess.C5: 0.5,
        chess.F4: 0.5, chess.F5: 0.5,
    }

    def activity_score(piece, square):
        if piece.piece_type == chess.KNIGHT:
            center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
            if square in center_squares:
                return 10
            else:
                return -5
        if piece.piece_type == chess.BISHOP:

            if square in [chess.C1, chess.F1, chess.C8, chess.F8]:
                return 5
            else:
                return 2
        if piece.piece_type == chess.ROOK or piece.piece_type == chess.QUEEN:
            open_lines = [chess.A1, chess.H1, chess.A8, chess.H8]
            if square in open_lines:
                return 15
            return 5
        return 0

    def calculate_protection(board, square, color):
        protected = 0
        for move in board.legal_moves:
            if move.to_square == square and board.piece_at(move.from_square).color == color:
                protected += 1
        return protected

    def calculate_threat(board, square, color):
        threatened = 0
        for move in board.legal_moves:
            if move.to_square == square and board.piece_at(move.from_square).color != color:
                threatened += 1
        return threatened

    def king_safety(board, color):
        king_square = board.king(color)
        safety_score = 0
        for move in board.legal_moves:
            if move.to_square == king_square and board.piece_at(move.from_square).color != color:
                safety_score -= 100
        return safety_score

    def evaluate_pawn_structure(board):
        passed_pawn_score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                if piece.color == chess.WHITE:
                    if square >= chess.A5 and square <= chess.H5:
                        passed_pawn_score += 50
                else:
                    if square <= chess.A4 and square >= chess.H4:
                        passed_pawn_score -= 50  #
        return passed_pawn_score

    def evaluate_dynamic_position(board, color):
        dynamic_score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color:
                enemy_king_square = board.king(not color)
                distance_to_enemy_king = chess.square_distance(square, enemy_king_square)
                if distance_to_enemy_king < 3:
                    dynamic_score += 30

        return dynamic_score

    def evaluate_tempo(board, color):
        tempo_score = 0
        for move in board.legal_moves:
            if board.piece_at(move.to_square) is not None and board.piece_at(move.to_square).color != color:
                tempo_score += 10
        return tempo_score

    def is_endgame(board):
        return len(board.piece_map()) <= 10

    material = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_value[piece.piece_type]

            value += activity_score(piece, square)

            protection = calculate_protection(board, square, piece.color)
            if protection > 0:
                value += 50
            else:
                value -= 50

            threat = calculate_threat(board, square, piece.color)
            if threat > 0:
                value -= 100

            material += value

    material += king_safety(board, chess.WHITE)
    material -= king_safety(board, chess.BLACK)
    material += evaluate_dynamic_position(board, chess.WHITE)
    material -= evaluate_dynamic_position(board, chess.BLACK)
    material += evaluate_tempo(board, chess.WHITE)
    material -= evaluate_tempo(board, chess.BLACK)

    material += evaluate_pawn_structure(board)

    if is_endgame(board):
        material += 200

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                material += center_control.get(square, 0)
            else:
                material -= center_control.get(square, 0)

    return material


def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


def best_move(board, depth):
    best_move = None
    best_value = -float('inf')

    for move in board.legal_moves:
        board.push(move)
        move_value = minimax(board, depth - 1, -float('inf'), float('inf'), False)
        board.pop()

        if move_value > best_value:
            best_value = move_value
            best_move = move

    return best_move


def is_in_check(board):
    return board.is_check()


def draw_board(window, board, selected_square=None, legal_moves=[]):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR
            pygame.draw.rect(window, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                piece_color = 'w' if piece.color == chess.WHITE else 'b'
                piece_type = 'PNBRQK'[piece.piece_type - 1]
                piece_str = f'{piece_color}{piece_type}'
                window.blit(PIECES_IMAGES[piece_str], (col * SQUARE_SIZE, row * SQUARE_SIZE))

            if selected_square and selected_square == chess.square(col, 7 - row):
                pygame.draw.rect(window, SELECTED_SQUARE_COLOR,
                                 (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

            if chess.square(col, 7 - row) in [move.to_square for move in legal_moves]:
                pygame.draw.rect(window, HIGHLIGHT_COLOR,
                                 (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)


def get_square_under_mouse(mouse_pos):
    col, row = mouse_pos
    return col // SQUARE_SIZE, row // SQUARE_SIZE


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def draw_history(window, history, scroll_offset):
    font = pygame.font.SysFont('Arial', 24)
    pygame.draw.rect(window, RIGHT_PANEL_BG_COLOR, (WIDTH, HISTORY_START_Y, HISTORY_WIDTH, HISTORY_HEIGHT))
    y_offset = HISTORY_START_Y + scroll_offset

    for color, move in history:
        move_surface = font.render(f"{color}: {move}", True, (0, 0, 0))
        window.blit(move_surface, (WIDTH + 20, y_offset))
        y_offset += 40

        if y_offset > (HISTORY_START_Y + HISTORY_HEIGHT):
            break


def draw_game_over(window, winner):
    font = pygame.font.SysFont('Arial', 48)
    message = f"{winner}!"
    text_surface = font.render(message, True, (255, 0, 0))
    window.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT // 2 - 24))

    button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
    pygame.draw.rect(window, (0, 0, 0), button_rect)
    button_text = pygame.font.SysFont('Arial', 24).render("Выход", True, (255, 255, 255))
    window.blit(button_text, (WIDTH // 2 - button_text.get_width() // 2, HEIGHT // 2 + 20))

    return button_rect


def show_result_screen(window, winner, width, height):
    while True:
        window.fill(WHITE_COLOR)
        font = pygame.font.SysFont('Arial', 48)
        message = f"{winner}!"
        text_surface = font.render(message, True, (255, 0, 0))
        window.blit(text_surface, (width // 2 - text_surface.get_width() // 2, height // 2 - 24))

        button_rect = pygame.Rect(width // 2 - 100, height // 2 + 40, 200, 50)
        pygame.draw.rect(window, (0, 0, 0), button_rect)
        button_text = pygame.font.SysFont('Arial', 24).render("Выход", True, (255, 255, 255))
        window.blit(button_text, (width // 2 - button_text.get_width() // 2, height // 2 + 40))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    pygame.quit()
                    return

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def play_game():
    pygame.init()
    window = pygame.display.set_mode((WIDTH + RIGHT_PANEL_WIDTH, HEIGHT))
    pygame.display.set_caption("Шахматы против бота")
    clock = pygame.time.Clock()

    load_images()

    board = chess.Board()
    selected_square = None
    legal_moves = []

    game_over = False
    player_turn = True

    history = []
    scroll_offset = 0
    start_time = time.time()

    while True:
        window.fill(WHITE_COLOR)

        if game_over:
            winner = "Игра окончена"
            if board.is_checkmate():
                winner = "Вы проиграли!" if board.turn == chess.WHITE else "Вы выиграли!"
            elif board.is_stalemate() or board.is_insufficient_material():
                winner = "Ничья!"

            show_result_screen(window, winner, WIDTH + RIGHT_PANEL_WIDTH, HEIGHT)
            break
        else:
            draw_board(window, board, selected_square, legal_moves)

            pygame.draw.rect(window, RIGHT_PANEL_BG_COLOR, (WIDTH, 0, RIGHT_PANEL_WIDTH, HEIGHT))

            turn_text = "Ход белых" if board.turn == chess.WHITE else "Ход чёрных"
            text_surface = pygame.font.SysFont('Arial', 30).render(turn_text, True, (0, 0, 0))
            window.blit(text_surface, (WIDTH + RIGHT_PANEL_WIDTH // 2 - text_surface.get_width() // 2, 10))

            draw_history(window, history, scroll_offset)

            elapsed_time = int(time.time() - start_time)
            time_text = format_time(elapsed_time)
            time_surface = pygame.font.SysFont('Arial', 30).render(f"Время: {time_text}", True, (0, 0, 0))
            window.blit(time_surface, (WIDTH + 20, HEIGHT - 60))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not game_over:
                        mouse_pos = pygame.mouse.get_pos()
                        col, row = get_square_under_mouse(mouse_pos)

                        if event.button == 4:
                            scroll_offset = min(scroll_offset + 40, 0)
                        elif event.button == 5:
                            scroll_offset = max(scroll_offset - 40,
                                                -(len(history) * 40 - HISTORY_HEIGHT))

                        if player_turn and board.turn == chess.WHITE:
                            if selected_square is not None:
                                if selected_square == chess.square(col, 7 - row):
                                    continue

                                move = chess.Move.from_uci(
                                    f'{chess.square_name(selected_square)}{chess.square_name(chess.square(col, 7 - row))}')

                                if move in legal_moves:
                                    board.push(move)
                                    history.insert(0, ("Белые", move))
                                    selected_square = None
                                    legal_moves = []

                                    if board.is_game_over():
                                        game_over = True
                                    player_turn = False
                                else:
                                    selected_square = None
                                    legal_moves = []
                            else:
                                selected_square = chess.square(col, 7 - row)
                                legal_moves = [move for move in board.legal_moves if
                                               move.from_square == selected_square]

                                if not legal_moves:
                                    selected_square = None

        if not game_over and not player_turn and board.turn == chess.BLACK:
            move = best_move(board, depth=3)
            board.push(move)

            history.insert(0, ("Чёрные", move))

            if board.is_game_over():
                game_over = True
            player_turn = True

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    play_game()

