import random
import time

# Initialize game variables
game_width, game_height = 800, 600
block_size = 20
snake_speed = 15
game_duration = 300  # Game duration in seconds (5 minutes)

# Colors
BLACK = "#000000"
WHITE = "#FFFFFF"
RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"

class Snake:
    def __init__(self, color, is_ai=False):
        self.snake_list = [[random.randint(0, game_width - block_size) // block_size * block_size,
                            random.randint(0, game_height - block_size) // block_size * block_size]]
        self.snake_length = 1
        self.x = self.snake_list[0][0]
        self.y = self.snake_list[0][1]
        self.x_change = 0
        self.y_change = 0
        self.color = color
        self.is_ai = is_ai
        self.score = 0

    def update(self, food):
        if self.is_ai:
            # Implement AI logic here
            head_x, head_y = self.snake_list[-1]
            food_x, food_y = food.x, food.y
            
            if random.random() < 0.7:  # 70% chance of polarized movement
                if abs(head_x - food_x) > abs(head_y - food_y):
                    if head_x < food_x and self.x_change >= 0:
                        self.x_change, self.y_change = block_size, 0
                    elif head_x > food_x and self.x_change <= 0:
                        self.x_change, self.y_change = -block_size, 0
                    else:
                        self.y_change = block_size if head_y < food_y else -block_size
                        self.x_change = 0
                else:
                    if head_y < food_y and self.y_change >= 0:
                        self.x_change, self.y_change = 0, block_size
                    elif head_y > food_y and self.y_change <= 0:
                        self.x_change, self.y_change = 0, -block_size
                    else:
                        self.x_change = block_size if head_x < food_x else -block_size
                        self.y_change = 0
            else:  # 30% chance of random movement
                possible_moves = [(block_size, 0), (-block_size, 0), (0, block_size), (0, -block_size)]
                self.x_change, self.y_change = random.choice(possible_moves)
        
        self.x += self.x_change
        self.y += self.y_change

        # Wrap around boundaries
        self.x = self.x % game_width
        self.y = self.y % game_height

        self.snake_list.append([self.x, self.y])
        if len(self.snake_list) > self.snake_length:
            del self.snake_list[0]

    def is_collision(self):
        head_x, head_y = self.snake_list[-1]
        for block in self.snake_list[:-1]:
            if block == [head_x, head_y]:
                return True
        return False

    def eat_food(self, food):
        head_x, head_y = self.snake_list[-1]
        if head_x == food.x and head_y == food.y:
            self.snake_length += 1
            self.score += 1
            return True
        return False

class Food:
    def __init__(self):
        self.reposition()

    def reposition(self):
        self.x = round(random.randrange(0, game_width - block_size) / block_size) * block_size
        self.y = round(random.randrange(0, game_height - block_size) / block_size) * block_size

def game_loop():
    user_snake = Snake(GREEN)
    ai_snake = Snake(BLUE, is_ai=True)
    food = Food()

    start_time = time.time()

    while time.time() - start_time < game_duration:
        user_snake.update(food)
        ai_snake.update(food)

        if user_snake.is_collision():
            user_snake = Snake(GREEN)
        if ai_snake.is_collision():
            ai_snake = Snake(BLUE, is_ai=True)
            ai_snake.score = 0  # Reset AI score when it collides

        if user_snake.eat_food(food):
            food.reposition()
        elif ai_snake.eat_food(food):
            food.reposition()

        # Return game state
        return {
            'user_snake': user_snake.snake_list,
            'ai_snake': ai_snake.snake_list,
            'food': [food.x, food.y],
            'user_score': user_snake.score,
            'ai_score': ai_snake.score,
            'time_remaining': int(game_duration - (time.time() - start_time))
        }

    # Game over
    if ai_snake.score > user_snake.score:
        return {
            'game_over': True,
            'message': "AI will replace you AHAHA - AbdullahAI",
            'winner': 'AI'
        }
    else:
        return {
            'game_over': True,
            'message': "Game Over!",
            'winner': 'User'
        }

def handle_key_press(key, user_snake):
    if key == 'ArrowLeft' and user_snake.x_change == 0:
        user_snake.x_change = -block_size
        user_snake.y_change = 0
    elif key == 'ArrowRight' and user_snake.x_change == 0:
        user_snake.x_change = block_size
        user_snake.y_change = 0
    elif key == 'ArrowUp' and user_snake.y_change == 0:
        user_snake.y_change = -block_size
        user_snake.x_change = 0
    elif key == 'ArrowDown' and user_snake.y_change == 0:
        user_snake.y_change = block_size
        user_snake.x_change = 0

# The main game loop and event handling will be implemented in JavaScript
