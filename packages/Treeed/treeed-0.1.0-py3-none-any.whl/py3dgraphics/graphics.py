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
    def __init__(self, points, edges, speed=0.01):
        self.points = [Point3D(*p) for p in points]
        self.edges = edges
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.speed = speed

    def rotate(self, angle_x, angle_y, angle_z):
        """Поворачивает объект вокруг осей X, Y и Z."""
        for point in self.points:
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

            point.x, point.y, point.z = x, y, z

    def project(self, scale, width, height):
        """Проецирует точки объекта в 2D."""
        projected = []
        for point in self.points:
            x, y, z = point.x, point.y, point.z
            factor = scale / (z + 500)
            x_2d = x * factor + width / 2
            y_2d = y * factor + height / 2
            projected.append((x_2d, y_2d))
        return projected

    def update_rotation(self):
        """Обновляет углы вращения."""
        self.angle_x += self.speed
        self.angle_y += self.speed
        self.angle_z += self.speed
        self.rotate(self.angle_x, self.angle_y, self.angle_z)

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
