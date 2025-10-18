# Py3DGraphics

Библиотека для создания и отображения 3D объектов с помощью Tkinter.

## Установка

```bash
pip install py3dgraphics
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

cube = Object3D(points, edges, speed=0.02)
scene = Scene3D()
scene.add_object(cube)
scene.run()
```

## Классы и функции

- `Point3D`: Представляет 3D точку.
- `Object3D`: Представляет 3D объект с точками и рёбрами.
- `Scene3D`: Управляет сценой и отображением объектов.
- `create_cube(size=150, speed=0.01)`: Создаёт куб с заданными параметрами.
- `quick_scene(*objects, width=600, height=600, title="3D Сцена", bg="black")`: Быстро создаёт и запускает сцену с объектами.

## Лицензия

MIT
