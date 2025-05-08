import pygame
import numpy as np
from dearpygui.dearpygui import *
# from dearpygui.core import *
# from dearpygui.simple import *
import threading


# Настройки
GRID_W, GRID_H = 100, 100
SCALE = 4  # каждый пиксель становится 4×4
DAMPING = 0.99
WIDTH, HEIGHT = GRID_W * SCALE, GRID_H * SCALE
AMPLITUDE = 255                    # амплитуда при клике
DIRECTION_FLIP_PROB = 0.01   # шанс смены направления
SPEED_RANGE = (0.8, 1.2)     # min/max множители скорости

# Цвета
BASE_COLOR = (0, 0, 0)              # цвет фона
WAVE_COLOR = (0.5, 0.7, 1.0)        # множители RGB



# Глобальные значения, чтобы GUI и основной цикл могли использовать их
gui_values = {
    "DAMPING": DAMPING,
    "AMPLITUDE": AMPLITUDE,
    "DIRECTION_FLIP_PROB": DIRECTION_FLIP_PROB,
    "SPEED_MIN": SPEED_RANGE[0],
    "SPEED_MAX": SPEED_RANGE[1]
}

def update_values(sender, data):
    global DAMPING, AMPLITUDE, DIRECTION_FLIP_PROB, SPEED_RANGE, speed_map

    DAMPING = get_value("Затухание (DAMPING)")
    AMPLITUDE = get_value("Амплитуда капли")
    DIRECTION_FLIP_PROB = get_value("Шанс инверсии направления (%)")
    speed_min = get_value("Скорость MIN")
    speed_max = get_value("Скорость MAX")

    # Обновляем диапазон и карту скоростей
    SPEED_RANGE = (speed_min, speed_max)
    speed_map[:] = np.random.uniform(*SPEED_RANGE, size=(GRID_H, GRID_W))

create_context()
create_viewport(title='Параметры волны', width=600, height=300)

with window(label="Параметры волны"):#, width=350, height=300):
    add_text("Настройки симуляции:")

    add_slider_float(label="Затухание (DAMPING)", min_value=0.90, max_value=1.0,
                     default_value=DAMPING, callback=update_values,
                     user_data="DAMPING")
    # bind_item_to_variable("Затухание (DAMPING)", gui_values, "DAMPING")

    add_slider_float(label="Амплитуда капли", min_value=10, max_value=255,
                     default_value=AMPLITUDE, callback=update_values,
                     user_data="AMPLITUDE")
    # bind_item_to_variable("Амплитуда капли", gui_values, "AMPLITUDE")

    add_slider_float(label="Шанс инверсии направления (%)", min_value=0.0, max_value=0.2,
                     default_value=DIRECTION_FLIP_PROB, callback=update_values,
                     user_data="DIRECTION_FLIP_PROB")
    # bind_item_to_variable("Шанс инверсии направления (%)", gui_values, "DIRECTION_FLIP_PROB")

    add_slider_float(label="Скорость MIN", min_value=0.1, max_value=2.0,
                     default_value=SPEED_RANGE[0], callback=update_values,
                     user_data="SPEED_MIN")
    # bind_item_to_variable("Скорость MIN", gui_values, "SPEED_MIN")

    add_slider_float(label="Скорость MAX", min_value=0.1, max_value=2.0,
                     default_value=SPEED_RANGE[1], callback=update_values,
                     user_data="SPEED_MAX")
    # bind_item_to_variable("Скорость MAX", gui_values, "SPEED_MAX")



# def run_gui():
setup_dearpygui()
show_viewport()
start_dearpygui()
destroy_context()
# threading.Thread(target=run_gui, daemon=True).start()


# Инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Water Ripple")

# Волновые буферы
prev = np.zeros((GRID_H, GRID_W), dtype=np.float32)
curr = np.zeros((GRID_H, GRID_W), dtype=np.float32)


# speed_map = np.random.uniform(0.8, 1.2, size=(GRID_H, GRID_W))
speed_map = np.random.uniform(*SPEED_RANGE, size=(GRID_H, GRID_W))
direction_map = np.random.choice([-1, 1], size=(GRID_H, GRID_W))


clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 18)

running = True
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif pygame.mouse.get_pressed()[0]:  # ЛКМ
            mx, my = pygame.mouse.get_pos()
            if 1 < mx < WIDTH - 1 and 1 < my < HEIGHT - 1:
                # curr[my, mx] = 255  # исправлено: сначала Y, потом X
                grid_x = mx // SCALE
                grid_y = my // SCALE
                if 1 < grid_x < GRID_W - 1 and 1 < grid_y < GRID_H - 1:
                    curr[grid_y, grid_x] = AMPLITUDE

    # Расчёт следующего состояния
    # next_state = (
    #     (np.roll(curr, 1, axis=0) + np.roll(curr, -1, axis=0) +
    #      np.roll(curr, 1, axis=1) + np.roll(curr, -1, axis=1)) / 2
    #     - prev
    # ) * DAMPING
    avg = (
                  np.roll(curr, 1, axis=0) + np.roll(curr, -1, axis=0) +
                  np.roll(curr, 1, axis=1) + np.roll(curr, -1, axis=1)
          ) / 2

    next_state = (avg - prev) * DAMPING
    # next_state *= speed_map * direction_map

    # Отскок от стен (границ)
    next_state[0, :] = 0
    next_state[-1, :] = 0
    next_state[:, 0] = 0
    next_state[:, -1] = 0

    # Обновление буферов
    prev, curr = curr, next_state

    # Преобразование в картинку
    pixels = np.clip(curr, 0, 255).astype(np.uint8)

    # Генерация цвета 🌊
    colored = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    colored[..., 0] = np.clip(pixels * WAVE_COLOR[0], 0, 255)
    colored[..., 1] = np.clip(pixels * WAVE_COLOR[1], 0, 255)
    colored[..., 2] = np.clip(pixels * WAVE_COLOR[2], 0, 255)

    # 1% ячеек меняют направление
    # flip_mask = np.random.rand(GRID_H, GRID_W) < 0.01
    # flip_mask = np.random.rand(GRID_H, GRID_W) < DIRECTION_FLIP_PROB

    # direction_map[flip_mask] *= -1

    # Создание кадра
    surface = pygame.surfarray.make_surface(colored)
    surface = pygame.transform.flip(surface, False,  True)  # отражение по Y (по вертикали)
    surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))

    screen.blit(pygame.transform.rotate(surface, -90), (0, 0))

    # Вывод FPS в угол
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
    text_rect = fps_text.get_rect(bottomright=(WIDTH - 10, HEIGHT - 10))
    screen.blit(fps_text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
