import pygame
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
game_width, game_height = 800, 600
width, height = game_width, game_height
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('User vs AI Snake Game')

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

# Snake settings
block_size = 20
snake_speed = 15
game_duration = 300  # Game duration in seconds (5 minutes)

# Neural Network Hyperparameters
learning_rate = 0.001
gamma = 0.99  # Discount factor for future rewards
epsilon = 0.1  # Exploration rate

# Font settings
font_style = pygame.font.SysFont(None, 30)

def message(msg, color, y_displace=0):
    mesg = font_style.render(msg, True, color)
    text_rect = mesg.get_rect(center=(width/2, height/2 + y_displace))
    screen.blit(mesg, text_rect)

class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.fc1 = nn.Linear(12, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 4)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

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
        if is_ai:
            self.brain = NeuralNetwork()
            self.optimizer = optim.Adam(self.brain.parameters(), lr=learning_rate)
            self.memory = []

    def update(self, food):
        if self.is_ai:
            input_state = self.get_input_state(food)
            action = self.get_action(input_state)
            
            # Implement more random and polarized movement for AI
            head_x, head_y = self.snake_list[-1]
            food_x, food_y = food.x, food.y
            
            # Randomly choose between polarized movement and random movement
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
            
            # Store the experience for learning
            reward = 0
            if self.eat_food(food):
                reward = 10
            elif self.is_collision():
                reward = -10
            else:
                # Reward moving towards food
                distance_before = abs(head_x - food_x) + abs(head_y - food_y)
                distance_after = abs(self.x + self.x_change - food_x) + abs(self.y + self.y_change - food_y)
                if distance_after < distance_before:
                    reward = 1
                else:
                    reward = -1
            
            next_state = self.get_input_state(food)
            self.memory.append((input_state, action, reward, next_state, not self.is_collision()))
            
            # Learn from experience
            self.learn()
        
        self.x += self.x_change
        self.y += self.y_change

        # Wrap around boundaries
        self.x = self.x % game_width
        self.y = self.y % game_height

        self.snake_list.append([self.x, self.y])
        if len(self.snake_list) > self.snake_length:
            del self.snake_list[0]

    def get_input_state(self, food):
        head_x, head_y = self.snake_list[-1]
        return np.array([
            head_x / game_width,
            head_y / game_height,
            (game_width - head_x) / game_width,
            (game_height - head_y) / game_height,
            (food.x - head_x) / game_width,
            (food.y - head_y) / game_height,
            1 if self.x_change < 0 else 0,
            1 if self.x_change > 0 else 0,
            1 if self.y_change < 0 else 0,
            1 if self.y_change > 0 else 0,
            self.check_collision_ahead(),
            len(self.snake_list) / 100
        ])

    def get_action(self, state):
        if random.random() < epsilon:
            return random.randint(0, 3)
        state = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.brain(state)
        return torch.argmax(q_values).item()

    def learn(self):
        if len(self.memory) < 1000:  # Wait until we have enough experiences
            return

        batch = random.sample(self.memory, 32)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)

        current_q_values = self.brain(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.brain(next_states).max(1)[0]
        target_q_values = rewards + (gamma * next_q_values * dones)

        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def check_collision_ahead(self):
        head_x, head_y = self.snake_list[-1]
        next_x = head_x + self.x_change
        next_y = head_y + self.y_change
        for block in self.snake_list[:-1]:
            if block[0] == next_x and block[1] == next_y:
                return 1
        return 0

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

    def draw(self):
        for i, block in enumerate(self.snake_list):
            if i == len(self.snake_list) - 1:  # Head
                pygame.draw.rect(screen, self.color, [block[0], block[1], block_size, block_size])
                eye_radius = block_size // 5
                if self.x_change > 0:  # Moving right
                    pygame.draw.circle(screen, white, (block[0] + block_size - eye_radius, block[1] + eye_radius), eye_radius)
                    pygame.draw.circle(screen, white, (block[0] + block_size - eye_radius, block[1] + block_size - eye_radius), eye_radius)
                elif self.x_change < 0:  # Moving left
                    pygame.draw.circle(screen, white, (block[0] + eye_radius, block[1] + eye_radius), eye_radius)
                    pygame.draw.circle(screen, white, (block[0] + eye_radius, block[1] + block_size - eye_radius), eye_radius)
                elif self.y_change < 0:  # Moving up
                    pygame.draw.circle(screen, white, (block[0] + eye_radius, block[1] + eye_radius), eye_radius)
                    pygame.draw.circle(screen, white, (block[0] + block_size - eye_radius, block[1] + eye_radius), eye_radius)
                elif self.y_change > 0:  # Moving down
                    pygame.draw.circle(screen, white, (block[0] + eye_radius, block[1] + block_size - eye_radius), eye_radius)
                    pygame.draw.circle(screen, white, (block[0] + block_size - eye_radius, block[1] + block_size - eye_radius), eye_radius)
            else:
                pygame.draw.rect(screen, self.color, [block[0], block[1], block_size, block_size])

class Food:
    def __init__(self):
        self.reposition()

    def reposition(self):
        self.x = round(random.randrange(0, game_width - block_size) / block_size) * block_size
        self.y = round(random.randrange(0, game_height - block_size) / block_size) * block_size

    def draw(self):
        pygame.draw.rect(screen, red, [self.x, self.y, block_size, block_size])

def game_loop():
    clock = pygame.time.Clock()

    user_snake = Snake(green)
    ai_snake = Snake(blue, is_ai=True)
    food = Food()

    start_time = time.time()

    while time.time() - start_time < game_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and user_snake.x_change == 0:
                    user_snake.x_change = -block_size
                    user_snake.y_change = 0
                elif event.key == pygame.K_RIGHT and user_snake.x_change == 0:
                    user_snake.x_change = block_size
                    user_snake.y_change = 0
                elif event.key == pygame.K_UP and user_snake.y_change == 0:
                    user_snake.y_change = -block_size
                    user_snake.x_change = 0
                elif event.key == pygame.K_DOWN and user_snake.y_change == 0:
                    user_snake.y_change = block_size
                    user_snake.x_change = 0

        screen.fill(black)

        user_snake.update(food)
        ai_snake.update(food)

        if user_snake.is_collision():
            user_snake = Snake(green)
        if ai_snake.is_collision():
            ai_snake = Snake(blue, is_ai=True)
            ai_snake.score = 0  # Reset AI score when it collides

        if user_snake.eat_food(food):
            food.reposition()
        elif ai_snake.eat_food(food):
            food.reposition()

        user_snake.draw()
        ai_snake.draw()
        food.draw()

        # Display scores and time remaining
        font = pygame.font.Font(None, 36)
        user_score_text = font.render(f"User: {user_snake.score}", True, white)
        ai_score_text = font.render(f"AI: {ai_snake.score}", True, white)
        time_remaining = int(game_duration - (time.time() - start_time))
        time_text = font.render(f"Time: {time_remaining}s", True, white)
        screen.blit(user_score_text, (10, 10))
        screen.blit(ai_score_text, (game_width - 100, 10))
        screen.blit(time_text, (game_width // 2 - 50, 10))

        pygame.display.update()
        clock.tick(snake_speed)

    if ai_snake.score > user_snake.score:
        screen.fill(black)
        message("AI will replace you AHAHA - AbdullahAI", red)
        message("Play again? (Y/N)", white, 50)
        pygame.display.update()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        return True
                    elif event.key == pygame.K_n:
                        return False
    else:
        message("Game Over!", red)
        pygame.display.update()
        pygame.time.wait(2000)

    return False

# Add a try-except block to handle potential errors
try:
    play_again = True
    while play_again:
        play_again = game_loop()
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    pygame.quit()
    quit()
