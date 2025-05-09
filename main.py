import pygame
import numpy as np
from Slider import Slider

# Настройки
GRID_W, GRID_H = 100, 100
SCALE = 6  # каждый пиксель становится 4×4
# WIDTH, HEIGHT = GRID_W * SCALE, GRID_H * SCALE

VIS_WIDTH = GRID_W * SCALE
GUI_WIDTH = 260  # под GUI
WIDTH, HEIGHT = VIS_WIDTH + GUI_WIDTH, GRID_H * SCALE


DAMPING = 0.99
AMPLITUDE = 255                    # амплитуда при клике
DIRECTION_FLIP_PROB = 0.01   # шанс смены направления
SPEED_RANGE = (0.8, 1.2)     # min/max множители скорости

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

        # speed_map = np.random.uniform(*SPEED_RANGE, size=(GRID_H, GRID_W))
        # direction_map = np.random.choice([-1, 1], size=(GRID_H, GRID_W))

        # Cоздаем слайдеры
        self.init_sliders()

    def start(self):
        while self.running:
            # Обработка событий
            self.event_filter()

            # На лету переделываем перменные от слайдеров
            self.sliders_setters()

            # Расчёт следующего состояния
            next_state = self.calc_next_state()

            # Обновление буферов
            self.previous_grid, self.current_grid = self.current_grid, next_state

            # Преобразование в картинку
            surface = self.grid_to_surface()

            # Отрисовка
            self.draw(surface)

    def init_pygame(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Water Ripple")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

    def init_sliders(self):
        self.sliders = [
            Slider("Damping", 20, 40, 200, 0.900, 1.1, 0.001, DAMPING),
            Slider("Amplitude", 20, 100, 200, 50, 255, 1, AMPLITUDE),
            Slider("FlipProb", 20, 160, 200, 0.0, 0.1, 0.001, DIRECTION_FLIP_PROB),
            Slider("SpeedMin", 20, 220, 200, 0.5, 1.0, 0.01, SPEED_RANGE[0]),
            Slider("SpeedMax", 20, 280, 200, 1.0, 2.0, 0.01, SPEED_RANGE[1]),
        ]

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

    def sliders_setters(self):
        global DAMPING, AMPLITUDE, DIRECTION_FLIP_PROB, SPEED_RANGE

        DAMPING = self.sliders[0].value
        AMPLITUDE = self.sliders[1].value
        DIRECTION_FLIP_PROB = self.sliders[2].value
        SPEED_RANGE = (self.sliders[3].value, self.sliders[4].value)
        speed_map = np.random.uniform(*SPEED_RANGE, size=(GRID_H, GRID_W))

    def calc_next_state(self):
        # next_state = (
        #     (np.roll(current_grid, 1, axis=0) + np.roll(current_grid, -1, axis=0) +
        #      np.roll(current_grid, 1, axis=1) + np.roll(current_grid, -1, axis=1)) / 2
        #     - previous_grid
        # ) * DAMPING
        avg = (
                      np.roll(self.current_grid, 1, axis=0) + np.roll(self.current_grid, -1, axis=0) +
                      np.roll(self.current_grid, 1, axis=1) + np.roll(self.current_grid, -1, axis=1)
              ) / 2

        next_state = (avg - self.previous_grid) * DAMPING
        # next_state *= speed_map * direction_map

        # Отскок от стен (границ)
        next_state[0, :] = 0
        next_state[-1, :] = 0
        next_state[:, 0] = 0
        next_state[:, -1] = 0

        # 1% ячеек меняют направление
        # flip_mask = np.random.rand(GRID_H, GRID_W) < 0.01
        # flip_mask = np.random.rand(GRID_H, GRID_W) < DIRECTION_FLIP_PROB

        # direction_map[flip_mask] *= -1

        return next_state

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

