#!/usr/bin/env python3
"""
jeopardy.py - Pygame Jeopardy with selectable question files and feedback sounds
"""

import os, csv, sys, pygame
from collections import defaultdict
from math import floor

pygame.init()
pygame.mixer.init()

# ---------- Config ----------
xx = 1.1
SCREEN_WIDTH = int(1200 * xx)
SCREEN_HEIGHT = int(800 * xx)
FPS = 30

TOP_MARGIN = 100
LEFT_MARGIN = 40
RIGHT_MARGIN = 40
BOTTOM_MARGIN = 120

CATEGORY_HEIGHT = 80
CATEGORY_PADDING = 12
TILE_MARGIN = 12
TILE_MIN_HEIGHT = 64
TILE_MIN_WIDTH = 120

#FONT_NAME = "NotoSansSC-Regular.ttf"
FONT_NAME = ""
FONT_SMALL = 18
FONT_MED = 24
FONT_LARGE = 30
TEAM_FONT_SIZE = 35

BG = (10, 10, 10)
TILE_COLOR = (30, 110, 200)
TILE_USED_COLOR = (80, 80, 80)
CATEGORY_COLOR = (20, 90, 160)
TEXT = (255, 255, 255)
HIGHLIGHT = (255, 165, 0)
CORRECT_COLOR = (30, 200, 80)
WRONG_COLOR = (200, 40, 40)
OVERLAY_BG = (250, 250, 250)
OVERLAY_TEXT = (10, 10, 10)

FEEDBACK_DURATION = 60  # frames (~2 sec at 30 FPS)

# ---------- Initialize Pygame ----------
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jeopardy")
clock = pygame.time.Clock()

font_small = pygame.font.SysFont(FONT_NAME, FONT_SMALL)
font_med = pygame.font.SysFont(FONT_NAME, FONT_MED)
font_large = pygame.font.SysFont(FONT_NAME, FONT_LARGE)
font_team = pygame.font.SysFont(FONT_NAME, TEAM_FONT_SIZE)

# ---------- Load sounds ----------
try:
    sound_correct = pygame.mixer.Sound("correct.wav")
    sound_wrong = pygame.mixer.Sound("wrong.wav")
except:
    sound_correct = sound_wrong = None

# ---------- Helpers ----------
def detect_delimiter(header_line):
    return "\t" if "\t" in header_line else ","

def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = cur + " " + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines

def parse_correct_field(correct_field):
    if not correct_field:
        return None
    c = correct_field.strip()
    if len(c) == 1 and c in "1234":
        return int(c)-1
    if len(c) == 1 and c.upper() in "ABCD":
        return ord(c.upper()) - ord("A")
    return c

# ---------- Game State ----------
team_names = ["Team A","Team B"]
team_scores = [0,0]
current_team_idx = 0

showing_overlay = False
overlay_question = None
overlay_metadata = {}

feedback_showing = False
feedback_text = ""
feedback_color = (0,0,0)
feedback_timer = 0

categories = {}
category_names = []
max_rows = 0

# ---------- File Selection ----------
QUESTION_DIR = "./"
question_files = sorted([f for f in os.listdir(QUESTION_DIR) if f.startswith("q") and f.endswith(".txt")])
showing_file_select = True
file_select_scroll = 0
file_select_item_h = 50
file_select_pad = 10

