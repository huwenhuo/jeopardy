import pygame
import csv
import sys
from collections import defaultdict, OrderedDict

# ------------------------------
# CONFIG
# ------------------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
BOARD_TOP = 100
BOARD_LEFT = 50
CELL_WIDTH = 200
CELL_HEIGHT = 100
CELL_MARGIN = 10
CATEGORY_HEIGHT = 50
CATEGORY_PADDING = 20
FONT_SIZE = 24
SCORE_FONT_SIZE = 32
BOTTOM_MARGIN = 80  # space for round buttons

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
RED = (255, 50, 50)
YELLOW = (255, 200, 0)

# ------------------------------
# Pygame Initialization
# ------------------------------
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Jeopardy")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, FONT_SIZE)
score_font = pygame.font.SysFont(None, SCORE_FONT_SIZE)

# ------------------------------
# Load TSV/CSV Data
# ------------------------------
if len(sys.argv) < 2:
    print("Usage: python jeopardy.py questions.tsv")
    sys.exit(1)

csv_file = sys.argv[1]
questions = []
with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row["air_date"].strip() and row["round"].strip() and row["category"].strip() and row["question"].strip():
            questions.append({
                "air_date": row["air_date"].strip(),
                "round": int(row["round"]),
                "category": row["category"].strip(),
                #"question": row["question"].strip(),
                "answer": row["question"].strip(),
                "question": row["answer"].strip(),
                "points": int(row["clue_value"]),
                "used": False
            })

# ------------------------------
# Group questions: air_date -> round -> category
# ------------------------------
dates_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for q in questions:
    dates_dict[q["air_date"]][q["round"]][q["category"]].append(q)

# Sort
dates_sorted = OrderedDict()
for date in sorted(dates_dict.keys()):
    rounds_sorted = OrderedDict()
    for rnd in sorted(dates_dict[date].keys()):
        categories_sorted = OrderedDict()
        for cat in sorted(dates_dict[date][rnd].keys()):
            categories_sorted[cat] = sorted(dates_dict[date][rnd][cat], key=lambda x: x["points"])
        rounds_sorted[rnd] = categories_sorted
    dates_sorted[date] = rounds_sorted

date_list = list(dates_sorted.keys())
current_date_idx = 0
current_round_idx = 0

def get_current_round():
    current_date = date_list[current_date_idx]
    round_numbers = list(dates_sorted[current_date].keys())
    current_round_number = round_numbers[current_round_idx]
    current_round_data = dates_sorted[current_date][current_round_number]
    return current_date, current_round_number, current_round_data

current_date, current_round_number, current_round = get_current_round()

# ------------------------------
# Game State
# ------------------------------
score = 0
showing_question_window = False
showing_answer = False
current_question = None
feedback = ""

# Buttons
correct_button = pygame.Rect(250, 550, 200, 60)
wrong_button = pygame.Rect(750, 550, 200, 60)
show_answer_button = pygame.Rect(500, 550, 200, 60)
next_round_button = pygame.Rect(0,0,150,50)  # will set y dynamically
prev_round_button = pygame.Rect(0,0,150,50)

