import asyncio
import discord
import time
import world
import sqlite3

#retrieves the current high score table from the persistence database. Sorts the scores from this session into a copy of it, and then if the copy is different, writes it back as the new high score table.
async def highscoreCheck(channel, client):
    print('highscoreCheck called')
    table = world.HighScoreTable() #reads in the existing table from the persistence database
    for player in list(client.scores):
        table.insertRow(player, client.game.playersDict[player].VP, client.DURATION)
    table.sortRows() 
    newTable = table.rowsToRawTable() 
    if table.rawTable != newTable: #if changes have been made, write the new table back
        table.submitNewTable(newTable)
        await channel.send("The high score table was updated!")
        for player in list(client.scores):
            wasAdded = False
            for row in table.rows:
                if row.duration == client.DURATION and row.score == client.game.playersDict[player].VP and player == row.name:
                    wasAdded = True
            if wasAdded:
                await channel.send(f"{player}'s score of {client.game.playersDict[player].VP} has been inscribed upon the village's monument of heroes!")
    else:
        await channel.send("No changes were made to the highscore table.")

#sends a private message to all players in the active game session.
async def messageall(channel, client, time, message):
    await asyncio.sleep(time) # wait for supplied duration
    await channel.send(message)
    for player in list(client.scores):
            await client.usernames[player].send(message)

async def postgame(channel, client, wait):
    await asyncio.sleep(wait) # wait for supplied duration
    client.state = "scoring"
    await channel.send("**Time's up!**")
    for player in list(client.scores):
            await client.usernames[player].send("**Time's up!** Return to the main channel for the final scores.")
    await asyncio.sleep(6)
    await channel.send("Waiting for all player actions to finish...")      
    for player in list(client.scores):
        try:
            await client.game.playersDict[player].isFinishedActing()
            string = client.game.playersDict[player].playerName + " has finished acting."
            await channel.send(string)
        except:
            print("An error occurred while waiting for players to finish acting.")        
    await channel.send("All actions finished!")
    await asyncio.sleep(1)
    await channel.send("This round's scores were:")
    await asyncio.sleep(1)
    string = ""
    for player in list(client.scores):
        string += f"player {player} scored: {str(client.game.playersDict[player].VP)}\n"
    await channel.send(string)
    await asyncio.sleep(1)
    await channel.send("Checking if a new high score has been set...")
    await highscoreCheck(channel, client)
    await asyncio.sleep(1)
    await channel.send("The running total of this session's scores is:")
    await asyncio.sleep(1)
    for player in list(client.scores):
        client.scores[player] += client.game.playersDict[player].VP
    string = ""
    for player in list(client.scores):
        string += f"** {player} **: ** {str(client.scores[player])} ** points\n"
    await channel.send(string)
    await asyncio.sleep(1)
    await channel.send("Type #start to play another game!")
    client.state = "idle"
        
    
class ExitOperation():
    def check(self, message):
        return message.startswith("#exit") 
    
    async def run(self, message, content , client):
        exit()  
         
class SessionOperation():   
    def check(self, message):
        return message.startswith("#session")
    
    async def run(self, message, content, client):
        #a slightly hacky way of prevent a session from being created in a private channel
        if getattr(message.channel, 'name', 0) == 0:
           await message.channel.send("You can't create a session in a private channel!")
        else:
            client.scores = {}
            client.usernames = {}
            client.state = "register"
            client.mainchannel = message.channel
            await message.channel.send("A new session has been created. Type **#join** to participate. When everyone is ready, type **#start** to begin.")   
        
class JoinOperation():  
    def check(self, message):
        return message.startswith("#join")
    
    async def run(self, message, content, client):
        if not (client.state == "register"):
            await message.channel.send("There is no active session to join. Please type #session.")
            return
        if getattr(message.channel, 'name', 0) == 0:
            await message.channel.send("You can't join a session from a private channel!")
            return
        if (client.mainchannel.name != message.channel.name):
            await message.channel.send("A new game must be joined from the channel where the session was made.")
            return   
        client.scores[message.author.name] = 0
        client.usernames[message.author.name] = message.author
        await message.channel.send(f"Thank you for joining, {message.author.name}.")
        
class GameOperation():
    def check(self, message):
        return message.startswith("#start")
    
    async def run(self, message, content, client):
        if (client.state == "startup"):
            await message.channel.send("A new session must be created before a game can start. Please use #session.")
            return
        if (len(list(client.scores)) == 0):
            await message.channel.send("A game cannot begin if no players have joined the session. Please type #join.")
            return      
        if (client.mainchannel.name != message.channel.name):
            await message.channel.send("A new game must be started from the channel where the session was made.")
            return               
        client.state = "playing"
        client.gamestart = time.time()
        client.game = world.GameWorld(client.usernames)
        await message.channel.send(f"**Beginning the game!**\nPlay in the private message channel where the bot messages you.\nYou have {client.DURATION} seconds.")
        for player in list(client.scores):
            await client.usernames[player].send(f"Thank you for joining this game. You have {client.DURATION} seconds!")
            await client.game.playersDict[player].currentLocation.describe(message, client, player)
        await messageall(message.channel, client, client.DURATION*0.25, f"**{int(client.DURATION*0.75)} seconds remaining!**")    
        await messageall(message.channel, client, client.DURATION*0.25, f"**{int(client.DURATION*0.5)} seconds remaining!**")    
        await messageall(message.channel, client, client.DURATION*0.25, f"**{int(client.DURATION*0.25)} seconds remaining!**")     
        await postgame(message.channel, client, client.DURATION*0.25)

class ResetOperation():
    def check(self, message):
        return message.startswith("#hiscorereset")

    async def run(self, message, content, client):
        if client.state == "busy":
            await message.channel.send("This command cannot be used right now. Try again later.")
            return
        if not message.author.permissions_in(message.channel).administrator:
            await message.channel.send("This command can only be used by a user with administrator permissions.")
            return
        client.state = "confirming"
        await message.channel.send("Are you sure you wish to reset the highscore table for this server? (Answer yes or no in the next 10 seconds)")
        await asyncio.sleep(10)
        print(f"the ten seconds are up and client.state = {client.state}")
        if client.state == "confirming":
            await message.channel.send("Time is up; highscores will not be reset. Use #hiscorereset if you wish to try again.")
        client.state = "idle"
        print(f"leaving ResetOperation with client.state = {client.state}")

class ConfirmOperation():
    def check(self, message):
        return message in ["y","yes","Yes","Y","n","N","No","no"]

    async def run(self, message, content, client):
        print(f"ConfirmOperation has been called. Client state is {client.state}. Message is {content}")
        if content in ["y","yes","Yes","Y"]:
            client.state = "busy"
            await message.channel.send("Confirmed. Resetting highscores...")
            connection = sqlite3.connect('dbPersistence.db')
            cursor = connection.cursor()
            cursor.execute("DROP TABLE IF EXISTS highscores")
            cursor.execute('CREATE TABLE "highscores" ("position" INTEGER UNIQUE, "name"  TEXT, "score" INTEGER, "duration"  INTEGER, PRIMARY KEY("position"));')
            for x in range (1,11):
                print(x)
                cursor.execute("INSERT INTO highscores VALUES(?,?,?,?)",(x,None,None,None))
            connection.commit()
            await message.channel.send("Highscores have been reset.")
            client.state = "idle"
        else:
            client.state = "idle"
            await message.channel.send("Highscores will not be reset.")




    
