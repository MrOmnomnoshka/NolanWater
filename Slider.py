import pygame


class Slider:
    def __init__(self, name, x, y, w, min_val, max_val, step, initial):
        self.name = name
        self.rect = pygame.Rect(x, y, w, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.value = initial
        self.dragging = False

    def move_slider(self, event):
        rel_x = event.pos[0] - self.rect.x
        rel_x = max(0, min(rel_x, self.rect.width))
        ratio = rel_x / self.rect.width
        raw = self.min_val + ratio * (self.max_val - self.min_val)
        self.value = round(raw / self.step) * self.step

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.move_slider(event)
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.move_slider(event)

    def draw(self, surface, font):
        # rect
        pygame.draw.rect(surface, (100, 100, 100), self.rect)
        fill = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.rect(surface, (200, 200, 255), (self.rect.x, self.rect.y, fill, self.rect.height))
        name_surf = font.render(f"{self.name}: {self.value:.3f}", True, (255, 255, 255))

        # handle
        pygame.draw.rect(surface, (250, 100, 100), [fill+20, self.rect.y, 2, 20])

        # update
        surface.blit(name_surf, (self.rect.x, self.rect.y - 20))