# ------------------------------
# Helper Functions
# ------------------------------
def draw_board():
    global next_round_button, prev_round_button, CELL_HEIGHT_DYNAMIC
    screen.fill(BLACK)
    max_rows = max(len(current_round[cat]) for cat in current_round)
    
    # Adjust cell height to fit screen if needed
    available_height = WINDOW_HEIGHT - BOARD_TOP - BOTTOM_MARGIN
    cell_area_height = available_height - CATEGORY_HEIGHT - CATEGORY_PADDING
    CELL_HEIGHT_DYNAMIC = min(CELL_HEIGHT, cell_area_height // max_rows)
    
    # Categories
    for col_idx, cat in enumerate(current_round.keys()):
        x = BOARD_LEFT + col_idx * (CELL_WIDTH + CELL_MARGIN)
        y = BOARD_TOP
        # Draw category title
        pygame.draw.rect(screen, BLUE, (x, y, CELL_WIDTH, CATEGORY_HEIGHT))
        screen.blit(font.render(cat, True, WHITE), (x + 5, y + 5))
        # Draw clue buttons
        for row_idx, q in enumerate(current_round[cat]):
            cell_y = y + CATEGORY_HEIGHT + CATEGORY_PADDING + row_idx * (CELL_HEIGHT_DYNAMIC + CELL_MARGIN)
            color = GRAY if q["used"] else BLUE
            pygame.draw.rect(screen, color, (x, cell_y, CELL_WIDTH, CELL_HEIGHT_DYNAMIC))
            screen.blit(font.render(str(q["points"]), True, WHITE), (x + 10, cell_y + 10))
    
    # Score and info
    screen.blit(score_font.render(f"Score: {score}", True, GREEN), (BOARD_LEFT, 20))
    screen.blit(font.render(f"Date: {current_date}  Round: {current_round_number}", True, YELLOW), (500, 20))
    
    # Feedback
    if feedback:
        screen.blit(score_font.render(feedback, True, RED if "Wrong" in feedback else GREEN), (800, 20))
    
    # Round navigation buttons
    board_bottom = BOARD_TOP + CATEGORY_HEIGHT + CATEGORY_PADDING + max_rows * (CELL_HEIGHT_DYNAMIC + CELL_MARGIN) + 20
    next_round_button.y = board_bottom
    next_round_button.x = BOARD_LEFT
    prev_round_button.y = board_bottom
    prev_round_button.x = BOARD_LEFT + 160
    pygame.draw.rect(screen, GREEN, next_round_button)
    pygame.draw.rect(screen, GREEN, prev_round_button)
    screen.blit(font.render("Next Round", True, WHITE), (next_round_button.x + 10, next_round_button.y + 15))
    screen.blit(font.render("Prev Round", True, WHITE), (prev_round_button.x + 10, prev_round_button.y + 15))

def get_cell_under_mouse(pos):
    x, y = pos
    for col_idx, cat in enumerate(current_round.keys()):
        col_x = BOARD_LEFT + col_idx * (CELL_WIDTH + CELL_MARGIN)
        if col_x <= x <= col_x + CELL_WIDTH:
            for row_idx, q in enumerate(current_round[cat]):
                row_y = BOARD_TOP + CATEGORY_HEIGHT + CATEGORY_PADDING + row_idx * (CELL_HEIGHT_DYNAMIC + CELL_MARGIN)
                if row_y <= y <= row_y + CELL_HEIGHT_DYNAMIC:
                    return (col_idx, row_idx)
    return None

def show_question_window_func():
    screen.fill(WHITE)
    # Question text wrapping
    text = current_question["question"]
    lines = []
    line = ""
    for w in text.split():
        if font.size(line + " " + w)[0] > WINDOW_WIDTH - 40:
            lines.append(line)
            line = w
        else:
            line += " " + w
    lines.append(line)
    for i, l in enumerate(lines):
        screen.blit(font.render(l.strip(), True, BLACK), (20, 50 + i*30))
    
    if not showing_answer:
        pygame.draw.rect(screen, YELLOW, show_answer_button)
        screen.blit(font.render("Show Answer", True, WHITE), (show_answer_button.x + 25, show_answer_button.y + 15))
    else:
        # Correct/Wrong buttons
        pygame.draw.rect(screen, GREEN, correct_button)
        pygame.draw.rect(screen, RED, wrong_button)
        screen.blit(font.render("Correct", True, WHITE), (correct_button.x + 40, correct_button.y + 15))
        screen.blit(font.render("Wrong", True, WHITE), (wrong_button.x + 50, wrong_button.y + 15))
        # Show answer
        answer_text = current_question["answer"]
        screen.blit(font.render(f"Answer: {answer_text}", True, BLUE), (20, 200))

# ------------------------------
# Main Loop
# ------------------------------
running = True
while running:
    clock.tick(30)
    if not showing_question_window:
        draw_board()
    else:
        show_question_window_func()
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not showing_question_window:
                if next_round_button.collidepoint(pos):
                    current_round_idx += 1
                    round_numbers = list(dates_sorted[date_list[current_date_idx]].keys())
                    if current_round_idx >= len(round_numbers):
                        current_round_idx = len(round_numbers)-1
                    _, current_round_number, current_round = get_current_round()
                elif prev_round_button.collidepoint(pos):
                    current_round_idx -= 1
                    if current_round_idx < 0:
                        current_round_idx = 0
                    _, current_round_number, current_round = get_current_round()
                else:
                    cell = get_cell_under_mouse(pos)
                    if cell:
                        col_idx, row_idx = cell
                        cat = list(current_round.keys())[col_idx]
                        q = current_round[cat][row_idx]
                        if not q["used"]:
                            current_question = q
                            showing_question_window = True
                            showing_answer = False
            else:
                # Question window buttons
                if not showing_answer and show_answer_button.collidepoint(pos):
                    showing_answer = True
                elif showing_answer:
                    if correct_button.collidepoint(pos):
                        score += current_question["points"]
                        current_question["used"] = True
                        showing_question_window = False
                    elif wrong_button.collidepoint(pos):
                        current_question["used"] = True
                        showing_question_window = False

pygame.quit()

