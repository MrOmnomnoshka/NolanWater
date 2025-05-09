import pygame
import numpy as np
from Slider import Slider
import random

# === РАЗДЕЛ НАСТРОЕК ДОЖДЯ ===
RAIN_ENABLED = True
RAIN_INTERVAL_MS = 300  # частота появления капель (в миллисекундах)
RAIN_AMOUNT = 1         # сколько капель за раз
RAIN_AMPLITUDE = 100.0    # амплитуда капли
RAIN_RADIUS = 2         # радиус влияния

# Настройки
SCREEN_W, SCREEN_H = 600, 600
SCALE = 2  # каждый пиксель становится X×X
GRID_W, GRID_H = SCREEN_W // SCALE, SCREEN_H // SCALE

VIS_WIDTH = GRID_W * SCALE
GUI_WIDTH = 260  # под GUI
WIDTH, HEIGHT = VIS_WIDTH + GUI_WIDTH, GRID_H * SCALE

DAMPING = 0.99               # рассеивание
AMPLITUDE = 255              # амплитуда при клике
DIRECTION_FLIP_PROB = 0.01   # шанс смены направления

# Цвета
BASE_COLOR = (0, 0, 0)              # цвет фона
WAVE_COLOR = (0.5, 0.7, 1.0)        # множители RGB


