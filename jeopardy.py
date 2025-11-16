import pygame
import sys
import csv

from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: python minecraft_jeopardy_csv.py <filename.csv>")
    sys.exit(1)

filename = sys.argv[1]

pygame.init()

# Screen settings
xx = 1.3
WIDTH, HEIGHT = 1024*xx, 600*xx
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minecraft Jeopardy")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 120, 215)
YELLOW = (255, 255, 0)

# Fonts
#Noto_Sans_SC.zip
#-rw-r--r--@  1 huw  staff   10560076 Sep 11 12:44 NotoSansSC-Regular.ttf
FONT = pygame.font.Font("NotoSansSC-Regular.ttf", 28)
#FONT = pygame.font.SysFont('arial', 20)
BIG_FONT = pygame.font.Font('NotoSansSC-Regular.ttf', 28)
BIG_SCORE_FONT = pygame.font.Font('NotoSansSC-Regular.ttf', 30)

# Teams
teams = {"Team 1": 0, "Team 2": 0}
current_team = "Team 1"

# Feedback
feedback_text = ""
feedback_timer = 0

# Load questions from CSV
questions = []
delimiter_char = '\t'  # or '\t' for TSV

try:
    with open(filename, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter_char)
        next(reader)  # skip header
        for row in reader:
            if len(row) < 9:
                continue
            try:
                subtype = row[0].strip()
                question = row[1].strip()
                a1 = row[2].strip()
                a2 = row[3].strip()
                a3 = row[4].strip()
                a4 = row[5].strip()
                correct = int(row[6].strip())
                time_sec = int(row[7].strip())
                square_text = row[8].strip()
                questions.append([subtype, question, a1, a2, a3, a4, correct, time_sec, square_text])
            except ValueError:
                print(f"Skipping invalid row: {row}")
except FileNotFoundError:
    print(f"Error: file '{filename}' not found.")
    sys.exit()

print(f"Loaded {len(questions)} questions from {filename}")

# Detect subtypes and organize questions
subtype_questions = defaultdict(list)
for q in questions:
    subtype_questions[q[0]].append(q)

# Sort questions in each subtype by square_text
for s in subtype_questions:
    subtype_questions[s].sort(key=lambda x: int(x[8]))

subtypes = list(subtype_questions.keys())
COLS = len(subtypes)
ROWS = max(len(subtype_questions[s]) for s in subtypes)

SCORE_ROW_HEIGHT = 100
square_width = WIDTH // COLS
square_height = (HEIGHT - SCORE_ROW_HEIGHT) // ROWS

# Build board squares and mapping
board_squares = []
square_mapping = []
square_texts = []

for col_index, s in enumerate(subtypes):
    for row_index, q in enumerate(subtype_questions[s]):
        rect = pygame.Rect(col_index*square_width,
                           SCORE_ROW_HEIGHT + row_index*square_height,
                           square_width, square_height)
        board_squares.append(rect)
        square_mapping.append(q)
        square_texts.append(q[8])  # show points from CSV

used_squares = [False]*len(board_squares)

# Draw the board
def draw_board():
    SCREEN.fill(BLACK)
    # Score row
    pygame.draw.rect(SCREEN, GRAY, (0,0, WIDTH, SCORE_ROW_HEIGHT))
    score_display = BIG_SCORE_FONT.render(
        f"Team 1: {teams['Team 1']} | Team 2: {teams['Team 2']} | Current: {current_team}", True, WHITE)
    SCREEN.blit(score_display, (10, 10))
    
    # Feedback
    if feedback_text:
        feedback_render = BIG_SCORE_FONT.render(feedback_text, True, GREEN if feedback_text=="Correct!" else RED)
        SCREEN.blit(feedback_render, (WIDTH//2 - feedback_render.get_width()//2, 10))
    
    # Column headers
    for col_index, s in enumerate(subtypes):
        text = BIG_FONT.render(s, True, WHITE)
        SCREEN.blit(text, (col_index*square_width + square_width//2 - text.get_width()//2,
                           SCORE_ROW_HEIGHT - 40))
    
    # Draw squares
    for i, rect in enumerate(board_squares):
        color = BLUE if not used_squares[i] else GRAY
        pygame.draw.rect(SCREEN, color, rect)
        pygame.draw.rect(SCREEN, WHITE, rect, 3)
        text_to_show = square_texts[i] if i < len(square_texts) else ""
        text = BIG_FONT.render(text_to_show, True, WHITE)
        SCREEN.blit(text, (rect.x + rect.width // 2 - text.get_width()//2,
                           rect.y + rect.height // 2 - text.get_height()//2))
    pygame.display.flip()

# Show question and handle answer
def show_question(q):
    global feedback_text, feedback_timer
    _, question, a1, a2, a3, a4, correct, time_sec, _ = q
    answers = [a1, a2, a3, a4]
    start_ticks = pygame.time.get_ticks()
    
    while True:
        SCREEN.fill(BLACK)
        pygame.draw.rect(SCREEN, GRAY, (0,0, WIDTH, SCORE_ROW_HEIGHT))
        score_display = BIG_SCORE_FONT.render(
            f"Team 1: {teams['Team 1']} | Team 2: {teams['Team 2']} | Current: {current_team}", True, WHITE)
        SCREEN.blit(score_display, (10, 10))
        
        seconds = time_sec - (pygame.time.get_ticks()-start_ticks)//1000
        timer_text = BIG_SCORE_FONT.render(f"Time: {seconds}", True, RED)
        SCREEN.blit(timer_text, (WIDTH-200, 10))
        if seconds <=0:
            return None
        
        # Wrap question text
        words = question.split(' ')
        lines=[]
        line=""
        for w in words:
            if len(line + ' ' + w)<40:
                line+=w+' '
            else:
                lines.append(line)
                line=w+' '
        lines.append(line)
        for i,l in enumerate(lines):
            text = BIG_FONT.render(l,True,YELLOW)
            SCREEN.blit(text,(50,SCORE_ROW_HEIGHT + 10 + i*30))
        
        # Draw answer buttons
        answer_rects = []
        for i, ans in enumerate(answers):
            rect = pygame.Rect(100, SCORE_ROW_HEIGHT + 100 + i*50, 800, 40)
            answer_rects.append(rect)
            pygame.draw.rect(SCREEN, WHITE, rect, 2)
            text = BIG_FONT.render(f"{i+1}. {ans}", True, WHITE)
            SCREEN.blit(text, (rect.x + 5, rect.y + 5))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type==pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, rect in enumerate(answer_rects):
                    if rect.collidepoint(mouse_pos):
                        chosen = i+1
                        feedback_text = "Correct!" if chosen == correct else "Wrong!"
                        feedback_timer = pygame.time.get_ticks() + 1500
                        return chosen

# Main loop
def main():
    global current_team, feedback_text
    running = True
    clock = pygame.time.Clock()
    
    while running:
        draw_board()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            if event.type==pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, rect in enumerate(board_squares):
                    if rect.collidepoint(pos) and not used_squares[i]:
                        used_squares[i]=True
                        q = square_mapping[i]
                        answer = show_question(q)
                        if answer == q[6]:  # correct
                            try:
                                points = int(q[8])
                            except ValueError:
                                points = 0
                            teams[current_team] += points
                            square_texts[i] = "Correct!"
                        else:
                            square_texts[i] = "Wrong!"
                            # Switch team
                            current_team = "Team 2" if current_team=="Team 1" else "Team 1"
        if feedback_text and pygame.time.get_ticks() > feedback_timer:
            feedback_text = ""
        clock.tick(30)

main()
pygame.quit()

