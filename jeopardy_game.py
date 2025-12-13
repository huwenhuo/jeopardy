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

# ---------- Load sounds ----------
try:
    sound_correct = pygame.mixer.Sound("correct.wav")
    sound_wrong = pygame.mixer.Sound("wrong.wav")
except:
    sound_correct = sound_wrong = None

# --- Load dataset ---
if len(sys.argv) < 2:
    print("Usage: python program.py database_file.tsv")
    sys.exit()

csv_file = sys.argv[1]

def load_data(filename):
    global rounds_list, rounds_dict
    rounds_dict = {}
    try:
        with open(filename, newline='', encoding='utf-8') as f:
            # Use tab as delimiter, as requested in the user's saved context and previous responses
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                # Ensure core fields exist before processing
                if row.get('air_date') and row.get('round') and row.get('category') and row.get('answer'):
                    try:
                        points = int(row.get('clue_value') or row.get('cluevalue') or 0)
                    except ValueError:
                        points = 0
                        
                    clue = {
                        'question': row['answer'].strip(),
                        'answer': row['question'].strip(),
                        'points': points,
                        'used': False
                    }
                    air_date = row['air_date'].strip()
                    try:
                        rnd = int(row['round'])
                    except ValueError:
                        rnd = 1 # Default to round 1 if unparsable
                        
                    category = row['category'].strip()
                    key = (air_date, rnd)
                    if key not in rounds_dict:
                        rounds_dict[key] = {}
                    if category not in rounds_dict[key]:
                        rounds_dict[key][category] = []
                    rounds_dict[key][category].append(clue)
        rounds_list = sorted(rounds_dict.keys())
    except Exception as e:
        print(f"Error loading data from {filename}: {e}")
        sys.exit()

load_data(csv_file)

