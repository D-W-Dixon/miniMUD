# miniMUD
This discord bot will allow users to join and play a game which condenses aspects of classic MUD gameplay into short, competitive, multiplayer sessions. It is adapted from work done by GitHub user joapoerfig and available at https://github.com/joaoperfig/discordBoggle.

## Setup
1. Follow the initial setup of creating a bot and adding it to your server here.
2. Clone this repository.
3. Install dependencies with pip. pip install discord, pip install pillow
4. Open miniMUD.py and scroll down to the last line where it says to add your token.
5. Open a shell and run the bot with python boggle.py.

## How To Play
1. Type #session on a channel to start a game session. (Players can only join newly created sessions)
2. Each player types #join to join the session.
3. Type #start to start a game.

At this point, the bot will DM each registered player with a description of the starting area. All commands available to the player in each location are indicated by the bot. Each command is preceded by the # character. 

The goal of the game is to amass power by defeating monsters in the forest, which awards gold and experience points. Once strong enough they can challenge the dungeon monsters, who award the victory points by which the game is won. Experience points allow the player to level up, while gold can be spent on items in the shop. Weapons offer extra damage while shields and armour increase maximum hit points. When a player's hit points are depleted, they must visit the healer to replenish them before continuing combat. While you can see other players in the world, you cannot attack them.

Care must be taken as only the player who deals the finishing blow to the dungeon monster receives victory points. The strategy in the game is therefore management of resources, including the limited time available, to end the game with as many victory points as possible. To change the duration of a game, open the miniMUD.py file and change the value of the constant self.DURATION on line 9.

The game has not been especially carefully balanced. Attribute values for the equipment and monsters can be found in the dbTemplate.db file. You can change these as you see fit using a DBMS such as DB Browser for SQLite (https://sqlitebrowser.org/). If you want to change players' starting attributes, you can find these under the Player class in world.py.


## Other info

All licencing information follows as per the original project.
