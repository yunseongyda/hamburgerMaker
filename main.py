import pygame
import cv2
import numpy as np
import sys
import random
import mediapipe as mp
import time
import json
import os

pygame.init()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Burger Maker")

font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (0, 100, 255)
DARK_BLUE = (0, 50, 150)
BROWN = (222, 184, 135)
GREEN = (0, 200, 0)
DARK_RED = (150, 0, 0)
PINK = (255, 105, 180)
OLIVE = (128, 128, 0)
TOMATO = (255, 99, 71)

# 이름 저장 완료 타이머
saved_message_timer = 0
saved_message_alpha = 0

ranking_file = "ranking.json"
input_active = False
user_input = ""

def save_score(name, score):
    data = []
    if os.path.exists(ranking_file):
        with open(ranking_file, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append({"name": name, "score": score})
    data.sort(key=lambda x: x["score"], reverse=True)
    with open(ranking_file, "w") as f:
        json.dump(data[:10], f, indent=2)  # Top 10만 저장

def draw_input_modal():
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 120, 400, 80), border_radius=12)
    pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 120, 400, 80), 2, border_radius=12)
    input_text = font.render(f"Enter your name: {user_input}", True, BLACK)
    screen.blit(input_text, input_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 160)))


clock = pygame.time.Clock()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils
menu_active = True
running = True

#option_button = pygame.image.load('an_image.png').convert()
#rect = IMAGE.get_rect()
#rect.center = (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2)

