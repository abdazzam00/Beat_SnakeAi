// Initialize game variables
const game_width = 800;
const game_height = 600;
const block_size = 20;
const snake_speed = 15;
const game_duration = 300;  // Game duration in seconds (5 minutes)

// Colors
const BLACK = "#000000";
const WHITE = "#FFFFFF";
const RED = "#FF0000";
const GREEN = "#00FF00";
const BLUE = "#0000FF";

class Snake {
    constructor(color, is_ai = false) {
        this.snake_list = [[
            Math.floor(Math.random() * (game_width - block_size) / block_size) * block_size,
            Math.floor(Math.random() * (game_height - block_size) / block_size) * block_size
        ]];
        this.snake_length = 1;
        this.x = this.snake_list[0][0];
        this.y = this.snake_list[0][1];
        this.x_change = 0;
        this.y_change = 0;
        this.color = color;
        this.is_ai = is_ai;
        this.score = 0;
    }

    update(food) {
        if (this.is_ai) {
            // Implement AI logic here
            let [head_x, head_y] = this.snake_list[this.snake_list.length - 1];
            let food_x = food.x;
            let food_y = food.y;
            
            if (Math.random() < 0.7) {  // 70% chance of polarized movement
                if (Math.abs(head_x - food_x) > Math.abs(head_y - food_y)) {
                    if (head_x < food_x && this.x_change >= 0) {
                        [this.x_change, this.y_change] = [block_size, 0];
                    } else if (head_x > food_x && this.x_change <= 0) {
                        [this.x_change, this.y_change] = [-block_size, 0];
                    } else {
                        this.y_change = head_y < food_y ? block_size : -block_size;
                        this.x_change = 0;
                    }
                } else {
                    if (head_y < food_y && this.y_change >= 0) {
                        [this.x_change, this.y_change] = [0, block_size];
                    } else if (head_y > food_y && this.y_change <= 0) {
                        [this.x_change, this.y_change] = [0, -block_size];
                    } else {
                        this.x_change = head_x < food_x ? block_size : -block_size;
                        this.y_change = 0;
                    }
                }
            } else {  // 30% chance of random movement
                let possible_moves = [[block_size, 0], [-block_size, 0], [0, block_size], [0, -block_size]];
                [this.x_change, this.y_change] = possible_moves[Math.floor(Math.random() * possible_moves.length)];
            }
        }
        
        this.x += this.x_change;
        this.y += this.y_change;

        // Wrap around boundaries
        this.x = (this.x + game_width) % game_width;
        this.y = (this.y + game_height) % game_height;

        this.snake_list.push([this.x, this.y]);
        if (this.snake_list.length > this.snake_length) {
            this.snake_list.shift();
        }
    }

    is_collision() {
        let [head_x, head_y] = this.snake_list[this.snake_list.length - 1];
        return this.snake_list.slice(0, -1).some(block => block[0] === head_x && block[1] === head_y);
    }

    eat_food(food) {
        let [head_x, head_y] = this.snake_list[this.snake_list.length - 1];
        if (head_x === food.x && head_y === food.y) {
            this.snake_length += 1;
            this.score += 1;
            return true;
        }
        return false;
    }

    draw(ctx) {
        this.snake_list.forEach(([x, y]) => {
            ctx.fillStyle = this.color;
            ctx.fillRect(x, y, block_size, block_size);
        });
    }
}

class Food {
    constructor() {
        this.reposition();
    }

    reposition() {
        this.x = Math.round(Math.random() * (game_width - block_size) / block_size) * block_size;
        this.y = Math.round(Math.random() * (game_height - block_size) / block_size) * block_size;
    }

    draw(ctx) {
        ctx.fillStyle = RED;
        ctx.fillRect(this.x, this.y, block_size, block_size);
    }
}

let canvas, ctx, user_snake, ai_snake, food, game_state;

function init_game() {
    canvas = document.getElementById('gameCanvas');
    ctx = canvas.getContext('2d');
    user_snake = new Snake(GREEN);
    ai_snake = new Snake(BLUE, true);
    food = new Food();
    game_state = {
        start_time: Date.now() / 1000,
        is_game_over: false
    };
}

function game_loop() {
    if (!game_state.is_game_over) {
        update_game();
        draw_game();
        requestAnimationFrame(game_loop);
    } else {
        show_game_over();
    }
}

function update_game() {
    let current_time = Date.now() / 1000;
    if (current_time - game_state.start_time < game_duration) {
        user_snake.update(food);
        ai_snake.update(food);

        if (user_snake.is_collision()) {
            user_snake = new Snake(GREEN);
        }
        if (ai_snake.is_collision()) {
            ai_snake = new Snake(BLUE, true);
            ai_snake.score = 0;  // Reset AI score when it collides
        }

        if (user_snake.eat_food(food) || ai_snake.eat_food(food)) {
            food.reposition();
        }
    } else {
        game_state.is_game_over = true;
    }
}

function draw_game() {
    ctx.clearRect(0, 0, game_width, game_height);
    
    user_snake.draw(ctx);
    ai_snake.draw(ctx);
    food.draw(ctx);

    // Display scores and time remaining
    ctx.fillStyle = WHITE;
    ctx.font = '20px Arial';
    ctx.fillText(`User: ${user_snake.score}`, 10, 30);
    ctx.fillText(`AI: ${ai_snake.score}`, game_width - 70, 30);
    let time_remaining = Math.max(0, Math.floor(game_duration - (Date.now() / 1000 - game_state.start_time)));
    ctx.fillText(`Time: ${time_remaining}s`, game_width / 2 - 40, 30);
}

function show_game_over() {
    ctx.fillStyle = BLACK;
    ctx.fillRect(0, 0, game_width, game_height);
    ctx.fillStyle = WHITE;
    ctx.font = '30px Arial';
    ctx.textAlign = 'center';
    if (ai_snake.score > user_snake.score) {
        ctx.fillText("AI will replace you AHAHA - AbdullahAI", game_width / 2, game_height / 2);
    } else {
        ctx.fillText("Game Over!", game_width / 2, game_height / 2);
    }
    ctx.fillText(`Final Score - User: ${user_snake.score}, AI: ${ai_snake.score}`, game_width / 2, game_height / 2 + 40);
    ctx.fillText("Press Space to play again", game_width / 2, game_height / 2 + 80);
}

function handle_key_press(event) {
    if (game_state.is_game_over && event.code === 'Space') {
        init_game();
        game_loop();
    } else {
        if (event.key === 'ArrowLeft' && user_snake.x_change === 0) {
            user_snake.x_change = -block_size;
            user_snake.y_change = 0;
        } else if (event.key === 'ArrowRight' && user_snake.x_change === 0) {
            user_snake.x_change = block_size;
            user_snake.y_change = 0;
        } else if (event.key === 'ArrowUp' && user_snake.y_change === 0) {
            user_snake.y_change = -block_size;
            user_snake.x_change = 0;
        } else if (event.key === 'ArrowDown' && user_snake.y_change === 0) {
            user_snake.y_change = block_size;
            user_snake.x_change = 0;
        }
    }
}

document.addEventListener('keydown', handle_key_press);

window.onload = function() {
    init_game();
    game_loop();
};