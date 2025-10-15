# Connect four in python

import numpy as np
import pygame
import sys
import math
import random

def main():
    RED = (255,0,0)
    BLUE = (0,0,255)
    BLACK = (0,0,0)
    YELLOW = (255,255,0)
    WHITE = (255,255,255)

    ROW_COUNT = 6
    COLUMN_COUNT = 7

    def create_board():
        return np.zeros((ROW_COUNT, COLUMN_COUNT))

    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    def is_valid_location(board, col):
        return board[ROW_COUNT-1][col] == 0

    def get_next_open_row(board, col):
        for r in range(ROW_COUNT):
            if board[r][col] == 0:
                return r     

    def print_board(board):
        print(np.flip(board, 0))

    def winning_move(board, piece):
    
        
        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT):
                if all(board[r][c+i] == piece for i in range(4)):
                    return True
                
        
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT-3):
                if all(board[r+i][c] == piece for i in range(4)):
                    return True
                
        
        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT-3):
                if all(board[r+i][c+i] == piece for i in range (4)):
                    return True


        for c in range(COLUMN_COUNT-3):
            for r in range(3, ROW_COUNT):
                if all(board[r-i][c+1] == piece for i in range(4)):
                    return True
                
        return False


    def draw_board(board):
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT):
                pygame.draw.rect(screen, BLUE, (c*SQUARESIZE, r*SQUARESIZE+SQUARESIZE, SQUARESIZE, SQUARESIZE))
                pygame.draw.circle(screen, BLACK, 
                                (int(c*SQUARESIZE+SQUARESIZE/2), int(r*SQUARESIZE+SQUARESIZE+SQUARESIZE/2)), RADIUS)

        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT):
                color = BLACK
                if board[r][c] == 1:
                    color = RED
                elif board[r][c] == 2:
                    color = YELLOW
                pygame.draw.circle(screen, color, 
                                (int(c*SQUARESIZE+SQUARESIZE/2), height - int(r*SQUARESIZE+SQUARESIZE/2)), RADIUS)
        pygame.display.update()


    def get_valid_locations(board):
        valid = []
        for col in range(COLUMN_COUNT):
            if is_valid_location(board, col):
                valid.append(col)

        return valid

    def score_window(window, piece):
        score = 0
        opp_piece = 1 if piece == 2 else 2

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        
        if window.count(opp_piece) == 3 and window.count(0) ==1:
            score -= 4

        
        return score

    def score_position(board, piece):
        score = 0
        center_array = [int(i) for i in list(board[:, COLUMN_COUNT//2])]
        center_count = center_array.count(piece)
        score += center_count * 3


        for r in range(ROW_COUNT):
            row_array = [int(i) for i in list(board[r, :])]
            for c in range(COLUMN_COUNT-3):
                window = row_array[c:c+4]
                score += score_window(window, piece)


        for c in range(COLUMN_COUNT):
            col_array = [int(i) for i in list(board[:, c])]
            for r in range(ROW_COUNT-3):
                window = col_array[r:r+4]
                score += score_window(window, piece)


        for r in range(ROW_COUNT-3):
            for c in range(COLUMN_COUNT-3):
                window = [int(board[r+i][c+i])for i in range(4)]
                score += score_window(window, piece)


        for r in range(3, ROW_COUNT):
            for c in range(COLUMN_COUNT-3):
                window = [int(board[r-1][c+i])for i in range(4)]
                score += score_window(window, piece)


        return score


    def pick_best_move(board, piece):
        valid_locations = get_valid_locations(board)
        best_score = -9999
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, piece)
            score = score_position(temp_board, piece)
            if score > best_score:
                best_score = score
                best_col = col
        return best_col


    def is_terminal_node(board):
        return winning_move(board, 1) or winning_move(board, 2) or len(get_valid_locations(board)) == 0

    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(board)
        terminal = is_terminal_node(board)
        if depth == 0 or terminal:
            if terminal:
                if winning_move(board, 2):
                    return (None, 100000000000000)
                elif winning_move(board, 1):
                    return (None, -10000000000000)
                else:
                    return (None, 0)
                
            else:
                return (None, score_position(board, 2))
        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = board.copy()
                drop_piece(b_copy, row, col, 2)
                new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = board.copy()
                drop_piece(b_copy, row, col, 1)
                new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value




    def main_menu():
        screen.fill(BLACK)
        title = font.render("CONNECT FOUR", True, YELLOW)
        single = small_font.render("1. Single Player", True, WHITE)
        multi = small_font.render("2. Multiplayer", True, WHITE)
        screen.blit(title, (width/2 - 220, 100))
        screen.blit(single, (width/2 - 120, 250))
        screen.blit(multi, (width/2 - 120, 350))
        pygame.display.update()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        return "single"
                    elif event.key == pygame.K_2:
                        return "multi"
                
    def difficulty_menu():
        screen.fill(BLACK)
        title = font.render("CHOOSE Difficulty", True, YELLOW)
        options = ["1. Easy", "2.Medium", "3. Hard", "4. Impossible"]
        screen.blit(title, (width/2 - 300, 100))
        for i, opt in enumerate(options):
            label = small_font.render(opt, True, WHITE)
            screen.blit(label,(width/2 - 120, 250 + i * 80))
        pygame.display.update()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        return "Easy"
                    elif event.key == pygame.K_2:
                        return "Medium"
                    elif event.key == pygame.K_3:
                        return "Hard" 
                    elif event.key == pygame.K_4:
                        return "Impossible"
    
    pygame.init()
    SQUARESIZE = 100
    width = COLUMN_COUNT * SQUARESIZE
    height = (ROW_COUNT+1) * SQUARESIZE
    size = (width, height)
    RADIUS = int(SQUARESIZE/2 - 5)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Connect Four")

    font = pygame.font.SysFont("monospace", 75)
    small_font = pygame.font.SysFont("monospace", 50)


    mode = main_menu()
    difficulty = None
    if mode == "single":
        difficulty = difficulty_menu()


    board = create_board()
    game_over = False
    turn = 0
    draw_board(board)
    pygame.display.update()


    pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE))
    pygame.display.update()


    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE))
                posx = event.pos[0]
                color = RED if turn == 0 else YELLOW
                pygame.draw.circle(screen, color, (posx, int(SQUARESIZE/2)), RADIUS)
                pygame.display.update()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.draw.rect(screen, BLACK, (0, 0 , width, SQUARESIZE))
                posx = event.pos[0]
                col = int(math.floor(posx / SQUARESIZE))

                if mode == "multi" or (mode == "single" and turn == 0):
                    if is_valid_location(board, col):
                        row = get_next_open_row(board, col)
                        drop_piece(board, row, col, 1 if turn == 0 else 2)
                        if winning_move(board, 1 if turn == 0 else 2):
                            label = font.render(f"PLAYER {turn + 1}WINS!", True, RED if turn == 0 else YELLOW)
                            screen.blit(label, (40, 10))
                            pygame.display.update()
                            draw_board(board)
                            pygame.time.wait(2500) 
                            game_over = True


                        draw_board(board)
                        print_board(board)
                        turn = (turn + 1) % 2

        if mode == "single" and not game_over and turn == 1:
                pygame.time.wait(300)
                valid_locations = get_valid_locations(board)
                col = None


                if difficulty == "Easy":
                    col = random.choice(valid_locations)


                elif difficulty == "Medium":
                    if random.random() < 0.6:
                        col = pick_best_move(board, 2)
                    else:
                        col = random.choice(valid_locations)


                elif difficulty == "Hard":
                    col = pick_best_move(board, 2)
                

                elif difficulty == "Impossible":
                    col, minimax_score =minimax(board, 4, -math.inf, math.inf, True)


                if col is not None and is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    drop_piece(board, row, col, 2)
                    if winning_move(board, 2):
                        label = font.render("PLAYER 2 WINS!", True, YELLOW)
                        screen.blit(label, (40, 10))
                        pygame.display.update()
                        game_over = True
                    draw_board(board)
                    print_board(board)
                    turn = (turn + 1) % 2

if __name__ == "__main__":
    main()