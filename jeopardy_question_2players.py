import csv
import sys
import pygame

pygame.init()

# --- Screen setup ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1800, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jeopardy Game")
font_category = pygame.font.SysFont(None, 36)
font_score = pygame.font.SysFont(None, 48)
font_clue = pygame.font.SysFont(None, 48)

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
BLUE = (0, 102, 204)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 140, 0)

# --- Game state ---
team_scores = [0, 0]
team_names = ["Team 1", "Team 2"]
current_team = 0

current_round_index = 0
rounds_list = []
rounds_dict = {}  # key: (air_date, round), value: dict of categories → list of clues

BUTTON_MARGIN_X = 20
BUTTON_MARGIN_Y = 20
CATEGORY_MARGIN_Y = 80
BOTTOM_MARGIN_Y = 120
BUTTON_HEIGHT = 60

# --- Load dataset ---
if len(sys.argv) < 2:
    print("Usage: python program.py database_file.tsv")
    sys.exit()

csv_file = sys.argv[1]

def load_data(filename):
    global rounds_list, rounds_dict
    rounds_dict = {}
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['air_date'].strip() and row['round'].strip() and row['category'].strip() and row['answer'].strip():
                clue = {
                    'question': row['answer'].strip(),  # The displayed question
                    'answer': row['question'].strip(),  # The "correct" answer
                    'points': int(row['clue_value']) if row['clue_value'] else 0,
                    'used': False
                }
                air_date = row['air_date'].strip()
                rnd = int(row['round'])
                category = row['category'].strip()
                key = (air_date, rnd)
                if key not in rounds_dict:
                    rounds_dict[key] = {}
                if category not in rounds_dict[key]:
                    rounds_dict[key][category] = []
                rounds_dict[key][category].append(clue)
    rounds_list = sorted(rounds_dict.keys())

load_data(csv_file)

