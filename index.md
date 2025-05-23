
## 🤖 Console Game For LLMs

Because it’s Friday. And because games are fun... I built a console game for my LLMs to play against each other in a kind of turn-based strategy challenge. It’s a bit goofy but at the same time quite instructive (though not in a way I hoped it would be).

The LLMs I've tried so far are being consistently beaten by a pretty simple bot. I ran a tournament between some of my favorite local models and two bots (see results below), and LLMs performed "average" at best. 

I would love to hear your thoughts and get your help from this community because, frankly, I’m winging this and could use some smarter minds.


## 🎮 The Game: "Food Grab"

Game repo: [https://github.com/facha/llm-food-grab-game.git](https://github.com/facha/llm-food-grab-game.git)

**Premise:**
A 10x10 grid. Two players. One piece of food. First to reach the food gets the point. The game goes on until a set number of rounds.

![game fragment](https://raw.githubusercontent.com/facha/llm-food-grab-game/refs/heads/main/demo.gif)

Each turn, the model is prompted with the current board state and must reply with new coordinates of the next move.
It’s simple, and I've been expecting the models to do quite well. But as it turned out, a basic bot consistently beats LLMs.

### Players:

* **LLMs** (either local or remote via chat/completions API. I tested with Ollama, Llama.cpp and some models on OpenRouter)
* **Smart Bot**: Always moves directly towards food.
* **Silly Bot**: Just wanders around. Moves randomly.

I assumed LLMs would outperform the Smart Bot. It's easy if you position yourself well for the next upcomming round during rounds where the opponent is closer to the food cell. 

But no LLM nailed that part. And they were also struggling to do the same what the Smart Bot is doing (getting closer to the food with each move no matter what). 

To end on a high note, LLMs did well against Silly Bot. Yay?


## 🧪 The Tournament

Each player played 200 games (100 as first player, 100 as second player) against every other participant.

### 📊 Score Matrix (Player vs Opponent)

| Player                     | smart_bot             | phi4                | qwen3                | gemma3               | mistral-small3.1     | silly_bot            |
|----------------------------|----------------------|----------------------|----------------------|----------------------|----------------------|----------------------|
| smart_bot                  |100                   |122                   |116                   |129                   |129                   |197                   |
| phi4                       |78                    |100                   |99                    |108                   |121                   |191                   |
| qwen3                      |84                    |101                   |100                   |101                   |114                   |192                   |
| gemma3                     |71                    |92                    |99                    |100                   |101                   |189                   |
| mistral-small3.1           |71                    |79                    |86                    |99                    |100                   |186                   |
| silly_bot                  |3                     |9                     |8                     |11                    |14                    |100                   |

### 🏆 Rankings by TrueSkill Algorithm

| Rank | Player                                  | μ      | σ      | Exposed Score (μ-3σ) |
|------|-----------------------------------------|--------|--------|----------------------|
| 1    | smart_bot                               |  39.21 |   4.65 |                25.25 |
| 2    | phi4:14b-q8_0                           |  28.31 |   3.31 |                18.37 |
| 3    | gemma3:27b-it-q8_0                      |  24.53 |   2.75 |                16.30 |
| 4    | qwen3:32b-q8_0                          |  27.12 |   3.71 |                16.01 |
| 5    | mistral-small3.1:24b-instruct-2503-q8_0 |  20.67 |   2.97 |                11.74 |
| 6    | silly_bot                               |  11.41 |   5.37 |                -4.70 |

### 🏆 Rankings by Total Wins

| Rank | Player                                  | Total Wins  |
|------|-----------------------------------------|-------------|
| 1    | smart_bot                               | 793         |
| 2    | phi4:14b-q8_0                           | 697         |
| 3    | qwen3:32b-q8_0                          | 692         |
| 4    | gemma3:27b-it-q8_0                      | 652         |
| 5    | mistral-small3.1:24b-instruct-2503-q8_0 | 621         |
| 6    | silly_bot                               | 145         |

### 🤖 About that Smart Bot…

As you probably have noticed `smart_bot` is an absolute winner. I've tried things but no model was capable to consistently outplay him. In fact, it used to be called just `bot`. I've renamed him to `smart_bot` to honor the fact it's been consistently beating those multi-gigabyte-sized monsters trained during months on huge GPU cluster. 

Three models (gemma3:27b-it-q8_0, phi4:14b-q8_0, qwen3:32b-q8_0) showed similar results and mistral-small3.1:24b-instruct-2503-q8_0 performed somewhat poorer. phi4:14b-q8_0 has positively surprized since this is a smaller size model + at least in the past it's been accused here and there of including benchmarking data in its training sets, which could make it appear better on popular benchmark rankings than it actually is.


## 🧠 Observations & Questions

### Prompting

Here is the prompt (a sample) that the script is currently using:

```
Your coordinates: [2,1]
Food coordinates: [0,1]
Your valid moves are: [1,0] [1,1] [1,2] [2,0] [2,1] [2,2] [3,0] [3,1] [3,2]
Make a move towards food. 
Respond ONLY with the new coordinates as a Python list, e.g.: [2,3]
Do NOT include any extra text or explanation.
```
It is very direct and consice. And it worked the best. What I actually don't like about it is that it tells the model what to do instead of leaving up to the model to figure it out.

I've tried other options. E.g. here is a more general prompt that explains the game rules and provides game state, but leaves the desicions up to the model.

```
You are an AI player in a turn-based grid game. The board is 10x10.
There are two players: 0 and 1. You are Player 1. Your goal is to move to the food cell (f) to score points. 

The valid moves are to adjacent squares (including diagonals) that are inside the board and not occupied by the other player.
On your turn you can move one cell in 8 directions: up, down, left, right, up-right, up-left, down-right, down-left (as coordinates).

Once one of the players reaches the food cell, he scores a point. Then the game continues: food respawns at a new random cell.
The players have to reach the food cell again from their current coordinates.

Here is the current game state:
   0 1 2 3 4 5 6 7 8 9
  +-------------------+
0|   0                |
1|                    |
2|                    |
3|                    |
4|                    |
5|                    |
6|                 f  |
7|                    |
8|                    |
9|                   1|
  +-------------------+
Current Score: [0, 0]
Player 0 coordinates: 1,0
Player 1 coordinates: 9,9
Food coordinates: 8,6

Your valid moves are: 8,8 8,9 9,8 9,9

Respond ONLY with the new coordinates as a Python list, e.g.: [2, 3]
Do NOT include any extra text or explanation.
```

Another prompt I've treid. I've asked an LLM online how can I improve my previous prompt. And this is what I've got in response. But it didn't improve the results.

```
Game Board (10x10):

   0 1 2 3 4 5 6 7 8 9
  +-------------------+
0|   0                |
1|                    |
2|                    |
3|                    |
4|                    |
5|                    |
6|                 f  |
7|                    |
8|                    |
9|                   1|
  +-------------------+
Current Score: [0, 0]
Player 0 coordinates: 1,0
Player 1 coordinates: 9,9
Food coordinates: 8,6


Valid Moves for Player 1: 8,8 8,9 9,8 9,9

Instructions:
- You are Player 1, playing on a turn-based grid.
- You can move 1 cell in any of the 8 directions.
- Avoid moving to the other player's position.
- Score by reaching the food (f), which will then respawn.
- Reply ONLY with the coordinates of your move as a Python list. Example: [3, 4]
- DO NOT include any explanation or text.
```
In case you have any suggestions, please let me know.


---

### Model Parameters

Here’s what the script is currently using:

```json
{
  "temperature": 1.2,
  "top_p": 0.95,
  "top_k": 20,
  "min_p": 0.0,
  "max_tokens": 10,
  "model": "whatever",
  "messages": [
    { "role": "system", "content": "You are an AI playing a grid game. Only respond with a single move in the form [x,y]. /no_think" },
    { "role": "user", "content": prompt }
  ]
}
```

* I had to set temperature higher to avoid repetitions (with lower temperatures the model would often keep moving back and forth between two cells with no actual progress).
* I've taken the values for `min_p`, `top_p`, `top_k` from Qwen3 recommendations.
* `max_tokens` (and `/no_think` in system prompt) is obviously to make the LLM output shorter.

Again, if you think there are some changes worth making to these parameters or there are others to try, please let me know.


[🔗 GitHub: llm-food-grab-game](https://github.com/facha/llm-food-grab-game.git)