def draw_file_selection():
    screen.fill(BG)
    title = font_large.render("Select Question Set", True, TEXT)
    screen.blit(title, ((SCREEN_WIDTH-title.get_width())//2, 20))
    start_y = 100 - file_select_scroll
    for i, f in enumerate(question_files):
        rect = pygame.Rect(LEFT_MARGIN, start_y + i*(file_select_item_h+file_select_pad),
                           SCREEN_WIDTH-LEFT_MARGIN-RIGHT_MARGIN, file_select_item_h)
        pygame.draw.rect(screen, TILE_COLOR, rect, border_radius=6)
        fname = font_med.render(f, True, TEXT)
        screen.blit(fname, (rect.x+10, rect.y+(file_select_item_h-fname.get_height())//2))

# ---------- Load questions ----------
def load_questions(filename):
    global categories, category_names, max_rows, team_scores, current_team_idx
    team_scores = [0,0]
    current_team_idx = 0

    questions_raw = []
    with open(filename,"r",encoding="utf-8",newline="") as fh:
        header_line = fh.readline()
        delimiter = detect_delimiter(header_line)
    with open(filename,"r",encoding="utf-8",newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        for row in reader:
            row_lc = {k.strip(): v for k,v in row.items()}
            subtype = row_lc.get("subtype") or row_lc.get("category") or ""
            qtext = row_lc.get("question") or ""
            options = [row_lc.get(f"option{i}", "") for i in range(1,5)]
            correct_raw = row_lc.get("correct") or ""
            try:
                time_allowed = int(row_lc.get("time") or 20)
            except:
                time_allowed = 20
            square_text = row_lc.get("square_text") or "100"
            try:
                points = int(square_text)
            except:
                import re
                m = re.search(r"\d+", str(square_text))
                points = int(m.group()) if m else 100
            questions_raw.append({
                "subtype": subtype.strip(),
                "question": qtext.strip(),
                "options": [o.strip() for o in options],
                "correct_raw": correct_raw.strip(),
                "correct": parse_correct_field(correct_raw.strip()),
                "time": time_allowed,
                "square_text": str(square_text).strip(),
                "points": points,
                "used": False
            })

    categories = defaultdict(list)
    for q in questions_raw:
        categories[q["subtype"] or "Misc"].append(q)
    category_names = sorted(categories.keys())
    for cat in category_names:
        categories[cat].sort(key=lambda x:x["points"])
    max_rows = max(len(categories[c]) for c in category_names)

# ---------- Grid & Board ----------
def compute_grid():
    avail_w = SCREEN_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    col_w = max((avail_w - (len(category_names)-1)*TILE_MARGIN)/len(category_names), TILE_MIN_WIDTH)
    avail_h = SCREEN_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN - CATEGORY_HEIGHT - CATEGORY_PADDING
    tile_h = max(floor((avail_h - (max_rows-1)*TILE_MARGIN)/max_rows), TILE_MIN_HEIGHT) if max_rows>0 else TILE_MIN_HEIGHT
    return col_w, tile_h

def draw_board():
    screen.fill(BG)
    # --- team scores ---
    surf1 = font_team.render(f"{team_names[0]}: {team_scores[0]}", True, TEXT)
    surf2 = font_team.render(f"{team_names[1]}: {team_scores[1]}", True, TEXT)
    screen.blit(surf1,(LEFT_MARGIN,10))
    screen.blit(surf2,(SCREEN_WIDTH-RIGHT_MARGIN-surf2.get_width(),10))
    if current_team_idx==0:
        pygame.draw.rect(screen,HIGHLIGHT,(LEFT_MARGIN-8,6,surf1.get_width()+16,surf1.get_height()+8),3)
    else:
        pygame.draw.rect(screen,HIGHLIGHT,(SCREEN_WIDTH-RIGHT_MARGIN-surf2.get_width()-8,6,surf2.get_width()+16,surf2.get_height()+8),3)

    tile_w, tile_h = compute_grid()
    # --- categories ---
    for col_idx, cat in enumerate(category_names):
        col_x = LEFT_MARGIN + col_idx*(tile_w+TILE_MARGIN)
        cat_rect = pygame.Rect(col_x, TOP_MARGIN, tile_w, CATEGORY_HEIGHT)
        pygame.draw.rect(screen, CATEGORY_COLOR, cat_rect)
        pygame.draw.rect(screen, (0,0,0), cat_rect,2)
        cat_lines = wrap_text(cat, font_med, tile_w-20)
        total_h = len(cat_lines)*font_med.get_height()
        start_y = TOP_MARGIN + (CATEGORY_HEIGHT - total_h)//2
        for i,line in enumerate(cat_lines):
            ls = font_med.render(line, True, TEXT)
            screen.blit(ls, (col_x + (tile_w-ls.get_width())//2, start_y + i*font_med.get_height()))
    # --- question tiles ---
    for col_idx, cat in enumerate(category_names):
        col_x = LEFT_MARGIN + col_idx*(tile_w+TILE_MARGIN)
        for row_idx, q in enumerate(categories[cat]):
            tile_y = TOP_MARGIN + CATEGORY_HEIGHT + CATEGORY_PADDING + row_idx*(tile_h+TILE_MARGIN)
            rect = pygame.Rect(col_x, tile_y, tile_w, tile_h)
            color = TILE_USED_COLOR if q["used"] else TILE_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=6)
            label = q["square_text"]
            pts = font_large.render(label, True, TEXT)
            screen.blit(pts,(col_x+tile_w/2-pts.get_width()/2, tile_y+tile_h/2-pts.get_height()/2))

def get_tile_at(pos):
    x,y = pos
    tile_w, tile_h = compute_grid()
    for col_idx, cat in enumerate(category_names):
        col_x = LEFT_MARGIN + col_idx*(tile_w+TILE_MARGIN)
        for row_idx, q in enumerate(categories[cat]):
            tile_y = TOP_MARGIN + CATEGORY_HEIGHT + CATEGORY_PADDING + row_idx*(tile_h+TILE_MARGIN)
            if pygame.Rect(col_x, tile_y, tile_w, tile_h).collidepoint(x,y):
                return col_idx,row_idx
    return None,None

# ---------- Overlay ----------
def open_overlay(col_idx,row_idx):
    global showing_overlay, overlay_question, overlay_metadata
    cat = category_names[col_idx]
    q = categories[cat][row_idx]
    if q["used"]:
        return
    showing_overlay = True
    overlay_question = q
    overlay_metadata = {"col":col_idx,"row":row_idx,"option_rects":[]}
    correct = q["correct"]
    overlay_metadata["correct_index"] = correct if isinstance(correct,int) else None

def draw_overlay():
    pad = 20
    overlay_w = SCREEN_WIDTH-200
    overlay_h = SCREEN_HEIGHT-220
    ox = (SCREEN_WIDTH-overlay_w)//2
    oy = (SCREEN_HEIGHT-overlay_h)//2
    pygame.draw.rect(screen, OVERLAY_BG,(ox,oy,overlay_w,overlay_h),border_radius=8)
    pygame.draw.rect(screen, (180,180,180),(ox,oy,overlay_w,overlay_h),2,border_radius=8)
    title = f"{overlay_question['subtype']} — {overlay_question['square_text']} pts"
    screen.blit(font_med.render(title,True,OVERLAY_TEXT),(ox+pad,oy+pad))
    q_lines = wrap_text(overlay_question["question"], font_med, overlay_w-2*pad)
    for i,line in enumerate(q_lines):
        screen.blit(font_med.render(line,True,OVERLAY_TEXT),(ox+pad,oy+pad+40+i*(font_med.get_height()+4)))
    options_y = oy+pad+40+len(q_lines)*(font_med.get_height()+4)+20
    opt_h = 56
    opt_w = overlay_w-2*pad
    option_rects=[]
    for i,opt in enumerate(overlay_question["options"]):
        r = pygame.Rect(ox+pad, options_y+i*(opt_h+12), opt_w, opt_h)
        pygame.draw.rect(screen, TILE_COLOR,r,border_radius=6)
        label = f"{chr(65+i)}. {opt}"
        screen.blit(font_med.render(label,True,(255,255,255)),(r.x+12,r.y+(opt_h-font_med.get_height())//2))
        option_rects.append(r)
    overlay_metadata["option_rects"]=option_rects

# ---------- Handle click ----------
def handle_option_click(idx):
    global showing_overlay, current_team_idx
    global overlay_question, overlay_metadata
    global feedback_showing, feedback_text, feedback_color, feedback_timer

    q = overlay_question
    correct = overlay_metadata.get("correct_index")
    is_correct = (idx==correct)

    if is_correct:
        team_scores[current_team_idx]+=q["points"]
        feedback_text="CORRECT! 🎉"
        feedback_color=CORRECT_COLOR
        if sound_correct:
            sound_correct.play()
    else:
        feedback_text="WRONG ❌"
        feedback_color=WRONG_COLOR
        if sound_wrong:
            sound_wrong.play()

    q["used"]=True
    categories[q["subtype"]][overlay_metadata["row"]]["used"]=True

    current_team_idx=1-current_team_idx
    showing_overlay=False
    overlay_question=None
    overlay_metadata.clear()
    feedback_showing=True
    feedback_timer=FEEDBACK_DURATION

def draw_feedback():
    s = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
    s.fill((0,0,0,180))
    screen.blit(s,(0,0))
    surf = font_large.render(feedback_text,True,feedback_color)
    screen.blit(surf,((SCREEN_WIDTH-surf.get_width())//2,(SCREEN_HEIGHT-surf.get_height())//2))

# ---------- Main loop ----------
running=True
while running:
    clock.tick(FPS)
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            mx,my = e.pos
            if showing_file_select:
                start_y = 100 - file_select_scroll
                for i, f in enumerate(question_files):
                    rect = pygame.Rect(LEFT_MARGIN, start_y + i*(file_select_item_h+file_select_pad),
                                       SCREEN_WIDTH-LEFT_MARGIN-RIGHT_MARGIN, file_select_item_h)
                    if rect.collidepoint(mx,my):
                        load_questions(os.path.join(QUESTION_DIR,f))
                        showing_file_select = False
                        break
            elif showing_overlay:
                for i,r in enumerate(overlay_metadata.get("option_rects",[])):
                    if r.collidepoint(mx,my):
                        handle_option_click(i)
                        break
            else:
                col,row = get_tile_at((mx,my))
                if col is not None:
                    open_overlay(col,row)

    if showing_file_select:
        draw_file_selection()
    else:
        draw_board()
        if showing_overlay:
            draw_overlay()
        if feedback_showing:
            draw_feedback()
            feedback_timer -= 1
            if feedback_timer<=0:
                feedback_showing=False

    pygame.display.flip()

pygame.quit()

