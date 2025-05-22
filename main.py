import os
import re
import random
import textwrap
import requests
import json
import configparser
import logging


class Player:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.score = 0

    def pos(self):
        return (self.x, self.y)

    def set_pos(self, pos):
        self.x = pos[0]
        self.y = pos[1]


class GameLogic:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.players = [Player(0, 0), Player(board_size - 1, board_size - 1)]
        self.food = (
            random.randint(1, board_size - 2),
            random.randint(1, board_size - 2),
        )
        self.current_player = 0

    def spawn_food(self):
        player_positions = [p.pos() for p in self.players]
        empty_cells = [
            (x, y)
            for y in range(self.board_size)
            for x in range(self.board_size)
            if (x, y) not in player_positions
        ]
        self.food = random.choice(empty_cells)

    def get_valid_moves(self):
        player = self.players[self.current_player]
        other_player_positions = [p.pos() for p in self.players if p != player]
        x, y = player.pos()
        possible_moves = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.board_size and 0 <= new_y < self.board_size:
                    if (new_x, new_y) not in other_player_positions:
                        possible_moves.append((new_x, new_y))
        return possible_moves

    def move_player(self, new_pos):
        player = self.players[self.current_player]
        player.set_pos(new_pos)
        if new_pos == self.food:
            player.score += 1
            self.spawn_food()

    def get_score(self):
        return [p.score for p in self.players]

    def next_turn(self):
        self.current_player = 0 if self.current_player == 1 else 1

    def check_pos(self, x, y):
        for i, p in enumerate(self.players):
            if (x, y) == p.pos():
                return str(i)
        if (x, y) == self.food:
            return "f"
        return " "

    def get_board_str(self):
        lines = []
        lines.append("")
        lines.append("   " + " ".join(str(i) for i in range(self.board_size)))
        lines.append("  +" + "-" * (self.board_size * 2 - 1) + "+")
        for y in range(self.board_size):
            row = f"{y}|"
            for x in range(self.board_size):
                row += f" {self.check_pos(x, y)}"
            row += "|"
            lines.append(row)
        lines.append("  +" + "-" * (self.board_size * 2 - 1) + "+\n")
        return "\n".join(lines)


class GameUI:
    def __init__(self, game):
        self.game = game

    def draw_new_move_screen(self):
        os.system("cls" if os.name == "nt" else "clear")
        print("------ Food Grab ------")
        print(f"Score: {self.game.get_score()}")
        print(f"Current Turn: Player {self.game.current_player}")
        print(self.game.get_board_str())

    def draw_game_over_screen(self):
        score  = self.game.get_score()
        winner = score.index(max(score))
        os.system("cls" if os.name == "nt" else "clear")
        print("------ Food Grab ------")
        print(f"Final Score: {score}")
        print(f"Winner: Player {winner}")
        print("------ Game Over ------")


class LLMInputHandler:
    def __init__(self, model, base_url, api_key):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def _build_prompt(self, game):
        px,py = game.players[game.current_player].pos()
        fx,fy  = game.food
        moves = " ".join(f"[{x},{y}]" for x,y in game.get_valid_moves())

        prompt = textwrap.dedent(f"""
            Your coordinates: [{px},{py}]
            Food coordinates: [{fx},{fy}]
            Your valid moves are: {moves}
            Make a move towards food. 
            Respond ONLY with the new coordinates as a Python list, e.g.: [2,3]
            Do NOT include any extra text or explanation.
        """).strip()

        logging.info(f"[LLM Player {game.current_player}] Prompt:\n{prompt}")
        return prompt

    def _parse_response(self, content):
        try:
            last_match = re.findall(r"\b(\d+)\s*,\s*(\d+)\b", content)[-1]
            return int(last_match[0]), int(last_match[1])
        except Exception:
            pass
        return None

    def get_move(self, game):
        prompt = self._build_prompt(game)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI playing a grid game. Only respond with a single move in the form [x,y]. /no_think",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 1.2,
            "min_p": 0.0,
            "top_p": 0.95,
            "top_k": 20,
            "max_tokens": 10,
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            logging.info(f"[LLM Player {game.current_player}] Response: {content}\n")
            move = self._parse_response(content)
            if move in game.get_valid_moves():
                return move
            else:
                raise ValueError(f"Invalid move from LLM: {move}")
        except Exception as e:
            print(f"LLM error: {e}")
            logging.exception(f"LLM error: {e}\n")
            return game.players[game.current_player].pos()  # stand still fallback


class SillyBotInputHandler:
    def get_move(self, game):
        return random.choice(game.get_valid_moves())


class SmartBotInputHandler:
    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        best_move = min(
            valid_moves,
            key=lambda m: (m[0] - game.food[0])**2 + (m[1] - game.food[1])**2
        )
        return best_move


def build_input_handlers(config):
    handlers = []
    for i in range(2):
        section = f"player{i}"
        model = config.get(section, "model", fallback="smart_bot")
        if model == "smart_bot":
            handlers.append(SmartBotInputHandler())
        elif model == "silly_bot":
            handlers.append(SillyBotInputHandler())
        else:
            base_url = config.get(section, "base_url")
            api_key = config.get(section, "api_key", fallback="DUMMY_KEY")
            handlers.append(LLMInputHandler(model, base_url, api_key))
        logging.info(f"Configured {section}: {model}")
    return handlers


def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    rounds = config.getint("global", "rounds", fallback=100)
    logfile = config.get("global", "logfile", fallback="game.log")

    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    game = GameLogic()
    ui = GameUI(game)
    input_handlers = build_input_handlers(config)

    while sum(game.get_score()) < rounds:
        ui.draw_new_move_screen()
        handler = input_handlers[game.current_player]
        new_pos = handler.get_move(game)
        game.move_player(new_pos)
        game.next_turn()
    ui.draw_game_over_screen()
    logging.info(f"Final Score: {game.get_score()}")


if __name__ == "__main__":
    main()
