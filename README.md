# Love Letter Board Game

A digital implementation of the popular "Love Letter" card game, built with Python and the Kivy framework. This project provides a fully playable game with a graphical user interface, CPU opponents, and support for both classic and expansion cards.


*(Image shows main menu, gameplay, and a card info popup)*

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Running the Game](#running-the-game)
- [How to Play](#how-to-play)
- [Building the Executable](#building-the-executable)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Classic Gameplay:** Full implementation of the original Love Letter rules for 2-4 players.
- **CPU Opponents:** Play against 1 to 3 simple AI opponents.
- **Graphical User Interface:** A clean and intuitive UI built with the Kivy framework.
- **Card Effect Animations:** Visual feedback for card plays, eliminations, and other effects.
- **Interactive Tutorial:** A guided walkthrough of the game's basic mechanics for new players.
- **Detailed Game Log:** Keep track of every move and event in the game.
- **Cross-Platform:** Thanks to Kivy and PyInstaller, the game can be built for Windows, macOS, and Linux.
- **Expansion Ready:** The logic includes cards from the "Kanai Factory Limited Edition" (for 5-8 players), although the current UI is limited to 4 players.

## Project Structure

The codebase is organized into logical components to separate game logic from the user interface.

```
/
├── assets/                 # All game images, fonts, etc.
│   ├── cards/              # Card images
│   └── ...
├── logic/                  # Core game logic (UI-independent)
│   ├── card_effects.py     # Functions for each card's effect
│   ├── constants.py        # Card data, game constants
│   ├── deck.py             # Deck creation and management
│   ├── game_round.py       # Manages a single game round
│   ├── player.py           # Player state class
│   └── ...
├── ui/                     # Kivy UI widgets and screens
│   ├── game_screen.py      # Main game screen widget (controller)
│   ├── screens.py          # Intro and Rules screens
│   ├── ui_components.py    # Reusable UI elements (buttons, popups)
│   └── ...
├── Dockerfile              # For creating a consistent build environment
├── requirements.txt        # Python package dependencies
├── run.py                  # Main entry point for the application
└── README.md               # This file
```

## Getting Started

Follow these instructions to run the game from the source code.

### Prerequisites

- Python 3.9+
- Kivy Framework and its dependencies.
- Docker (only required for building the executable, not for running from source).

### Running the Game

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/PetterPet/LoveLetterBoardGame.git
    cd LoveLetterBoardGame
    ```

2.  **Install the dependencies:**
    It's recommended to use a virtual environment.
    ```sh
    # Create and activate a virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install required packages
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```sh
    python run.py
    ```

## How to Play

1.  **Start:** Launch the game to see the main menu.
2.  **Tutorial:** If you're new, select "HƯỚNG DẪN" for a quick, interactive tutorial.
3.  **New Game:**
    - Click "BẮT ĐẦU CHƠI".
    - You will be prompted to select the number of players (2-4).
    - The game will set up the main UI and the first round will begin.
4.  **Gameplay:**
    - On your turn, you draw a card, leaving you with two cards in hand.
    - Click on one of the cards in your hand to play it.
    - If the card requires a target, a popup will appear for you to select another player.
    - Follow the card's instructions.
    - The round ends when all but one player are eliminated, or when the deck runs out.
    - The player with the highest card at the end of the round (if the deck runs out) wins the round.
5.  **Winning:** The first player to earn the required number of "Tokens of Affection" (red stars) wins the game!

## Building the Executable

To create a standalone, single-file executable, we use **PyInstaller** inside a **Docker** container. This ensures that the build environment is consistent and has all the necessary libraries, regardless of your host operating system.

### Prerequisites

- [Docker](https://www.docker.com/get-started) must be installed and running on your system.

### Build Steps

1.  **Build the Docker Image:**
    Navigate to the root directory of the project (where the `Dockerfile` is located) and run the following command. This creates a Docker image named `loveletter-builder-fin` containing Python, Kivy, and PyInstaller.

    ```sh
    docker build -t loveletter-builder-fin .
    ```

2.  **Run PyInstaller via Docker:**
    Execute the command below. This runs a temporary container from the image you just built, mounts your project directory into it, and then runs PyInstaller.

    ```sh
    docker run --rm -v "<path_to_local_dir>/LoveLetterBoardGame:/src" loveletter-builder-fin --name "LoveLetter" --onefile --add-data "assets:assets" run.py
    ```

    **Important:** Replace `<path_to_local_dir>` with the **absolute path** to the parent directory containing your `LoveLetterBoardGame` folder.
    - **Example on Windows:** `docker run --rm -v "C:/Users/YourUser/Documents/LoveLetterBoardGame:/src" ...`
    - **Example on macOS/Linux:** `docker run --rm -v "/home/youruser/projects/LoveLetterBoardGame:/src" ...`

    **Command Breakdown:**
    - `docker run --rm`: Runs a container and automatically removes it when it finishes.
    - `-v "<path...>/LoveLetterBoardGame:/src"`: Mounts your local project folder into the `/src` directory inside the container, so PyInstaller can access your files.
    - `loveletter-builder-fin`: The name of the Docker image to use.
    - `--name "LoveLetter"`: Sets the name of the output executable file.
    - `--onefile`: Bundles everything into a single executable file.
    - `--add-data "assets:assets"`: **Crucial step.** This tells PyInstaller to copy your entire `assets` folder into the final executable. The format is `SOURCE:DESTINATION`.
    - `run.py`: The entry point script for your application.

3.  **Find Your Executable:**
    Once the command finishes, you will find your standalone application inside a newly created `dist` folder in your project directory.
    - `LoveLetterBoardGame/dist/LoveLetter` (on macOS/Linux)
    - `LoveLetterBoardGame/dist/LoveLetter.exe` (on Windows)

You can now share this single file with others to play your game!