# --- Helper functions ---
def draw_board():
    screen.fill(BLACK)
    round_key = rounds_list[current_round_index]
    air_date, rnd_number = round_key
    current_categories = list(rounds_dict[round_key].keys())
    num_categories = len(current_categories)
    col_width = (SCREEN_WIDTH - BUTTON_MARGIN_X * (num_categories + 1)) / num_categories

    # Draw team scores (top-left)
    for i in range(2):
        score_surf = font_score.render(f"{team_names[i]}: {team_scores[i]}", True, WHITE)
        screen.blit(score_surf, (20 + i*500, 10))
        if i == current_team:
            pygame.draw.rect(screen, ORANGE, (20 + i*500 - 10, 5, score_surf.get_width()+20, score_surf.get_height()+10), 3)

    # Draw air_date and round (top-right)
    round_info = f"Air Date: {air_date}  |  Round: {rnd_number}"
    round_surf = font_score.render(round_info, True, WHITE)
    screen.blit(round_surf, (SCREEN_WIDTH - round_surf.get_width() - 20, 10))

    # Draw categories with wrapped text
    for idx, cat in enumerate(current_categories):
        x = BUTTON_MARGIN_X + idx * (col_width + BUTTON_MARGIN_X)
        wrapped_lines = wrap_text(cat, font_category, col_width)
        for i, line in enumerate(wrapped_lines):
            screen.blit(font_category.render(line, True, WHITE),
                        (x + (col_width - font_category.size(line)[0]) / 2,
                         CATEGORY_MARGIN_Y + i*30))

    # Draw clue buttons
    buttons = []
    max_rows = max(len(rounds_dict[round_key][cat]) for cat in current_categories)
    for row in range(max_rows):
        for col, cat in enumerate(current_categories):
            x = BUTTON_MARGIN_X + col * (col_width + BUTTON_MARGIN_X)
            y = CATEGORY_MARGIN_Y + 60 + row * (BUTTON_HEIGHT + BUTTON_MARGIN_Y)
            clues = rounds_dict[round_key][cat]
            if row < len(clues):
                clue = clues[row]
                color = BLUE if not clue['used'] else GRAY
                rect = pygame.Rect(x, y, col_width, BUTTON_HEIGHT)
                pygame.draw.rect(screen, color, rect)
                text_surf = font_clue.render(str(clue['points']), True, WHITE)
                screen.blit(text_surf, (x + (col_width - text_surf.get_width()) / 2,
                                        y + (BUTTON_HEIGHT - text_surf.get_height()) / 2))
                buttons.append({'rect': rect, 'clue': clue})

    # Round navigation buttons
    prev_rect = pygame.Rect(50, SCREEN_HEIGHT - BOTTOM_MARGIN_Y + 20, 200, 60)
    next_rect = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - BOTTOM_MARGIN_Y + 20, 200, 60)
    pygame.draw.rect(screen, GREEN, prev_rect)
    pygame.draw.rect(screen, GREEN, next_rect)
    prev_text = font_category.render("Prev Round", True, WHITE)
    next_text = font_category.render("Next Round", True, WHITE)
    screen.blit(prev_text, (prev_rect.x + (prev_rect.width - prev_text.get_width()) / 2,
                            prev_rect.y + (prev_rect.height - prev_text.get_height()) / 2))
    screen.blit(next_text, (next_rect.x + (next_rect.width - next_text.get_width()) / 2,
                            next_rect.y + (next_rect.height - next_text.get_height()) / 2))

    return buttons, prev_rect, next_rect


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def show_question(clue, category):
    running = True
    show_answer = False
    correct_rect = wrong_rect = answer_rect = None
    line_spacing = 80  # space between question lines

    while running:
        screen.fill(BLACK)

        # --- Display category at the top ---
        cat_surf = font_category.render(f"Category: {category}", True, ORANGE)
        screen.blit(cat_surf, (20, 20))  # top-left, orange

        # --- Display question below category ---
        lines = wrap_text(clue['question'], font_clue, SCREEN_WIDTH*0.6)
        for i, line in enumerate(lines):
            screen.blit(font_clue.render(line, True, WHITE), (20, 60 + i * line_spacing))

        # --- Buttons ---
        if not show_answer:
            answer_rect = pygame.Rect(SCREEN_WIDTH/2-100, SCREEN_HEIGHT-150, 200, 60)
            pygame.draw.rect(screen, GREEN, answer_rect)
            screen.blit(font_category.render("Show Answer", True, WHITE), (answer_rect.x+20, answer_rect.y+15))
        else:
            # Display answer
            lines_ans = wrap_text(clue['answer'], font_clue, SCREEN_WIDTH-40)
            for i, line in enumerate(lines_ans):
                screen.blit(font_clue.render(line, True, YELLOW), (20, 400 + i*30))

            # Correct / Wrong buttons
            correct_rect = pygame.Rect(SCREEN_WIDTH/2-220, SCREEN_HEIGHT-150, 200, 60)
            wrong_rect = pygame.Rect(SCREEN_WIDTH/2+20, SCREEN_HEIGHT-150, 200, 60)
            pygame.draw.rect(screen, GREEN, correct_rect)
            pygame.draw.rect(screen, RED, wrong_rect)
            screen.blit(font_category.render("Correct", True, WHITE), (correct_rect.x+50, correct_rect.y+15))
            screen.blit(font_category.render("Wrong", True, WHITE), (wrong_rect.x+60, wrong_rect.y+15))

        pygame.display.flip()

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if not show_answer and answer_rect and answer_rect.collidepoint(mx,my):
                    show_answer = True
                elif show_answer and correct_rect and correct_rect.collidepoint(mx,my):
                    handle_answer(True, clue['points'])
                    clue['used'] = True
                    running = False
                elif show_answer and wrong_rect and wrong_rect.collidepoint(mx,my):
                    handle_answer(False, clue['points'])
                    clue['used'] = True
                    running = False

def handle_answer(correct, points):
    global current_team
    if correct:
        team_scores[current_team] += points
    current_team = 1 - current_team  # switch turn

# --- Main loop ---
running = True
while running:
    buttons, prev_rect, next_rect = draw_board()
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Round navigation
            if prev_rect.collidepoint(mx, my):
                current_round_index = max(0, current_round_index - 1)
            elif next_rect.collidepoint(mx, my):
                current_round_index = min(len(rounds_list) - 1, current_round_index + 1)
            # Clue buttons
            for b in buttons:
                if b['rect'].collidepoint(mx, my):
                    # Find category for this clue
                    for cat, clues in rounds_dict[rounds_list[current_round_index]].items():
                        if b['clue'] in clues:
                            show_question(b['clue'], cat)
                            break

pygame.quit()

