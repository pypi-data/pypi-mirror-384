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
    """Класс для 3D объекта с точками, рёбрами и гранями."""
    def __init__(self, points, edges=None, faces=None, speed=0.01, position=(0, 0, 0), color="white"):
        # Храним оригинальные точки
        self.base_points = [Point3D(*p) for p in points]
        # А эти точки будем изменять и отрисовывать
        self.points = [Point3D(*p) for p in points]
        self.edges = edges  # Для каркасного режима
        self.faces = faces  # Для полигонального режима
        self.position = Point3D(*position)
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.speed = speed
        self.color = color

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
        if self.speed > 0:
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
        self.player = None  # Управляемый объект
        self.move_speed = 10  # Скорость движения
        self.window.bind("<KeyPress>", self.on_key_press)

    def add_object(self, obj):
        """Добавляет объект в сцену."""
        self.objects.append(obj)

    def update(self):
        """Главный цикл анимации. Обновляет логику, перерисовывает сцену и планирует следующий кадр."""
        self.canvas.delete("all")
        # Список всех полигонов для Z-сортировки
        polygons = []
        for obj in self.objects:
            obj.update_rotation()
            projected_points = obj.project(self.scale, self.width, self.height)
            if obj.faces:
                # Рисуем полигоны
                for face in obj.faces:
                    # Вычисляем среднюю Z для сортировки
                    z_avg = sum(obj.points[i].z + obj.position.z for i in face) / len(face)
                    points_2d = [projected_points[i] for i in face]
                    polygons.append((z_avg, points_2d, obj.color))
            elif obj.edges:
                # Рисуем рёбра (каркас)
                for edge in obj.edges:
                    p1 = projected_points[edge[0]]
                    p2 = projected_points[edge[1]]
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=obj.color, width=2)
        # Сортировка полигонов по Z (от дальних к ближним)
        polygons.sort(key=lambda x: x[0], reverse=True)
        for _, points_2d, color in polygons:
            self.canvas.create_polygon(points_2d, outline="black", fill=color)
        self.window.after(16, self.update)  # ~60 FPS

    def set_player(self, obj):
        """Устанавливает объект как управляемый игроком."""
        self.player = obj

    def on_key_press(self, event):
        """Обработчик нажатий клавиш для управления игроком."""
        if self.player is None:
            return
        key = event.keysym.lower()
        if key == 'w':
            self.player.move(0, 0, -self.move_speed)
        elif key == 's':
            self.player.move(0, 0, self.move_speed)
        elif key == 'a':
            self.player.move(-self.move_speed, 0, 0)
        elif key == 'd':
            self.player.move(self.move_speed, 0, 0)
        elif key == 'q':
            self.player.move(0, -self.move_speed, 0)
        elif key == 'e':
            self.player.move(0, self.move_speed, 0)

    def run(self):
        """Запускает анимацию и главный цикл окна."""
        self.update()
        self.window.mainloop()

def create_cube(size=150, speed=0.01, position=(0, 0, 0), color="white"):
    """Создаёт куб с заданными размерами, скоростью вращения, позицией и цветом."""
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
    faces = [
        (0, 1, 2, 3),  # Задняя грань
        (4, 5, 6, 7),  # Передняя грань
        (0, 4, 7, 3),  # Левая грань
        (1, 5, 6, 2),  # Правая грань
        (0, 1, 5, 4),  # Нижняя грань
        (3, 2, 6, 7)   # Верхняя грань
    ]
    return Object3D(points, edges, faces, speed, position, color)

def quick_scene(*objects, width=600, height=600, title="3D Сцена", bg="black", player=None):
    """Быстро создаёт сцену с объектами и запускает её. player - объект для управления клавиатурой."""
    scene = Scene3D(width, height, title, bg)
    for obj in objects:
        scene.add_object(obj)
    if player is not None:
        scene.set_player(player)
    scene.run()