# --- Helper functions ---
def draw_board():
    screen.fill(BLACK)
    
    if not rounds_list:
        no_data_surf = font_score.render("No valid data loaded. Check TSV file.", True, RED)
        screen.blit(no_data_surf, (SCREEN_WIDTH/2 - no_data_surf.get_width()/2, SCREEN_HEIGHT/2 - 50))
        return [], None, None, []
        
    round_key = rounds_list[current_round_index]
    air_date, rnd_number = round_key
    current_categories = list(rounds_dict[round_key].keys())
    num_categories = len(current_categories)
    
    if num_categories == 0:
        no_cat_surf = font_score.render(f"Round {rnd_number} has no categories.", True, RED)
        screen.blit(no_cat_surf, (SCREEN_WIDTH/2 - no_cat_surf.get_width()/2, SCREEN_HEIGHT/2 - 50))
        return [], None, None, []
        
    col_width = (SCREEN_WIDTH - BUTTON_MARGIN_X * (num_categories + 1)) / num_categories

    score_rects = []
    # Draw team scores (top-left)
    for i in range(2):
        score_surf = font_score.render(f"{team_names[i]}: {team_scores[i]}", True, WHITE)
        x_pos = 20 + i * 500
        y_pos = 10
        score_rect = pygame.Rect(x_pos - 10, y_pos - 5, score_surf.get_width() + 20, score_surf.get_height() + 10)
        
        screen.blit(score_surf, (x_pos, y_pos))
        
        if i == current_team:
            pygame.draw.rect(screen, ORANGE, score_rect, 3)
        
        # Draw subtle border for score clickability
        pygame.draw.rect(screen, GRAY, score_rect, 1) 
        score_rects.append(score_rect) 

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
    # Find max rows dynamically based on the current round's categories
    max_rows = max(len(rounds_dict[round_key][cat]) for cat in current_categories) if current_categories else 0
    
    for row in range(max_rows):
        for col, cat in enumerate(current_categories):
            x = BUTTON_MARGIN_X + col * (col_width + BUTTON_MARGIN_X)
            y = CATEGORY_MARGIN_Y + 60 + row * (BUTTON_HEIGHT + BUTTON_MARGIN_Y)
            clues = rounds_dict[round_key].get(cat, [])
            
            if row < len(clues):
                clue = clues[row]
                color = BLUE if not clue['used'] else GRAY
                rect = pygame.Rect(x, y, col_width, BUTTON_HEIGHT)
                pygame.draw.rect(screen, color, rect)
                
                # Check for 0 points (Final Jeopardy) or other special clues
                text_label = str(clue['points'])
                if clue['points'] == 0:
                     text_label = "FINAL!"
                     
                text_surf = font_clue.render(text_label, True, WHITE)
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

    return buttons, prev_rect, next_rect, score_rects


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def show_question(clue, category):
    global current_team
    running = True
    show_answer = False
    correct_rect = wrong_rect = answer_rect = None
    line_spacing = 80
    
    # Check for Final Jeopardy: points = 0
    is_final_jeopardy = (clue['points'] == 0)
    
    # NEW STATE VARIABLE for Final Jeopardy Flow
    # 1: Wager Collection, 2: Clue Display, 3: Answer/Scoring
    if is_final_jeopardy:
        fj_stage = 1
    else:
        fj_stage = 2 # Treat regular questions as starting at stage 2 (Clue Display)

    while running:
        screen.fill(BLACK)
        
        # --- Display category ---
        cat_text = "FINAL JEOPARDY!" if is_final_jeopardy else f"Category: {category}"
        cat_color = RED if is_final_jeopardy else ORANGE
        cat_surf = font_category.render(cat_text, True, cat_color)
        screen.blit(cat_surf, (20, 20))
        
        # --- Final Jeopardy Stage 1: Wager Collection ---
        if is_final_jeopardy and fj_stage == 1:
            title = font_score.render("STAGE 1: WAGER COLLECTION", True, ORANGE)
            screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, SCREEN_HEIGHT/4))
            
            prompt_lines = [
                "*** HOST INSTRUCTION ***",
                "1. Instruct all teams to **WRITE DOWN THEIR WAGERS** in private.",
                "2. When all wagers are submitted, click **'Show Clue'**."
            ]
            for i, line in enumerate(prompt_lines):
                surf = font_clue.render(line, True, WHITE)
                screen.blit(surf, (SCREEN_WIDTH/2 - surf.get_width()/2, SCREEN_HEIGHT/4 + 100 + i*line_spacing))

            answer_rect = pygame.Rect(SCREEN_WIDTH/2-150, SCREEN_HEIGHT-150, 300, 60)
            pygame.draw.rect(screen, GREEN, answer_rect)
            screen.blit(font_category.render("Show Clue", True, WHITE), (answer_rect.x+90, answer_rect.y+15))
            
            # This is the only clickable button in this stage
            correct_rect = answer_rect
            wrong_rect = None
            
        # --- Final Jeopardy Stage 2: Clue Display (Wager placed) ---
        elif is_final_jeopardy and fj_stage == 2:
            title = font_score.render("STAGE 2: CLUE DISPLAY (Teams must write their answer!)", True, RED)
            screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, SCREEN_HEIGHT/4))

            # Display question
            lines = wrap_text(clue['question'], font_clue, SCREEN_WIDTH*0.6)
            for i, line in enumerate(lines):
                screen.blit(font_clue.render(line, True, WHITE), (20, 90 + i * line_spacing))
                
            answer_rect = pygame.Rect(SCREEN_WIDTH/2-150, SCREEN_HEIGHT-150, 300, 60)
            pygame.draw.rect(screen, ORANGE, answer_rect)
            screen.blit(font_category.render("Show Answer/Score", True, WHITE), (answer_rect.x+20, answer_rect.y+15))
            
            correct_rect = answer_rect
            wrong_rect = None

        # --- Final Jeopardy Stage 3: Answer & Score ---
        elif is_final_jeopardy and fj_stage == 3:
            # Display answer
            lines_ans = wrap_text(clue['answer'], font_clue, SCREEN_WIDTH-40)
            for i, line in enumerate(lines_ans):
                screen.blit(font_clue.render(line, True, YELLOW), (20, SCREEN_HEIGHT / 2 - 100 + i*60))

            # Manual Score Prompt
            prompt_lines = [
                "WAGER & RESPONSE REVEALED. Manual Score Adjustment Required.",
                "USE KEYS: [+] or [=] to ADD $1000, [-] to SUBTRACT $1000.",
                "[T] to TOGGLE TEAM. Adjust for both teams, then click DONE."
            ]
            for i, line in enumerate(prompt_lines):
                surf = font_score.render(line, True, RED if i == 0 else WHITE)
                screen.blit(surf, (SCREEN_WIDTH/2 - surf.get_width()/2, SCREEN_HEIGHT - 350 + i*60))

            # Done Button (exits to board)
            done_rect = pygame.Rect(SCREEN_WIDTH/2-100, SCREEN_HEIGHT-150, 200, 60)
            pygame.draw.rect(screen, GREEN, done_rect)
            screen.blit(font_category.render("Done (Exit)", True, WHITE), (done_rect.x+20, done_rect.y+15))
            
            correct_rect = done_rect
            wrong_rect = None
            
        # --- Regular Question Clue/Answer Flow ---
        else: # Regular clue (not Final Jeopardy or fj_stage is not active)
            # Display question
            lines = wrap_text(clue['question'], font_clue, SCREEN_WIDTH*0.6)
            for i, line in enumerate(lines):
                screen.blit(font_clue.render(line, True, WHITE), (20, 90 + i * line_spacing))

            if not show_answer:
                # Button: Show Answer
                answer_rect = pygame.Rect(SCREEN_WIDTH/2-100, SCREEN_HEIGHT-150, 200, 60)
                pygame.draw.rect(screen, GREEN, answer_rect)
                screen.blit(font_category.render("Show Answer", True, WHITE), (answer_rect.x+20, answer_rect.y+15))
            else:
                # Display answer
                lines_ans = wrap_text(clue['answer'], font_clue, SCREEN_WIDTH-40)
                for i, line in enumerate(lines_ans):
                    screen.blit(font_clue.render(line, True, YELLOW), (20, SCREEN_HEIGHT / 2 - 100 + i*60))

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
                
                # --- Final Jeopardy State Transitions ---
                if is_final_jeopardy:
                    if correct_rect and correct_rect.collidepoint(mx,my):
                        if fj_stage == 1:
                            fj_stage = 2 # Wager collected, move to Clue
                        elif fj_stage == 2:
                            fj_stage = 3 # Clue displayed, move to Answer/Score
                        elif fj_stage == 3:
                            clue['used'] = True # Done scoring
                            running = False # Exit to board
                        
                # --- Regular Question Flow ---
                elif not is_final_jeopardy:
                    if not show_answer and answer_rect and answer_rect.collidepoint(mx,my):
                        show_answer = True
                    
                    elif show_answer:
                        if correct_rect and correct_rect.collidepoint(mx,my):
                            handle_answer(True, clue['points'])
                            clue['used'] = True
                            running = False
                        elif wrong_rect and wrong_rect.collidepoint(mx,my):
                            handle_answer(False, clue['points'])
                            clue['used'] = True
                            running = False


