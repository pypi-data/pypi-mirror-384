# Py3DGraphics

Библиотека для создания и отображения 3D объектов с помощью Tkinter. Версия 0.2.0.

## Особенности

- Создание 3D объектов с точками, рёбрами и гранями
- Вращение объектов в реальном времени
- Z-сортировка для правильного отображения глубины
- Полигональная заливка граней
- Управление объектами с клавиатуры
- Оптимизация производительности с использованием NumPy для векторных операций
- Настраиваемая толщина линий рёбер
- Независимая скорость вращения по осям X, Y, Z

## Установка

```bash
pip install treeed
```

## Быстрый старт

Создайте вращающийся куб в пару строк:

```python
from py3dgraphics import create_cube, quick_scene

cube = create_cube()  # Куб по умолчанию
quick_scene(cube)     # Запуск сцены
```

## Пример использования

```python
from py3dgraphics import create_cube, quick_scene

# Создание кубов с разными размерами и скоростями
cube1 = create_cube(size=150, speed=0.02)  # Большой, быстрый
cube2 = create_cube(size=75, speed=0.005)  # Маленький, медленный

# Запуск сцены
quick_scene(cube1, cube2)
```

## Расширенное использование

```python
from py3dgraphics import create_cube, Scene3D
import time

# Создание кубов
cube = create_cube(size=150, speed=0.009, position=(300, 0, 0))
cube1 = create_cube(size=120, speed=0.007)

# Создание сцены
scene = Scene3D()
scene.add_object(cube)
scene.add_object(cube1)

# Анимация движения
xp = 300
while True:
    xp += 1
    cube.set_position(xp, 0, 0)  # Изменение позиции
    scene.update_scene()  # Обновление сцены
    time.sleep(0.05)
```

### Цвета, заливка и управление анимацией

Объекты могут иметь разные цвета. Объекты вращаются только если их `speed > 0`. Для статичных объектов установите `speed=0`.

**Новые возможности кастомизации:**
- **Заливка граней:** Параметр `fill=True` включает заливку граней цветом, заданным в `color`.
- **Цвет контура:** Параметр `outline_color` позволяет задать цвет контура граней (по умолчанию "white").
- **По умолчанию:** Кубы отображаются только с белыми контурами без заливки, как в предыдущих версиях.

```python
from py3dgraphics import create_cube, quick_scene

# Создание кубов с разными скоростями и цветами
cube1 = create_cube(size=150, speed=0.02, color="red")  # Вращается
cube2 = create_cube(size=75, speed=0, color="blue")     # Не вращается

# Запуск сцены
quick_scene(cube1, cube2)
```

### Настраиваемая толщина линий и скорость вращения по осям

**Новые параметры кастомизации:**
- **Толщина линий:** Параметр `line_width` задаёт толщину рёбер (по умолчанию 2).
- **Скорость вращения по осям:** Параметры `speed_x`, `speed_y`, `speed_z` позволяют задать независимую скорость вращения по каждой оси.

```python
from py3dgraphics import create_cube, quick_scene

# Куб с толстыми линиями и вращением только по оси Y
cube1 = create_cube(size=150, speed_y=0.02, line_width=5, color="red")

# Куб с тонкими линиями и вращением по всем осям с разной скоростью
cube2 = create_cube(size=100, speed_x=0.01, speed_y=0.02, speed_z=0.005, line_width=1, color="blue")

# Запуск сцены
quick_scene(cube1, cube2)
```

### Управление объектом клавиатурой

Вы можете управлять одним объектом с помощью клавиатуры (WASDQE для движения по осям X, Y, Z).

```python
from py3dgraphics import create_cube, quick_scene

cube1 = create_cube(size=150, speed=0.02, color="red")
cube2 = create_cube(size=75, speed=0, color="blue")  # Управляемый

# Запуск сцены с управлением вторым кубом
quick_scene(cube1, cube2, player=cube2)
```

Или ручное управление:

```python
from py3dgraphics import create_cube, Scene3D

scene = Scene3D()
scene.add_object(create_cube())
scene.add_object(create_cube(size=100, position=(200, 0, 0), speed=0, color="green"))
scene.set_player(scene.objects[1])  # Устанавливаем второго объекта как управляемого

scene.run()
```

### Ручное создание объектов

```python
from py3dgraphics import Point3D, Object3D, Scene3D

# Создание куба вручную
CUBE_SIZE = 150
points = [
    [-CUBE_SIZE, -CUBE_SIZE, -CUBE_SIZE],
    [ CUBE_SIZE, -CUBE_SIZE, -CUBE_SIZE],
    [ CUBE_SIZE,  CUBE_SIZE, -CUBE_SIZE],
    [-CUBE_SIZE,  CUBE_SIZE, -CUBE_SIZE],
    [-CUBE_SIZE, -CUBE_SIZE,  CUBE_SIZE],
    [ CUBE_SIZE, -CUBE_SIZE,  CUBE_SIZE],
    [ CUBE_SIZE,  CUBE_SIZE,  CUBE_SIZE],
    [-CUBE_SIZE,  CUBE_SIZE,  CUBE_SIZE]
]
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]
faces = [
    (0, 1, 2, 3),  # Задняя грань
    (4, 5, 6, 7),  # Передняя грань
    (0, 4, 7, 3),  # Левая грань
    (1, 5, 6, 2),  # Правая грань
    (0, 1, 5, 4),  # Нижняя грань
    (3, 2, 6, 7)   # Верхняя грань
]

# Создание объекта с гранями для заливки
cube = Object3D(points, edges, faces, speed=0.02, color="red", fill=True, line_width=3)
scene = Scene3D()
scene.add_object(cube)
scene.run()
```

## Классы и функции

- `Point3D`: Представляет 3D точку.
- `Object3D(points, edges=None, faces=None, speed=0.01, position=(0, 0, 0), color="white", fill=False, outline_color="white", line_width=2, speed_x=None, speed_y=None, speed_z=None)`: Представляет 3D объект с точками, рёбрами и гранями. Поддерживает вращение, позиционирование и кастомизацию внешнего вида.
- `Scene3D(width=600, height=600, title="3D Сцена", bg="black")`: Управляет сценой и отображением объектов с поддержкой Z-сортировки и управления клавиатурой.
- `create_cube(size=150, speed=0.01, position=(0, 0, 0), color="white", fill=False, outline_color="white", line_width=2, speed_x=None, speed_y=None, speed_z=None)`: Создаёт куб с заданными параметрами размера, скорости вращения, позиции, цветов и толщины линий.
- `quick_scene(*objects, width=600, height=600, title="3D Сцена", bg="black", player=None)`: Быстро создаёт и запускает сцену с объектами. Параметр `player` позволяет назначить управляемый клавиатурой объект.

## Лицензия

MIT
