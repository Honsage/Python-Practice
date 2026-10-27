from random import randint
import pygame


SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

BOARD_BACKGROUND_COLOR = (0, 0, 0)

BORDER_COLOR = (93, 216, 228)

APPLE_COLOR = (255, 0, 0)

SNAKE_COLOR = (0, 255, 0)

SPEED = 15

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

pygame.display.set_caption('Змейка')

clock = pygame.time.Clock()


class GameObject:
    """Базовый класс для игровых объектов"""

    def __init__(self, position=None):
        """Инициализация игрового объекта

        Параметры:
            position: Изначальная позиция объекта
        """
        self.position = position or (
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        )
        self.body_color = (255, 255, 255)

    def draw(self):
        """Абстракция отрисовки объекта"""
        pass


class Apple(GameObject):
    """Класс игрового объекта 'яблоко'"""

    def __init__(self):
        """Инициализация яблока"""
        super().__init__()
        self.body_color = APPLE_COLOR
        self.randomize_position()

    def randomize_position(self):
        """Установление случайной позиции яблока на поле"""
        x = randint(0, GRID_WIDTH - 1) * GRID_SIZE
        y = randint(0, GRID_HEIGHT - 1) * GRID_SIZE
        self.position = (x, y)

    def draw(self):
        """Отрисовка яблока на поле"""
        rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """Класс игрового объекта 'змейка'"""

    def __init__(self):
        """Инициализация змейки"""
        super().__init__()
        self.body_color = SNAKE_COLOR
        self.reset()
        self.last = None

    def reset(self):
        """Сброс змейки в исходное состояние"""
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None

    def update_direction(self):
        """Обновление направления движения змейки"""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def get_head_position(self):
        """Получение позиции головы змейки
        Возвращаемое значение:
            tuple(int, int): Координаты головы змейки
        """
        return self.positions[0]

    def move(self):
        """Перемещение змейки"""
        head_x, head_y = self.get_head_position()
        x, y = self.direction
        next_x = (head_x + x * GRID_SIZE) % SCREEN_WIDTH
        next_y = (head_y + y * GRID_SIZE) % SCREEN_HEIGHT
        next_head = (next_x, next_y)

        if next_head in self.positions[2:]:
            self.reset()
            return

        self.last = self.positions[-1] if len(self.positions) > 1 else None

        self.positions.insert(0, next_head)

        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self):
        """Отрисовка змейки на поле"""
        for position in self.positions[:]:
            rect = (pygame.Rect(position, (GRID_SIZE, GRID_SIZE)))
            pygame.draw.rect(screen, self.body_color, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

        head_rect = pygame.Rect(self.positions[0], (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, head_rect)
        pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

        if self.last:
            last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)


def handle_keys(game_object):
    """Обработка нажатия клавиш

    Параметры:
        game_object: Игровой объект
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and game_object.direction != DOWN:
                game_object.next_direction = UP
            elif event.key == pygame.K_DOWN and game_object.direction != UP:
                game_object.next_direction = DOWN
            elif event.key == pygame.K_LEFT and game_object.direction != RIGHT:
                game_object.next_direction = LEFT
            elif event.key == pygame.K_RIGHT and game_object.direction != LEFT:
                game_object.next_direction = RIGHT


def main():
    """Описание главного игрового цикла"""
    pygame.init()

    apple = Apple()
    snake = Snake()

    while True:
        clock.tick(SPEED)
        handle_keys(snake)

        snake.update_direction()
        snake.move()

        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position()

            while apple.position in snake.positions:
                apple.randomize_position()

            print(snake.length, snake.positions, apple.position)
        screen.fill(BOARD_BACKGROUND_COLOR)
        apple.draw()
        snake.draw()

        pygame.display.update()


if __name__ == '__main__':
    main()
