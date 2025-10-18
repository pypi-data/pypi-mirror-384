import tkinter as tk
import math

class Point3D:
    """Класс для представления 3D точки."""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def to_list(self):
        return [self.x, self.y, self.z]

class Object3D:
    """Класс для 3D объекта с точками и рёбрами."""
    def __init__(self, points, edges, speed=0.01, position=(0, 0, 0)):
        # Храним оригинальные точки
        self.base_points = [Point3D(*p) for p in points]
        # А эти точки будем изменять и отрисовывать
        self.points = [Point3D(*p) for p in points]
        self.edges = edges
        self.position = Point3D(*position)
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.speed = speed

    def set_position(self, x, y, z):
        """Устанавливает новую позицию объекта."""
        self.position.x = x
        self.position.y = y
        self.position.z = z

    def move(self, dx, dy, dz):
        """Перемещает объект относительно текущей позиции."""
        self.position.x += dx
        self.position.y += dy
        self.position.z += dz

    def rotate_point(self, point, angle_x, angle_y, angle_z):
        """Вспомогательная функция для поворота одной точки. Возвращает новую точку."""
        x, y, z = point.x, point.y, point.z

        # Вращение вокруг оси Y
        new_x = x * math.cos(angle_y) - z * math.sin(angle_y)
        new_z = x * math.sin(angle_y) + z * math.cos(angle_y)
        x, z = new_x, new_z

        # Вращение вокруг оси X
        new_y = y * math.cos(angle_x) - z * math.sin(angle_x)
        new_z = y * math.sin(angle_x) + z * math.cos(angle_x)
        y, z = new_y, new_z

        # Вращение вокруг оси Z
        new_x = x * math.cos(angle_z) - y * math.sin(angle_z)
        new_y = x * math.sin(angle_z) + y * math.cos(angle_z)
        x, y = new_x, new_y

        return Point3D(x, y, z)

    def project(self, scale, width, height):
        """Проецирует точки объекта в 2D."""
        projected = []
        for point in self.points:
            # Сначала вращаем точку вокруг (0,0,0), потом сдвигаем
            x = point.x + self.position.x
            y = point.y + self.position.y
            z = point.z + self.position.z

            factor = scale / (z + 500)
            x_2d = x * factor + width / 2
            y_2d = y * factor + height / 2
            projected.append((x_2d, y_2d))
        return projected

    def update_rotation(self):
        """Обновляет углы и поворачивает объект, исходя из ОРИГИНАЛЬНЫХ точек."""
        self.angle_x += self.speed
        self.angle_y += self.speed
        self.angle_z += self.speed

        # На каждом кадре начинаем с чистого листа
        for i, base_point in enumerate(self.base_points):
            rotated_point = self.rotate_point(base_point, self.angle_x, self.angle_y, self.angle_z)
            self.points[i] = rotated_point

class Scene3D:
    """Класс для управления 3D сценой."""
    def __init__(self, width=600, height=600, title="3D Сцена", bg="black"):
        self.width = width
        self.height = height
        self.scale = 200
        self.objects = []
        self.window = tk.Tk()
        self.window.title(title)
        self.canvas = tk.Canvas(self.window, width=width, height=height, bg=bg)
        self.canvas.pack()

    def add_object(self, obj):
        """Добавляет объект в сцену."""
        self.objects.append(obj)

    def update(self):
        """Обновляет и перерисовывает сцену."""
        self.canvas.delete("all")
        for obj in self.objects:
            obj.update_rotation()
            projected_points = obj.project(self.scale, self.width, self.height)
            for edge in obj.edges:
                p1 = projected_points[edge[0]]
                p2 = projected_points[edge[1]]
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="white", width=2)
        self.window.after(15, self.update)

    def run(self):
        """Запускает анимацию и главный цикл."""
        self.update()
        self.window.mainloop()

    def update_scene(self):
        """Обновляет сцену без автоматического повторения (для ручного управления)."""
        self.canvas.delete("all")
        for obj in self.objects:
            obj.update_rotation()
            projected_points = obj.project(self.scale, self.width, self.height)
            for edge in obj.edges:
                p1 = projected_points[edge[0]]
                p2 = projected_points[edge[1]]
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="white", width=2)

def create_cube(size=150, speed=0.01, position=(0, 0, 0)):
    """Создаёт куб с заданными размерами, скоростью вращения и позицией."""
    points = [
        [-size, -size, -size],
        [ size, -size, -size],
        [ size,  size, -size],
        [-size,  size, -size],
        [-size, -size,  size],
        [ size, -size,  size],
        [ size,  size,  size],
        [-size,  size,  size]
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    return Object3D(points, edges, speed, position)

def quick_scene(*objects, width=600, height=600, title="3D Сцена", bg="black"):
    """Быстро создаёт сцену с объектами и запускает её."""
    scene = Scene3D(width, height, title, bg)
    for obj in objects:
        scene.add_object(obj)
    scene.run()