start_button_img = pygame.image.load("resources/images/button.png").convert_alpha()
start_button_img = pygame.transform.scale(start_button_img, (450, 150))
start_button_img.set_colorkey((255, 255, 255))
start_button_rect = start_button_img.get_rect(center=(SCREEN_WIDTH // 2 + 2, SCREEN_HEIGHT // 2 + 400))

quit_button_img = pygame.image.load("resources/images/button.png").convert_alpha()
quit_button_img = pygame.transform.scale(quit_button_img, (450, 150))
quit_button_img.set_colorkey((255, 255, 255))
quit_button_rect = quit_button_img.get_rect(center=(SCREEN_WIDTH // 2 + 523, SCREEN_HEIGHT // 2 + 400))

option_button_img = pygame.image.load("resources/images/button.png").convert_alpha()
option_button_img = pygame.transform.scale(option_button_img, (450, 150))
option_button_img.set_colorkey((255, 255, 255))
option_button_rect = option_button_img.get_rect(center=(SCREEN_WIDTH // 2 - 530, SCREEN_HEIGHT // 2 + 400))

hand_status = "Detecting hand..."
prev_hand_status = "None"
message_alpha = 0
message_timer = 0
MESSAGE_DURATION = 60
hand_screen_pos = None

held_item = None
items_on_screen = []

ITEM_RADIUS = 50
PLATE_RADIUS = 100
plate_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)

ingredient_names = ["bun", "lettuce", "patty", "bacon", "pickle", "tomato"]
ingredient_spawns = {}
spacing = ITEM_RADIUS * 2 + 20
start_x = (SCREEN_WIDTH - (spacing * (len(ingredient_names) - 1))) // 2
start_y = SCREEN_HEIGHT - ITEM_RADIUS - 40
for i, name in enumerate(ingredient_names):
    ingredient_spawns[name] = (start_x + i * spacing, start_y)

ingredient_colors = {
    "bun": BROWN,
    "lettuce": GREEN,
    "patty": DARK_RED,
    "bacon": PINK,
    "pickle": OLIVE,
    "tomato": TOMATO
}

reset_button_rect = pygame.Rect(SCREEN_WIDTH - 300, SCREEN_HEIGHT //2 +50, 160, 60)
submit_button_rect = pygame.Rect(SCREEN_WIDTH - 300, SCREEN_HEIGHT //2 -150, 200, 150)

all_recipes = []
for _ in range(20):
    recipe = ["bun"] + random.sample(ingredient_names[1:], random.randint(2, 4)) + ["bun"]
    all_recipes.append(recipe)

current_recipe = all_recipes.pop(random.randrange(len(all_recipes)))

start_time = time.time()
score = 0
total_accuracy_score = 0
round_count = 0
cheat_index = 0

BURGER_TIME_LIMIT = 30
burger_start_time = time.time()

def draw_menu():
    main_menu_bg = pygame.image.load('resources/images/main_menu_bg.png').convert()
    main_menu_bg = pygame.transform.scale(main_menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(main_menu_bg, (0, 0))

    # 버튼 이미지
    screen.blit(start_button_img, start_button_rect)
    screen.blit(option_button_img, option_button_rect)
    screen.blit(quit_button_img, quit_button_rect)

    # Play 텍스트
    play_text = big_font.render("Play", True, WHITE)
    play_rect = play_text.get_rect(center=start_button_rect.center)
    screen.blit(play_text, play_rect)

    # Option 텍스트
    option_text = big_font.render("Options", True, WHITE)
    option_rect = option_text.get_rect(center=option_button_rect.center)
    screen.blit(option_text, option_rect)

    # Quit 텍스트
    quit_text = big_font.render("Quit", True, WHITE)
    quit_rect = quit_text.get_rect(center=quit_button_rect.center)
    screen.blit(quit_text, quit_rect)

    pygame.display.flip()

def draw_status():
    elapsed = int(time.time() - start_time) - 1
    time_text = font.render(f"Time: {elapsed}s", True, BLACK)
    score_text = font.render(f"Score: {score}", True, BLACK)
    round_text = font.render(f"Burger {round_count + 1} / 20", True, BLACK)  # 햄버거 개수 출력
    screen.blit(time_text, time_text.get_rect(center=(SCREEN_WIDTH // 2, 30)))
    screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 70)))
    screen.blit(round_text, round_text.get_rect(center=(SCREEN_WIDTH // 2, 110)))

def draw_buttons():
    pygame.draw.rect(screen, DARK_GRAY, reset_button_rect, border_radius=8)
    text2 = font.render("Reset", True, WHITE)
    screen.blit(text2, text2.get_rect(center=reset_button_rect.center))
    pygame.draw.rect(screen, BLUE, submit_button_rect, border_radius=8)
    text3 = font.render("Bell", True, WHITE)
    screen.blit(text3, text3.get_rect(center=submit_button_rect.center))

def draw_recipe(recipe):
    x, y = 60, 500
    for ingredient in reversed(recipe):
        color = ingredient_colors.get(ingredient, WHITE)
        pygame.draw.circle(screen, color, (x, y), 30)
        pygame.draw.circle(screen, WHITE, (x, y), 30, 2)
        y += 50

def get_camera_surface():
    global hand_status, message_alpha, message_timer, hand_screen_pos
    ret, frame = cap.read()
    if not ret:
        return None
    frame = cv2.flip(frame, 0)  # 상하 반전 추가
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    hand_screen_pos = None
    hand_status = "None"
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            folded = {
                "Thumb": hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x,
                "Index": hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y,
                "Middle": hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y,
                "Ring": hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y,
                "Pinky": hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y
            }
            hand_status = "Fist" if sum(folded.values()) >= 3 else "Open"
            if (not folded["Middle"] and all(folded[f] for f in ["Thumb", "Index", "Ring", "Pinky"])):
                message_alpha = 255
                message_timer = MESSAGE_DURATION
            cx = 1.0 - hand_landmarks.landmark[9].x
            cy = hand_landmarks.landmark[9].y
            x_offset = 80 if hand_landmarks.landmark[9].x > 0.9 else 0
            y_offset = -40 if hand_landmarks.landmark[9].y > 0.85 else 0
            hand_screen_pos = (int(cx * SCREEN_WIDTH - x_offset), int(cy * SCREEN_HEIGHT + y_offset))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    return pygame.transform.scale(pygame.surfarray.make_surface(frame), (800-200, 600-200))

def evaluate_recipe():
    global score, current_recipe, total_accuracy_score, round_count, burger_start_time
    built = [item["type"] for item in reversed(items_on_screen)]
    correct = current_recipe
    match = 0
    for i in range(min(len(built), len(correct))):
        if built[i] == correct[i]:
            match += 1
    accuracy = match / len(correct)
    accuracy_score = int(accuracy * 100)

    elapsed_burger_time = int(time.time() - burger_start_time)
    time_bonus = max(0, BURGER_TIME_LIMIT - elapsed_burger_time)
    time_score = int(time_bonus * accuracy)

    if elapsed_burger_time > BURGER_TIME_LIMIT:
        print("TIME OUT! No score for this burger.")
        accuracy_score = 0
        time_score = 0

    total_accuracy_score += accuracy_score
    round_count += 1
    score += accuracy_score + time_score

    print(f"Submitted! Accuracy: {accuracy:.2f}, +{accuracy_score} points, Time bonus: {time_score}")

    if all_recipes:
        burger_start_time = time.time()
        return all_recipes.pop(random.randrange(len(all_recipes)))
    else:
        return None

def end_game():
    global running, menu_active, score, round_count, total_accuracy_score, current_recipe, all_recipes, cheat_index
    global input_active, user_input
    global saved_message_timer, saved_message_alpha

    leave_record_button_rect = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 100, 240, 50)
    input_active = False
    user_input = ""

    while True:
        screen.fill(GRAY)

        #게임오버
        title = big_font.render("Game Over!", True, RED)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)))
        
        #최종 점수
        final_score = font.render(f"Final Score: {score}", True, BLACK)
        screen.blit(final_score, final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        exit_msg = font.render("Press ESC to exit / SPACE to return to Menu", True, DARK_GRAY)
        screen.blit(exit_msg, exit_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)))

        pygame.draw.rect(screen, BLUE, leave_record_button_rect, border_radius=8)
        screen.blit(font.render("Leave a record", True, WHITE),
                    font.render("Leave a record", True, WHITE).get_rect(center=leave_record_button_rect.center))

        if input_active:
            draw_input_modal()

        # 저장 완료 메시지 그리기
        if saved_message_timer > 0:
            saved_surface = font.render("Saved!", True, (0, 150, 0))
            saved_surface.set_alpha(saved_message_alpha)
            screen.blit(saved_surface, saved_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200)))
            saved_message_timer -= 1
            if saved_message_timer < 30:
                saved_message_alpha = max(0, int(255 * (saved_message_timer / 30)))  # 부드럽게 사라지도록

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN and user_input.strip():
                        save_score(user_input.strip(), score)
                        input_active = False
                        user_input = ""

                        # 저장 메시지 초기화
                        saved_message_timer = 120  # 2초 정도 유지 (60프레임 기준)
                        saved_message_alpha = 255
                    elif event.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    else:
                        if len(user_input) < 10:
                            user_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_SPACE:
                        # 상태 초기화
                        menu_active = True
                        score = 0
                        round_count = 0
                        total_accuracy_score = 0
                        cheat_index = 0
                        all_recipes = []
                        for _ in range(20):
                            recipe = ["bun"] + random.sample(ingredient_names[1:], random.randint(2, 4)) + ["bun"]
                            all_recipes.append(recipe)
                        current_recipe = all_recipes.pop(random.randrange(len(all_recipes)))
                        return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if leave_record_button_rect.collidepoint(event.pos):
                    input_active = True



while running:
    if menu_active:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    menu_active = False
                    start_time = time.time()
                    burger_start_time = time.time()
                elif quit_button_rect.collidepoint(event.pos):
                    running = False
        continue

    screen.fill(GRAY)
    draw_status()

    for event in pygame.event.get():
        if event.type == pygame.QUIT :
                pygame.quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and current_recipe:
                if cheat_index < len(current_recipe):
                    items_on_screen.insert(0, {"type": current_recipe[cheat_index]})
                    cheat_index += 1
            elif event.key == pygame.K_ESCAPE:
                end_game()
    pygame.draw.circle(screen, DARK_GRAY, plate_pos, PLATE_RADIUS)
    for idx, item in enumerate(reversed(items_on_screen)):
        y_offset = -idx * (ITEM_RADIUS // 2)
        draw_pos = (plate_pos[0], plate_pos[1] + y_offset)
        pygame.draw.circle(screen, ingredient_colors[item["type"]], draw_pos, ITEM_RADIUS)
        pygame.draw.circle(screen, WHITE, draw_pos, ITEM_RADIUS, 2)

    if held_item:
        pygame.draw.circle(screen, ingredient_colors[held_item["type"]], held_item["pos"], ITEM_RADIUS)
        pygame.draw.circle(screen, WHITE, held_item["pos"], ITEM_RADIUS, 2)

    for name, pos in ingredient_spawns.items():
        pygame.draw.circle(screen, ingredient_colors[name], pos, ITEM_RADIUS)
        pygame.draw.circle(screen, WHITE, pos, ITEM_RADIUS, 2)

    draw_buttons()
    if current_recipe:
        draw_recipe(current_recipe)

    if hand_screen_pos:
        color = DARK_BLUE if hand_status == "Fist" else BLUE
        pygame.draw.circle(screen, color, hand_screen_pos, 15)
        pygame.draw.circle(screen, WHITE, hand_screen_pos, 15, 2)

    camera_surface = get_camera_surface()
    if camera_surface:
        screen.blit(camera_surface, (0, 0))

    if hand_screen_pos and hand_status == "Fist" and prev_hand_status != "Fist":
        if reset_button_rect.collidepoint(hand_screen_pos):
            items_on_screen.clear()
        if submit_button_rect.collidepoint(hand_screen_pos):
            current_recipe = evaluate_recipe()
            items_on_screen.clear()
            cheat_index = 0
            if current_recipe is None:
                end_game()
        for name, pos in ingredient_spawns.items():
            if np.linalg.norm(np.array(hand_screen_pos) - np.array(pos)) < ITEM_RADIUS + 10:
                held_item = {"type": name, "pos": hand_screen_pos}

    if held_item:
        if hand_screen_pos:
            if hand_status == "Fist":
                held_item["pos"] = hand_screen_pos
            else:
                if np.linalg.norm(np.array(hand_screen_pos) - np.array(plate_pos)) < PLATE_RADIUS + 10:
                    items_on_screen.insert(0, {"type": held_item["type"]})
                held_item = None

    if message_timer > 0:
        surface = big_font.render("Don't be rude!", True, (255, 0, 0))
        surface.set_alpha(message_alpha)
        screen.blit(surface, surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        message_timer -= 1
        if message_timer < MESSAGE_DURATION:
            message_alpha = max(0, int(255 * (message_timer / MESSAGE_DURATION)))

    pygame.display.flip()
    clock.tick(30)
    prev_hand_status = hand_status

cap.release()
pygame.quit()
sys.exit()