class MainApp:
    screen = None
    gui_screen = None
    previous_grid = current_grid = None
    clock = None
    font = None
    sliders = []

    running = True

    sim_surface = pygame.Surface((VIS_WIDTH, HEIGHT))
    gui_surface = pygame.Surface((GUI_WIDTH, HEIGHT))

    def __init__(self):
        # Инициализация
        self.init_pygame()

        # Волновые буферы
        self.previous_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
        self.current_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)

        # self.direction_map = np.random.choice([-1, 1], size=(GRID_H, GRID_W))

        # Таймер последней капли
        self.last_rain_time = pygame.time.get_ticks()

        # Cоздаем слайдеры
        self.init_sliders()

    def start(self):
        while self.running:
            # Обработка событий
            self.event_filter()

            # На лету переделываем перменные от слайдеров
            self.sliders_setters()

            # Генерация капель-дождя
            self.rain_handler()

            # Расчёт следующего состояния
            self.calc_next_state()

            # Преобразование в картинку
            surface = self.grid_to_surface()

            # Отрисовка
            self.draw(surface)

    def rain_handler(self):
        if RAIN_ENABLED:
            now = pygame.time.get_ticks()
            if now - self.last_rain_time >= RAIN_INTERVAL_MS:
                self.spawn_random_drops()
                self.last_rain_time = now

    def spawn_random_drops(self):
        radius = RAIN_RADIUS

        """Создаёт случайные всплески на сетке."""
        height, width = self.current_grid.shape
        for _ in range(RAIN_AMOUNT):
            x = random.randint(radius, width - radius - 1)
            y = random.randint(radius, height - radius - 1)

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        self.current_grid[y + dy, x + dx] += RAIN_AMPLITUDE

    def init_pygame(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Water Ripple")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

    def init_sliders(self):
        self.sliders = [
            Slider("Damping", 0, 0, 200, 0.800, 1.1, 0.001, DAMPING),
            Slider("Amplitude", 0, 0, 200, 50, 10000, 1, AMPLITUDE),
            Slider("Rain Inter", 0, 0, 200, 1, 1000, 1, RAIN_INTERVAL_MS),
            Slider("Rain Amount", 0, 0, 200, 0, 20, 1, RAIN_AMOUNT),
            Slider("Rain Amplitude", 0, 0, 200, 50, 2000, 1, RAIN_AMPLITUDE),
            Slider("Rain Radius", 0, 0, 200, 1, 20, 1, RAIN_RADIUS),

            # Slider("FlipProb", 20, 160, 200, 0.0, 0.1, 0.001, DIRECTION_FLIP_PROB),
            # Slider("SpeedMax", 20, 280, 200, 1.0, 2.0, 0.01, SPEED_RANGE[1]),
        ]
        for i in range(len(self.sliders)):
            self.sliders[i].rect.y = 40 + i * 60 + (40 if i >= 2 else 0)
            self.sliders[i].rect.x = 20

    def sliders_setters(self):
        global DAMPING, AMPLITUDE, DIRECTION_FLIP_PROB, RAIN_INTERVAL_MS, RAIN_AMOUNT, RAIN_AMPLITUDE, RAIN_RADIUS

        if Slider.smth_changed:
            DAMPING = self.sliders[0].value
            AMPLITUDE = self.sliders[1].value
            RAIN_INTERVAL_MS = self.sliders[2].value
            RAIN_AMOUNT = self.sliders[3].value
            RAIN_AMPLITUDE = self.sliders[4].value
            RAIN_RADIUS = self.sliders[5].value
            # DIRECTION_FLIP_PROB = self.sliders[2].value

            Slider.smth_changed = False

    def event_filter(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif pygame.mouse.get_pressed()[0]:  # ЛКМ
                mx, my = pygame.mouse.get_pos()
                if mx < VIS_WIDTH:
                    # Это клик по симуляции
                    if 1 < mx < VIS_WIDTH - 1 and 1 < my < HEIGHT - 1:
                        # if 1 < grid_x < GRID_W - 1 and 1 < grid_y < GRID_H - 1:
                        self.current_grid[my // SCALE, mx // SCALE] = AMPLITUDE  # сначала Y, потом X
                else:
                    # Переводим позицию клика в область GUI
                    event.pos = (event.pos[0] - VIS_WIDTH, event.pos[1])

                    # Это клик по GUI
                    for slider in self.sliders:
                        slider.handle_event(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                for slider in self.sliders:
                    slider.dragging = False

    def calc_next_state(self):
        avg = (
                      np.roll(self.current_grid, 1, axis=0) + np.roll(self.current_grid, -1, axis=0) +
                      np.roll(self.current_grid, 1, axis=1) + np.roll(self.current_grid, -1, axis=1)
              ) / 2

        next_state = (avg - self.previous_grid) * DAMPING

        # next_state *= self.direction_map
        # next_state *= speed_map * direction_map

        # Отскок от стен (границ)
        next_state[0, :] = 0
        next_state[-1, :] = 0
        next_state[:, 0] = 0
        next_state[:, -1] = 0

        # 1% ячеек меняют направление
        # flip_mask = np.random.rand(GRID_H, GRID_W) < 0.01
        # flip_mask = np.random.rand(GRID_H, GRID_W) < DIRECTION_FLIP_PROB

        # self.direction_map[flip_mask] *= -1

        # Обновление буферов
        self.previous_grid, self.current_grid = self.current_grid, next_state

    def grid_to_surface(self):
        pixels = np.clip(self.current_grid, 0, 255).astype(np.uint8)

        # Генерация цвета 🌊
        colored = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
        colored[..., 0] = np.clip(pixels * WAVE_COLOR[0], 0, 255)
        colored[..., 1] = np.clip(pixels * WAVE_COLOR[1], 0, 255)
        colored[..., 2] = np.clip(pixels * WAVE_COLOR[2], 0, 255)

        # Создание кадра
        surface = pygame.surfarray.make_surface(colored)
        surface = pygame.transform.flip(surface, False, True)  # отражение по Y (по вертикали)
        surface = pygame.transform.scale(surface, (VIS_WIDTH, HEIGHT))

        return surface

    def draw(self, surface):
        self.sim_surface.blit(pygame.transform.rotate(surface, -90), (0, 0))

        # Вывод FPS в угол
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 255))
        text_rect = fps_text.get_rect(bottomright=(VIS_WIDTH - 10, HEIGHT - 10))
        self.sim_surface.blit(fps_text, text_rect)

        # Отрисовываем слайдеры
        self.gui_surface.fill((30, 30, 30))  # фон для GUI
        for slider in self.sliders:
            slider.draw(self.gui_surface, self.font)

        # Отображаем на экран GUI и SIM
        self.screen.blit(self.sim_surface, (0, 0))
        self.screen.blit(self.gui_surface, (VIS_WIDTH, 0))

        pygame.display.flip()
        self.clock.tick(60)


if __name__ == '__main__':
    pygame.init()

    app = MainApp()
    app.start()

    print("Exiting...")
    pygame.quit()

