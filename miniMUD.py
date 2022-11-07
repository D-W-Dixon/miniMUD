import asyncio
import discord
import session
import world

class MyClient(discord.Client):
    def __init__(self):
        discord.Client.__init__(self)
        self.DURATION = 360 #constant, measured in seconds, change this to change duration of a game
        self.state = "startup"
        self.scores = {}
        self.mainchannel = None

        self.operations = []
        self.operations += [session.SessionOperation()]
        self.operations += [session.JoinOperation()]
        self.operations += [session.GameOperation()]  
        self.operations += [session.ExitOperation()]
        self.operations += [session.ResetOperation()]
        self.operations += [session.ConfirmOperation()]
        print(self.operations)
        
    async def on_ready(self):
        print(f'Logged on as {self.user} to {self.guilds[0]}.')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        
        if message.author == client.user: 
            return #this prevents the bot from responding to its own messages

        if (self.state == "playing"):
            try:
                if (message.channel.name == self.mainchannel.name):
                    await message.channel.send("A game is currently in progress, please don't use this channel.")
                else:
                    return #this prevents the bot from interrupting conversations
            except:
                #exceptions occur when the message originates from a private channel
                player = message.author.name
                if (client.game.playersDict[player].actionCooldown):
                    await message.channel.send("You are already engaged in an action. You must wait for it to resolve before you can begin another.")
                else:
                    if not message.content.startswith("#"):
                        return #the '#' key is always used to get the attention of the bot
                    for operation in self.game.playersDict[player].currentLocation.operations:
                        if (operation.check(message.content)): #checks if message starts with any keyword
                            print(f"Attempting to call {operation.operationName}")
                            await operation.run(message, message.content, player, self) #runs the operation associated with any keyword found

        elif (self.state == "scoring"):
            return

        elif (self.state == "confirming"):
            print(f"since state=={self.state}, I am taking an interest in message {message.content}")
            if not message.author.permissions_in(message.channel).administrator:
                return #only users with administrator permissions can provide confirmation

            for operation in self.operations:
                if(operation.check(message.content)): 
                    await operation.run(message, message.content, self) 
        else:
            if not message.content.startswith("#"):
                return
            
            for operation in self.operations:
                if(operation.check(message.content)): 
                    await operation.run(message, message.content, self) 

    async def awaitActionCooldown(self, time, player):
        self.game.playersDict[player].setActionCooldown(True)
        await asyncio.sleep(time)
        self.game.playersDict[player].setActionCooldown(False)
        return
  

client = MyClient()
client.run('INSERT KEY HERE')
