
<div align="center">

# risiko-engine 

**A Stateless Russian Roulette Python Engine**

</div>

<div align="center">

[![PyPI version](https://badge.fury.io/py/risiko-engine.svg)](https://badge.fury.io/py/risiko-engine)
[![Python Version](https://img.shields.io/pypi/pyversions/risiko-engine.svg)](https://pypi.org/project/risiko-engine)
[![License](https://img.shields.io/pypi/l/risiko-engine.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Kodutzu/risiko-engine/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Kodutzu/risiko-engine/actions/workflows/python-ci.yml)

</div>

---

## 📖 Table of Contents

- [🚀 Installation](#-installation)
- [🎯 Quickstart](#-quickstart)
- [📜 License](#-license)

---

## 🚀 Installation

```bash
pip install risiko-engine
```

---

## 🎯 Quickstart

Here's a quick example of how to use `risiko-engine` to simulate a game of Russian Roulette:

```python
from risiko import RisikoState, processors
from risiko.core import PlayerBase, ShellBase

# Initialize the game state
state = RisikoState()

# Add a player to the game
state = processors.add_player_to_game(
    game_state=state, player=PlayerBase(id="player1", name="Player 1", charges=3)
)

# Load the magazine with shells
state = processors.load_magazine(
    game_state=state,
    round=[
        ShellBase(shell_type="live", damage=1),
        ShellBase(shell_type="blank", damage=0),
        ShellBase(shell_type="live", damage=1),
        ShellBase(shell_type="blank", damage=0),
    ],
)

# Shuffle the magazine
state = processors.shuffle_magazine(game_state=state)

# Load a shell into the shotgun
state = processors.shotgun_load_shell(game_state=state)

# Get the current player
current_player_id = state.turns.current_player_id
print(f"Current player: {current_player_id}")

# Fire the shell
fired_shell, state = processors.fire_shell(game_state=state, shooter_id=current_player_id)
print(f"Fired a {fired_shell.shell_type} shell!")

# Check the player's health
player = state.player.get_player(current_player_id)
print(f"{player.name} has {player.charges} charges remaining.")
```

`Note: Will be publishing it's documentation`

---


## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
