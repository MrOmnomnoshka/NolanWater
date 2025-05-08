import pygame
import numpy as np


# Настройки
GRID_W, GRID_H = 100, 100
SCALE = 6  # каждый пиксель становится 4×4
WIDTH, HEIGHT = GRID_W * SCALE, GRID_H * SCALE
DAMPING = 0.99
AMPLITUDE = 255                    # амплитуда при клике
DIRECTION_FLIP_PROB = 0.01   # шанс смены направления
SPEED_RANGE = (0.8, 1.2)     # min/max множители скорости

# Цвета
BASE_COLOR = (0, 0, 0)              # цвет фона
WAVE_COLOR = (0.5, 0.7, 1.0)        # множители RGB


class MainApp:
    screen = None
    previous_grid = current_grid = None
    clock = None
    font = None

    running = True

    def __init__(self):
        # Инициализация
        self.init_pygame()

        # Волновые буферы
        self.previous_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
        self.current_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)

        # speed_map = np.random.uniform(*SPEED_RANGE, size=(GRID_H, GRID_W))
        # direction_map = np.random.choice([-1, 1], size=(GRID_H, GRID_W))


    def start(self):
        while self.running:
            # Обработка событий
            self.event_filter()

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


    def event_filter(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif pygame.mouse.get_pressed()[0]:  # ЛКМ
                mx, my = pygame.mouse.get_pos()
                if 1 < mx < WIDTH - 1 and 1 < my < HEIGHT - 1:
                    grid_x = mx // SCALE
                    grid_y = my // SCALE
                    if 1 < grid_x < GRID_W - 1 and 1 < grid_y < GRID_H - 1:
                        self.current_grid[grid_y, grid_x] = AMPLITUDE  # сначала Y, потом X

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
        surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))

        return surface

    def draw(self, surface):
        self.screen.blit(pygame.transform.rotate(surface, -90), (0, 0))

        # Вывод FPS в угол
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 255))
        text_rect = fps_text.get_rect(bottomright=(WIDTH - 10, HEIGHT - 10))
        self.screen.blit(fps_text, text_rect)

        pygame.display.flip()
        self.clock.tick(60)


if __name__ == '__main__':
    pygame.init()

    app = MainApp()
    app.start()

    print("Exiting...")
    pygame.quit()

