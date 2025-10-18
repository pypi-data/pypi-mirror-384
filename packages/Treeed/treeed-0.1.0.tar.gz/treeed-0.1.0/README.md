# Py3DGraphics

Библиотека для создания и отображения 3D объектов с помощью Tkinter.

## Установка

```bash
pip install py3dgraphics
```

## Использование

```python
from py3dgraphics import Point3D, Object3D, Scene3D

# Создание куба
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

## Классы

- `Point3D`: Представляет 3D точку.
- `Object3D`: Представляет 3D объект с точками и рёбрами.
- `Scene3D`: Управляет сценой и отображением объектов.

## Лицензия

MIT