def handle_answer(correct, points):
    global current_team
    if correct:
        team_scores[current_team] += points
        if sound_correct: sound_correct.play()
    else:
        team_scores[current_team] -= points # Subtract points for wrong answer
        if sound_wrong: sound_wrong.play()

    current_team = 1 - current_team  # switch turn
    

# --- Main loop ---
running = True
while running:
    # --- IMPORTANT CHANGE: draw_board now returns score_rects ---
    buttons, prev_rect, next_rect, score_rects = draw_board()
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # Manual Score Adjustment Keys
            if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                team_scores[current_team] += 1000
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                team_scores[current_team] -= 1000
            elif event.key == pygame.K_t: # 'T' to switch team
                current_team = 1 - current_team
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            
            # 1. Round navigation
            if prev_rect and prev_rect.collidepoint(mx, my):
                current_round_index = max(0, current_round_index - 1)
            elif next_rect and next_rect.collidepoint(mx, my):
                current_round_index = min(len(rounds_list) - 1, current_round_index + 1)
            
            # 2. Score adjustment (Manual Scoring)
            # Clicking the score area while on the board adjusts the current team's score by +$1000
            for i, rect in enumerate(score_rects):
                if rect.collidepoint(mx, my) and i == current_team:
                    team_scores[i] += 1000
                    break

            # 3. Clue buttons
            for b in buttons:
                if b['rect'].collidepoint(mx, my) and not b['clue']['used']:
                    # Find category for this clue
                    for cat, clues in rounds_dict[rounds_list[current_round_index]].items():
                        if b['clue'] in clues:
                            show_question(b['clue'], cat)
                            break

pygame.quit()
