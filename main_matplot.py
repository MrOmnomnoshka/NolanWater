import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Настройки
size = 200
c = 1.0
dt = 1.0
dx = 1.0
damping = 0.999
coef = (c * dt / dx)**2

# Состояния
u_prev = np.zeros((size, size))
u_curr = np.zeros((size, size))
u_next = np.zeros((size, size))

# Добавление капли при клике
def on_click(event):
    if event.inaxes:
        x, y = int(event.xdata), int(event.ydata)
        if 3 <= x < size-3 and 3 <= y < size-3:
            # Заменяем квадратный всплеск на гауссову блямбу
            for j in range(-3, 4):
                for i in range(-3, 4):
                    r2 = i ** 2 + j ** 2
                    if 0 <= y + j < size and 0 <= x + i < size:
                        u_curr[y + j, x + i] += 5.0 * np.exp(-r2 / 4.0)
            u_prev[:, :] = u_curr  # важно: синхронизируем предыдущую волну
            print(f"Капля в ({x}, {y})")

# Обновление каждого кадра
def update(frame):
    global u_prev, u_curr, u_next

    # Расчёт Лапласиана (ручной, без roll)
    laplace = (
        u_curr[0:-2, 1:-1] +  # верх
        u_curr[2:, 1:-1] +    # низ
        u_curr[1:-1, 0:-2] +  # лево
        u_curr[1:-1, 2:] -    # право
        4 * u_curr[1:-1, 1:-1]
    )

    # Обновление только центральной части
    u_next[1:-1, 1:-1] = (
        2 * u_curr[1:-1, 1:-1]
        - u_prev[1:-1, 1:-1]
        + coef * laplace
    ) * damping

    # Отражающие граничные условия (Neumann)
    u_next[0, :] = u_next[1, :]
    u_next[-1, :] = u_next[-2, :]
    u_next[:, 0] = u_next[:, 1]
    u_next[:, -1] = u_next[:, -2]

    # Обновление массивов
    u_prev, u_curr = u_curr, u_next.copy()

    img.set_data(u_curr)
    return [img]

# Настройка отображения
fig, ax = plt.subplots()
img = ax.imshow(u_curr, cmap='seismic', vmin=-1, vmax=1, interpolation='bilinear')
ax.set_title("Кликни, чтобы уронить каплю")
ax.set_axis_off()
fig.canvas.mpl_connect('button_press_event', on_click)

# Запуск анимации
ani = animation.FuncAnimation(fig, update, interval=30, blit=True)
plt.show()
