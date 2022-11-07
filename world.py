import asyncio
import random
import sqlite3

#sends a private message to all players in the active game session.
async def messageAllGame(channel, client, message):
    for player in list(client.scores):
            await client.usernames[player].send(message)

#a function that helps sort lists of row objects for the highscore table.
def sortFunc(e):
    return float(e.score) / float(e.duration)

class GameWorld():
	def __init__(self, usernameArray):
		self.instanceVariable = random.choice("abcdefghijk")
		self.playersDict = {}
		self.dungeonLevel = 0
		print(f"this instance of GameWorld is brought to you by the letter {self.instanceVariable}")
		for playerName in usernameArray:
			self.playersDict[playerName] = Player(playerName)
		self.dungeonMonster = self.getDungeonMonster()
		self.dungeonMonster.clearDungeon()
		self.dungeonMonsterB = DungeonMonsterB(self.dungeonMonster)
		self.shop = Shop()
		print(f"gameworld has been initialised with dungeon level {str(self.dungeonLevel)} and dungeon monster {str(self.dungeonMonster)}")

	#queries the template database for a dungeon monster of an appropriate level and returns it as an object. 	
	def getDungeonMonster(self):
		if (self.dungeonLevel < 10):
			self.dungeonLevel += 1
		cursor = sqlite3.connect('dbTemplate.db').cursor()
		cursor.execute("SELECT name, attack, hp, vp FROM dungeon WHERE level = ?", str(self.dungeonLevel))
		choice = random.choice(cursor.fetchall())
		print(f"assigning a dungeon monster. I have chosen {str(choice)}")
		monsterObj = DungeonMonster(choice)
		return monsterObj

class Player():
	def __init__(self, name):
		self.actionCooldown = False
		self.playerName = name
		self.equipment = {}
		self.level = 1 #can be changed for esting purposes, but remember to change it back to the default of 1!
		self.levelThresholds = {1:1, 2:4, 3:10, 4:20, 5:9999}
		self.XP = 0
		self.VP = 0 #can be changed for esting purposes, but remember to change it back to the default of 0!
		self.gold = 0 #can be changed for esting purposes, but remember to change it back to the default of 0!
		self.maxHP = self.calculateMaxHP()
		self.currentHP = self.maxHP
		self.baseAttack = 0
		self.connectionPersistence = sqlite3.connect('dbPersistence.db')
		self.connectionTemplate = sqlite3.connect('dbTemplate.db')
		self.currentAttack = self.calculateAttack()
		self.currentMonster = self.getMonster()
		self.currentLocation = Location("village")
		self.currentlyActing = False
		print(f"player {self.playerName} has been created with db connections {str(self.connectionPersistence)} & {str(self.connectionTemplate)}")
		print(f"player {self.playerName} has been created with currentAttack {str(self.currentAttack)} monster {str(self.currentMonster)}")
		print(f"player {self.playerName} has been created with currentLocation {self.currentLocation.locationName}")

	#sets the action cooldown (to prevent a player beginning an action before another has completed).
	def setActionCooldown(self, boole):
		self.actionCooldown = boole
		return

	#updates the player's attack based on level and equipment.
	def calculateAttack(self):
		newAttack = self.baseAttack + self.level
		for item in self.equipment:
				print(f"calculateAttack is examing player's item: {self.equipment[item].itemName}")
				print(f"this item provides {getattr(self.equipment[item], 'atk', 0)} damage")
				newAttack += getattr(self.equipment[item], 'atk', 0)
		return newAttack

	#updates the player's current gold.
	def calculateGold(self, someGold):
		newGold = self.gold + someGold 
		return newGold

	#updates the player's maximum hit points based on level and equipment.
	def calculateMaxHP(self):
		newMaxHP = 8 + self.level * 2
		for item in self.equipment:
			print(f"calculateMaxHP is examing player's item: {self.equipment[item].itemName}")
			print(f"this item provides {getattr(self.equipment[item], 'maxhp', 0)} HP")
			newMaxHP += getattr(self.equipment[item], 'maxhp', 0)
		return newMaxHP

	#updates the player's experience point value. If past the threshold, the player levels up, and related attributes are recalculated in turn.
	async def calculateLevel(self, xp, message):
		self.XP += xp
		string = "You gained " + str(xp) + " experience points!"
		await message.channel.send(string)
		if (self.XP >= self.levelThresholds[self.level]):
			self.level += 1
			self.currentAttack = self.calculateAttack()
			self.maxHP = self.calculateMaxHP()
			self.currentHP = self.maxHP
			string = f"Congratulations, you are now level {str(self.level)}!\nYour attack is now {str(self.currentAttack)}.\nYour hit point maximum is now {str(self.maxHP)} and you have been healed to this value.\nYou need {str(self.levelThresholds[self.level] - self.XP)} experience points to reach the next level."
			await message.channel.send(string)
		else:
			string = f"You need {str(self.levelThresholds[self.level] - self.XP)} experience points to reach the next level."
			await message.channel.send(string)

	#updates the player's victory point value.
	async def calculateVP(self, vp, message):
		self.VP += vp
		string = "You gained " + str(vp) + " victory points!\n Your total is now :" + str(self.VP) + "."
		await message.channel.send(string)

	#returns a concise or verbose description of the object as a string, depending on the argument supplied.
	def getDescription(self, verboseBool):
		description = f"\n\n {self.playerName} is here."
		if (verboseBool):
			description += f"\n They have {str(self.currentHP)} hit points."
			if not self.equipment :
				string = f"\n They do not appear to be carrying any equipment."
			else:
				string = f"\n They are carrying the following equipment: "
				for item in self.equipment:
					string += f"{self.equipment[item].itemName}, "
				string = string[:len(string)-2]
				string += "."
			description += string
		return description
	
	#queries the template database for a monster of an appropriate level and returns it as an object. 	
	def getMonster(self):
		cursor = self.connectionTemplate.cursor()
		cursor.execute("SELECT name, attack, hp, xp, gold FROM forest WHERE level = ?", str(self.level))
		choice = random.choice(cursor.fetchall())
		print(f"assigning {self.playerName} a monster. I have chosen {str(choice)}")
		monsterObj =  Monster(choice)
		return monsterObj

	async def addItem(self, message, newItem):
		string = ""
		if newItem.type in self.equipment:
			oldItem = self.equipment[newItem.type]
			print(f"replacing {self.playerName}'s {oldItem.itemName} with {newItem.itemName} in the {newItem.type} slot")
			string = f"You remove the {oldItem.itemName} from your {newItem.type} and replace it with the {newItem.itemName}."
			self.equipment[newItem.type] = newItem
		else:
			print(f"placing {newItem.itemName} in {self.playerName}'s {newItem.type} slot")
			self.equipment[newItem.type] = newItem
		attackCheck = self.calculateAttack()
		maxHPCheck = self.calculateMaxHP()
		if attackCheck != self.currentAttack:
			improvement = attackCheck - self.currentAttack
			self.currentAttack = attackCheck
			string += f" Your attack changed by {str(improvement)} and is now {str(self.currentAttack)}."
		if maxHPCheck != self.maxHP:
			improvement = maxHPCheck - self.maxHP
			self.maxHP = maxHPCheck
			string += f" Your maximum hit points changed by {str(improvement)} and is now {str(self.maxHP)}."
			if self.currentHP > maxHPCheck:
				self.currentHP = maxHPCheck
				string += f" Accordingly, your current hit points were reduced to {str(self.currentHP)}."
		await message.channel.send(string)

	#does not complete until the player has finished acting. 
	async def isFinishedActing(self):
		while (self.currentlyActing):
			pass
		return

''' A DungeonMonster object is NOT assigned to a player, but to the game world. Any player that is assigned the dungeon location (that is, goes there) can interact with it, and the game handles parallel interactions via a system of transactions. This class operates in conjunction with DungeonMonsterB, which manages the representation of the object in the persistence database, while this class represents it in application memory.
'''
class DungeonMonster():
	def __init__(self, array):
		self.monsterName = array[0]
		self.attack = array[1]
		self.hp = array[2]
		self.vp = array[3]
		self.currentMonsterID = None

	#checks, drops and creates the dungeon table in the persistence database
	def clearDungeon(self):
		cursor = sqlite3.connect('dbPersistence.db').cursor()
		cursor.execute("DROP TABLE IF EXISTS dungeon")
		cursor.execute("CREATE TABLE dungeon (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, hp INTEGER NOT NULL, defeated_by TEXT DEFAULT NULL)")
		sqlite3.connect('dbPersistence.db').cursor()

	#returns a concise or verbose description of the object as a string, depending on the argument supplied.
	def getDescription(self, verboseBool):
		description = f"\n\n There is a {self.monsterName} here."
		if (verboseBool):
			description += f"\n It has {str(self.hp)} hit points and deals {str(self.attack)} damage."
			description += f"\n It is worth {str(self.vp)} victory points if slain."
		return description

	#sets the currentMonsterID to the provided integer value
	def setID(self, anID):
		self.currentMonsterID = anID

'''An item object carries attributes that can provide bonuses to the attributes of players for the purposes of game progression. They are read from the template database, operated upon via a shop object, and assigned to players at the end of a succesful purchase transaction in the shop location.
'''
class Item():
	def __init__(self, name):
		self.itemName = name
		cursor = sqlite3.connect('dbTemplate.db').cursor()
		array = cursor.execute("SELECT item_id, type, price FROM equipment WHERE name = ?", [self.itemName]).fetchall()[0]
		print(f"assigning a {self.itemName} some details. I have chosen {str(array)}")
		self.item_id = array[0]
		self.type = array[1]
		self.price = int(array[2])
		#load other attributes
		iterable = cursor.execute("SELECT attribute_name, attribute_value FROM equipment_attribute WHERE item_id = ?", [self.item_id]).fetchall()
		print(f"I have extracted an iterable for item {self.item_id} in equipment_attribute, it looks like {iterable}")
		for attribute in iterable:
			print(f"this attribute looks like {attribute}")
			setattr(self, attribute[0], attribute[1])
		print(f"Item object {self} has been built: {str(self)}")

	#overridden so that two items are considered equal if they have the same name. I'm not entirely sure this is sensible; could cause problems if used for anything except shop transaction evaluation.
	def __eq__(self, other):
		return self.itemName == other.itemName

	#returns a concise or verbose description of the object as a string, depending on the argument supplied.
	def getDescription(self, verboseBool):
		description = f"\n There is a {self.itemName} with a value of {str(self.price)} gold pieces."
		if (verboseBool):
			description += f"\n It provides {str(getattr(self, 'maxhp', 0))} hit points and {str(getattr(self, 'atk', 0))} attack damage."
		return description

''' An location object is assigned to a player to reflect their current environment, or 'room' in MUD parlance. Note that this composition is somewhat backwards; we would more naturally think of a location containing players than the other way around. But this implementation has the advantage of being a lot more straightforward.
'''
class Location():
	def __init__(self, name):
		self.locationName = name
		self.exits = []
		self.operations = []
		cursor = sqlite3.connect('dbTemplate.db').cursor()
		array = cursor.execute("SELECT location_id, description FROM location WHERE name = ?", [self.locationName]).fetchall()[0]
		print(f"assigning a {self.locationName} some details. I have chosen {str(array)}")
		self.location_id = array[0]
		self.description = array[1]
		#take a random addition description for flavour
		iterable = cursor.execute("SELECT description FROM location_description WHERE location_id = ?", [self.location_id]).fetchall()
		self.description += random.choice(iterable)[0]
		#load operations
		iterable = cursor.execute("SELECT operation, description FROM location_operation WHERE location_id = ?", [self.location_id]).fetchall()
		for operation in iterable:
			self.description += f"\n{operation[1]}"
			string = f"self.operations += [{operation[0]}Operation()]"
			print(f"Location() has built an fstring and it looks like {string}")
			print(f"adding {operation[0]}Operation to Location()")
			exec(string)
		#load exits		
		iterable = cursor.execute("SELECT direction, leads_to FROM location_exit WHERE location_id = ?", [self.location_id]).fetchall()
		for exit in iterable:
			self.description += f"\nTo the **#{exit[0].lower()}** is the path to the {exit[1]}."
			string = f"self.operations += [{exit[0]}Operation('{exit[1]}')]"
			print(f"Location() has built an fstring and it looks like {string}")
			print(f"adding {exit[0]}Operation to Location()")
			exec(string)
			self.exits += (exit[0],exit[1])
		print(f"location {self.locationName} initialised with the following operations: {str(self.operations)}")
		print(f"description is {self.description}")

	async def describe(self, message, client, aPlayerName):
		player = client.game.playersDict[aPlayerName]
		print(f"player {aPlayerName} has called describe()")
		monster = None
		wares = None
		for operation in self.operations:
			#print(f"this operation has str(type(operation)) == {str(type(operation))}")
			if str(type(operation)) == "<class 'world.AttackDOperation'>":
				monster = client.game.dungeonMonster
			if  str(type(operation)) == "<class 'world.AttackOperation'>":
				monster = player.currentMonster
			if str(type(operation)) == "<class 'world.BuyOperation'>":
				wares = client.game.shop.getWares()
				print(f"player {aPlayerName} is in the shop. describe() has received the following list of wares and is assigning it to {aPlayerName}: {wares}")
				#the state of the shop's wares on arrival are assigned to the player so they can be compared to the state at a time of purchase
				player.wares = wares
		if (monster):
			print(f"attempting to describe {aPlayerName}'s monster {player.currentMonster}")
			self.description += monster.getDescription(False)
		if (wares):
			self.description += f"\n\nThe chalkboard overhanging the counter lists {str(len(wares))} items for sale:"
			for x in range(0,len(wares)):
				print(f"x={x}, ware[x] = {wares[x]}, wares[x].getDescription(False) = {wares[x].getDescription(False)}")
				self.description += wares[x].getDescription(False)
		for otherPlayer in client.game.playersDict:
			otherPlayer = client.game.playersDict[otherPlayer]
			if (otherPlayer.currentLocation.locationName == player.currentLocation.locationName) and (otherPlayer != player):
				self.description += otherPlayer.getDescription(False)
		await client.usernames[aPlayerName].send(self.description)

''' A monster object is read from the template database and assigned to a player. Imaginatively, it inhabits the forest, and can only be interacted with when that location is assigned to the player as well.
'''
class Monster():
	def __init__(self, array):
		self.monsterName = array[0]
		self.attack = array[1]
		self.hp = array[2]
		self.xp = array[3]
		self.gold = array[4]

	#returns a concise or verbose description of the object as a string, depending on the argument supplied.
	def getDescription(self, verboseBool):
		description = f"\n\n There is a {self.monsterName} here."
		if (verboseBool):
			description += f"\n It has {str(self.hp)} hit points and deals {str(self.attack)} damage."
			description += f"\n It is worth {str(self.xp)} experience points and {str(self.gold)} gold pieces if slain."
		return description

''' A dungeon monster B object does not hold attributes in memory. It is a conduit by which players make transactions with the shop table in the persistence database and queries to relevant tables in the template database.
'''
class DungeonMonsterB():
	def __init__(self, aMonster):
		print(f"Initialising a DungeonMonsterB object with monster {aMonster.monsterName}")
		self.connectionPersistence = sqlite3.connect('dbPersistence.db')
		self.connectionTemplate = sqlite3.connect('dbTemplate.db')
		self.currentMonsterIDB = self.insertMonster(aMonster)
		aMonster.setID(self.currentMonsterIDB)

	#reads and returns the current state of the current boss
	def getLatest(self, cursor):
		cursor.execute("SELECT id, name, hp FROM dungeon WHERE id = (SELECT MAX(id) FROM dungeon)")
		return cursor 

	#reads and returns the current state of the boss with the given ID
	def getByID(self, cursor, anID):
		cursor.execute("SELECT id, name, hp, defeated_by FROM dungeon WHERE id = (?)", (anID,)) #I'm not sure why you have to add the comma after anID but you do
		return cursor 

	#retrieves a monster from the templateDB and write it to the persistence DB
	def insertMonster(self, monsterObj):
		cursor = self.connectionPersistence.cursor()
		print(f"attempting to insert a row into persistence.dungeon: monsterObj.monsterName = {monsterObj.monsterName}, monsterObj.hp = {monsterObj.hp}")
		cursor.execute("INSERT INTO dungeon(name, hp) VALUES(?,?)", (monsterObj.monsterName, monsterObj.hp))
		insertedID = cursor.lastrowid
		self.connectionPersistence.commit()
		return insertedID

	#creates a dict from supplied arguments. Makes a judgement about what updates regarding the monster to write to the persistence database based on dict's contents
	def submitResult(self, aPlayerName, damage, anID, aMonster):
		print(f"submitResult has been called by player: {aPlayerName}, damage: {str(damage)}, anID: {str(anID)}")
		result = ""
		cursor = self.connectionPersistence.cursor()
		monsterState = self.getByID(cursor, anID).fetchall()
		updatedHP = monsterState[0][2] - damage
		print(f"updatedHP has been calculated as {monsterState} - {damage} = {updatedHP}")
		if monsterState[0][3] : #if defeated_by is not None, the monster is already dead
			print(f"monster was already defeated by {monsterState}, rolling back")
			result = "rollback"
		else: 
			if updatedHP < 1:
				print(f"monster was defeated, attemping to write to DB")
				updateDict = {'hp':0, 'defeated_by':aPlayerName, 'id':anID}
				self.updateMonster(cursor, updateDict, aMonster)
				result = "victory"
			else:
				print(f"player was defeated, attemping to write to DB")
				updateDict = {'hp':updatedHP, 'id':anID}
				self.updateMonster(cursor, updateDict, aMonster)
				result = "defeat"
		print(f"leaving submitResult, returning result {result}")
		return result

	#update the provided values in the persistence database using the supplied dict (which contains the results of an individual combat)
	def updateMonster(self, cursor, aDict, aMonster):
		print(f"updateMonster called with dictionary {aDict}")
		if 'defeated_by' in aDict:
			cursor.execute("UPDATE dungeon SET hp = ?, defeated_by = ? WHERE id = ?", (aDict['hp'], aDict['defeated_by'], aDict['id']))
		else:
			cursor.execute("UPDATE dungeon SET hp = ? WHERE id = ?", (aDict['hp'], aDict['id']))
		aMonster.hp = aDict['hp']
		print(f"I made {cursor.rowcount} changes!")
		self.connectionPersistence.commit()
		return



'''A shop object does not hold attributes in memory. It is a conduit by which players make transactions with the shop table in the persistence database and queries to relevant tables in the template database.
'''
class Shop():
	def __init__(self):
		self.connectionPersistence = sqlite3.connect('dbPersistence.db')
		self.connectionTemplate = sqlite3.connect('dbTemplate.db')
		self.clearWares()
		wares = self.restockWares([None,None,None],"")
		self.insertWares(wares)

	#checks, drops and creates the shop table in the persistence database
	def clearWares(self):
		cursor = self.connectionPersistence.cursor()
		cursor.execute("DROP TABLE IF EXISTS shop")
		cursor.execute("CREATE TABLE shop (id INTEGER NOT NULL, name TEXT, PRIMARY KEY(id))")

	#reads and returns the current stock of the shop
	def getWares(self):
		array = []
		cursor = self.connectionPersistence.cursor()
		iterable = cursor.execute("SELECT name FROM shop").fetchall()
		for each in iterable:
			print(f"getWares thinks the name of this item is {each[0]}")
			item = Item(each[0])
			array.append(item)
		return array

	#attempt to insert the array values in the shop table in the persistence database
	def insertWares(self, array):
		cursor = self.connectionPersistence.cursor()
		for x in range(0,len(array)):
			print(f"insertWares() is attempting to insert the following values: {(x,array[x])}")
			cursor.execute("INSERT INTO shop(id, name) VALUES(?, ?)", (x,array[x]))
			self.connectionPersistence.commit()

	#for each provided empty value in the provided array, query the template database for items and assign one item at random to the empty value.
	def restockWares(self, array, toReplace):
		print(f"restockWares has been called with array: {array}")
		cursor = self.connectionTemplate.cursor()
		for x in range(0,len(array)):
			if not array[x]: #i.e. if array[x] = None
				cursor.execute("SELECT name FROM equipment")
				choices = cursor.fetchall()
				choice = random.choice(choices)[0]
				while (choice in array) or (choice==toReplace):#news item should not be duplicated or replace themselves with themselves
					choice = random.choice(choices)[0]
				print(f"assigning an item to wares array [{str(x)}]. I have chosen {str(choice)}")
				array[x] = choice
		print(f"restockWares is returning wares array: {str(array)}")
		return array

	#attempt to update the array values in the shop table in the persistence database (deprecated)
	'''
	def setWares(self, array, cursor):
		for x in range(0,len(array)):
			cursor.execute("UPDATE shop SET name = ? WHERE id = ?", (array[x], x))
	'''

	#attempt to update the array values in the shop table in the persistence database. return the rowcount attribute of the cursor to indicate the number of row updates made.
	def setWares2(self, oldarray, newarray, cursor):
		print(f"setWares2 called; oldarray = {oldarray}, newarray = {newarray}, cursor.rowcount= {cursor.rowcount}")
		for x in range(0,len(oldarray)):
			cursor.execute("UPDATE shop SET name = ? WHERE name = ?", (newarray[x],oldarray[x]))
		return cursor.rowcount

''' An operation object assigned to a player when in a location with a connection leading north. Assign the connected location to the player.
'''
class NorthOperation():
	def __init__(self, destination):
		self.operationName = "move"
		self.destination = destination

	def check(self, message):
		return message.startswith("#north")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		print(f"NorthOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"moving to {self.destination}")
		player.currentLocation =Location(self.destination)
		await player.currentLocation.describe(message, client, player.playerName)
		player.currentlyActing = False
		return

''' An operation object assigned to a player when in a location with a connection leading east. Assign the connected location to the player.
'''
class EastOperation():
	def __init__(self, destination):
		self.operationName = "move"
		self.destination = destination

	def check(self, message):
		return message.startswith("#east")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		print(f"EastOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"moving to {self.destination}")
		player.currentLocation =Location(self.destination)
		await player.currentLocation.describe(message, client, aPlayer)
		player.currentlyActing = False
		return

''' An operation object assigned to a player when in a location with a connection leading south. Assign the connected location to the player.
'''
class SouthOperation():
	def __init__(self, destination):
		self.operationName = "move"
		self.destination = destination

	def check(self, message):
		return message.startswith("#south")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		print(f"SouthOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"moving to {self.destination}")
		player.currentLocation =Location(self.destination)
		await player.currentLocation.describe(message, client, aPlayer)
		player.currentlyActing = False
		return

''' An operation object assigned to a player when in a location with a connection leading west. Assign the connected location to the player.
'''
class WestOperation():
	def __init__(self, destination):
		self.operationName = "move"
		self.destination = destination

	def check(self, message):
		return message.startswith("#west")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		print(f"WestOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"moving to {self.destination}")
		player.currentLocation =Location(self.destination)
		await player.currentLocation.describe(message, client, aPlayer)
		player.currentlyActing = False
		return

''' An operation object assigned to a player when in the forest location. Decrement the player's current hit point attribute, and the player's monster's hit point attribute, alternately and over time, until one reaches zero or below. If the monster reaches zero first, the player is assigned rewards and a calculation is made to see if they have levelled up. Then a new monster is assigned to the player.
'''
class AttackOperation():
	def __init__(self):
		self.operationName = "attack"

	def check(self, message):
		return message.startswith("#attack")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		monster = player.currentMonster
		print(f"AttackOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"Attacking the {monster.monsterName}!")
		await message.channel.send(f"Attacking the {monster.monsterName}!")
		await asyncio.sleep(1)
		while (player.currentHP > 0 and client.state == 'playing'):
			await self.playerAttacks(player, monster, message)
			if (monster.hp < 1):
				break
			await asyncio.sleep(1)
			await self.monsterAttacks(player, monster, message)
			await asyncio.sleep(1)
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			player.currentlyActing = False
			return
		if player.currentHP > 0:
			await self.postVictory(player, monster, message)
		else:
			await self.postDefeat(player, monster, message)
		player.currentlyActing = False
		return

	#subtracts the player's attack value from the monster's current HP
	async def playerAttacks(self, player, monster, message):
		monster.hp -= player.currentAttack
		string = monster.monsterName + " was hit for " + str(player.currentAttack) + " damage! (" + str(monster.hp) + " hit points remaining)"
		await message.channel.send(string)

	#subtracts the monsters's attack value from the player's current HP
	async def monsterAttacks(self, player, monster, message):
		player.currentHP -= monster.attack
		string = player.playerName + " was hit for " + str(monster.attack) + " damage! (" + str(player.currentHP) + " hit points remaining)"
		await message.channel.send(string)

	#updates player attributes and repopulates the forest with a new monster
	async def postVictory(self, player, monster, message):
		string = player.playerName + " was victorious!"
		await message.channel.send(string)
		player.gold = player.calculateGold(monster.gold)
		string = "You found " + str(monster.gold) + " gold on the monster and are now carrying " + str(player.gold) + " gold pieces."
		await message.channel.send(string)
		await player.calculateLevel(monster.xp, message)
		await message.channel.send("You hear a rustling in the bushes...")
		player.currentMonster = player.getMonster()
		string = "Suddenly, a wild " + player.currentMonster.monsterName + " appears!"
		await message.channel.send(string)

	async def postDefeat(self, player, monster, message):
		string = player.playerName + " can no longer fight; " + monster.monsterName + " was victorious!"
		await message.channel.send(string)

''' An operation object assigned to a player when in the dungeon location. Decrement the player's current hit point attribute, and the dungeon monster's hit point attribute, alternately and over time, until one reaches zero or below. If the monster reaches zero first, the player is assigned victory points. Then a new monster is assigned to the dungeon.
'''
class AttackDOperation():
	def __init__(self):
		self.operationName = "vanquish"

	def check(self, message):
		return message.startswith("#vanquish")

	async def run(self, message, content, aPlayer, client):		
		player = client.game.playersDict[aPlayer]
		monster = client.game.dungeonMonster
		currentID = monster.currentMonsterID
		print(f"AttackDOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		print(f"Attacking the {monster.monsterName}!")
		damage = 0
		monsterHP = monster.hp
		await message.channel.send(f"Attacking the {monster.monsterName}!")
		await asyncio.sleep(1)
		while (player.currentHP > 0 and client.state == 'playing'):
			monsterHP, damage = await self.playerAttacks(player, monster, damage, monsterHP, message)
			if (monsterHP < 1):
				break
			await asyncio.sleep(1)
			await self.monsterAttacks(player, monster, monsterHP, message)
			await asyncio.sleep(1)
		if not (client.state == 'playing'):
			string = f"{player.playerName}'s operation was interrupted because client.state = {str(client.state)}"
			print(string)
			player.currentlyActing = False
			return
		print(f"player {player.playerName} is attempting to register a result")	
		result = client.game.dungeonMonsterB.submitResult(player.playerName,damage,currentID,monster)
		if result == "rollback":
			await self.postUnexpectedDefeat(monster, message)
		elif player.currentHP > 0:
			await self.postVictory(client, player, monster, message)
		else:
			if result == "victory":
				await self.postUnexpectedVictory(client, player, monster, message)
			else:
				await self.postDefeat(player, monster, message)

		player.currentlyActing = False
		return

	#subtracts the player's attack value from the monster's current HP
	async def playerAttacks(self, player, monster, damage, monsterHP, message):
		monsterHP -= player.currentAttack
		damage += player.currentAttack
		string = f"{monster.monsterName} was hit for {str(player.currentAttack)} damage! ({str(monsterHP)} hit points remaining)"
		await message.channel.send(string)
		return monsterHP, damage

	#subtracts the monsters's attack value from the player's current HP
	async def monsterAttacks(self, player, monster, monsterHP, message):
		player.currentHP -= monster.attack
		string = f"{player.playerName} was hit for {str(monster.attack)} damage! ({str(player.currentHP)} hit points remaining)"
		await message.channel.send(string)

	#occurs in event of another player achieving victory during this player's successful but too slow attempt
	async def postUnexpectedDefeat(self, monster, message):
		string = f"The {monster.monsterName} falls, but it seems that the victory was stolen by a swifter player!"
		await message.channel.send(string)

	#updates player attributes and repopulates the dungeon with a new monster
	async def postVictory(self, client, player, monster, message):
		string = f"{player.playerName} was victorious!"
		await message.channel.send(string)
		await player.calculateVP(monster.vp, message)
		client.game.dungeonMonster =  client.game.getDungeonMonster()
		client.game.dungeonMonsterB = DungeonMonsterB(client.game.dungeonMonster)
		string = f"**With a mighty roar, a wild {client.game.dungeonMonster.monsterName} appears!**"
		await messageAllGame(message.channel, client, string)

	#occurs in the event of another player bringing the monster's HP below a threshold such that this player's unsuccessful attempt retroactively kills it
	#updates player attributes and repopulates the dungeon with a new monster	
	async def postUnexpectedVictory(self, client, player, monster, message):
		string = f"{player.playerName} can no longer fight; but at the last gasp, the {monster.monsterName} crashes to the ground, granting them the victory!"
		await message.channel.send(string)
		await player.calculateVP(monster.vp, message)
		client.game.dungeonMonster = client.game.getDungeonMonster()
		client.game.dungeonMonsterB = DungeonMonsterB(client.game.dungeonMonster)
		string = f"**With a mighty roar, a wild {client.game.dungeonMonster.monsterName} appears!**"
		await messageAllGame(message.channel, client, string)

	async def postDefeat(self, player, monster, message):
		string = f"{player.playerName} can no longer fight; {monster.monsterName} was victorious!"
		await message.channel.send(string)

'''An operation object assigned to a player when in the village location. Queries the highscores table in the persistence database and returns a description of it for the player'''
class ExamineOperation():
	def __init__(self):
		self.operationName = "examine"

	def check(self, message):
		return message.startswith("#examine")

	async def run(self, message, content, aPlayer, client):	
		player = client.game.playersDict[aPlayer]
		print(f"ExamineOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		self.table = HighScoreTable()
		print(f"sum(row.score for row in self.table.rows) = {sum(row.score for row in self.table.rows)}")
		if sum(row.score for row in self.table.rows) == -10: #each null record is assigned a score of -1, so an empty table will sum to -10
			await message.channel.send("It seems no records have as yet been inscribed on the monument. What better opportunity to earn yourself immortal fame?")
		else:
			await message.channel.send("Approaching the monument, you can see the following feats have been engraved on its marble facade:")
			for row in self.table.rows:
				if row.score > 0:
					await message.channel.send(f"#{row.position}: **{row.name}** scored **{row.score}** points in a game that lasted {row.duration} seconds.")
			await message.channel.send("Newly inspired, you are ready to resume your own legend.")
		player.currentlyActing = False
		return


''' An operation object assigned to a player when in the healer's guild location. Increments the player's current hit point attribute over time, until it reaches the maximum hit point attribute.
'''
class HealOperation():
	def __init__(self):
		self.operationName = "heal"

	def check(self, message):
		return message.startswith("#heal")

	async def run(self, message, content, aPlayer, client):	
		player = client.game.playersDict[aPlayer]
		print(f"HealOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		if (player.currentHP < player.maxHP):
			while (player.currentHP < player.maxHP and client.state == 'playing'):
				if (player.maxHP - player.currentHP == 1):
					player.currentHP += 1
					string = f"You were healed for 1 hit point, and now have {str(player.currentHP)} out of {str(player.maxHP)}."
					await message.channel.send(string)
					await asyncio.sleep(1)
				else:
					player.currentHP += 2
					string = f"You were healed for 2 hit points, and now have {str(player.currentHP)} out of {str(player.maxHP)}."
					await message.channel.send(string)
					await asyncio.sleep(1)
		else:
			await message.channel.send("You are already at maximum HP!")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			player.currentlyActing = False
			return
		await message.channel.send("You are ready to return to battle.")
		player.currentlyActing = False
		return

''' An operation object assigned to a player when in the shop location. Attempts to perform a transaction adding the item to the player's inventory, removing it from sale and replacing it with a new item.
'''
class BuyOperation():
	def __init__(self):
		self.operationName = "buy"

	def check(self, message):
		return message.startswith("#buy")

	def parseTarget(self, message, name):
		return message.endswith(name)

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		shop = client.game.shop
		print(f"BuyOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		validItem = None

		#check that the player has correctly specified a purchasable item. If false, abort the transaction.
		for item in player.wares:
			if self.parseTarget(message.content, item.itemName):
				await message.channel.send(f"You are attempting to purchase the {item.itemName}.")
				validItem = item
		if not validItem:
			await message.channel.send(f"That is not for sale. Type #buy followed by the name of the item you wish to purchase (for example, **#buy {player.wares[0].itemName}**).")

		else:
			cursor = player.connectionPersistence.cursor()
			print(f"{player.playerName} has begun the attempted purchase of {validItem.itemName}")
			shopState = shop.getWares()

			#business logic checks to determine whether the item's presence in the shop has changed in the database before attempting a write (to prevent a lost update)
			if not validItem in shopState:
				print(f"The item is no longer in shopState.") #meaning that someone else has bought it
				await message.channel.send(f'\n The shopkeeper clears his throat with an air of embarrassment. "I\'m sorry, but it seems we have already sold that item to another customer. Allow me to update the board."')
				player.currentLocation = Location("shop")
				await player.currentLocation.describe(message, client, aPlayer)

			#check that the player has enough money to make the purchase. If not, abort the transaction.
			elif player.gold < validItem.price:
				await message.channel.send(f'\n The shopkeeper clears his throat with an air of embarrassment. "I\'m sorry, but it seems that you cannot afford that item."')

			#a valid item that the player can afford has been requested, so proceed with the purchase
			else: 
				print(f"The state of the shop is currently the same as on {player}'s arrival.")
				cursor.execute("BEGIN TRANSACTION")
				import traceback #in case of an exception, this will be used to print details to the console

				#somewhat convoluted, but the effect is to rebuild a new shop inventory by combining the old one with a new item fetched from the template database
				try:
					oldWares = player.wares
					passList = []
					for x in range(0,len(oldWares)):
						passList.append(player.wares[x].itemName)
						if oldWares[x] == validItem:
							oldWares[x] = None
						else:
							oldWares[x] = oldWares[x].itemName
					print(f"calling restockWares with oldWares = {oldWares}")
					newWares = shop.restockWares(oldWares,validItem.itemName)
					print(f"calling setWares2 with newWares = {newWares}")
					changesMade = shop.setWares2(passList,newWares, cursor)
					print(f"setWares2 called; changesMade = {changesMade}")

					#if the item has been removed from the shop inventory, it is time to add it to the player inventory and update their gold balance
					if changesMade > 0:
						cursor.execute("COMMIT")
						print("the transaction was successful")
						player.gold -= validItem.price
						await message.channel.send(f'\n You pay for the item, leaving you with {str(player.gold)} gold pieces. The merchant thanks you, takes a duster from the counter and sets about updating the chalkboard.')
						await player.addItem(message, validItem)
						player.currentLocation = Location("shop")
						await player.currentLocation.describe(message, client, aPlayer)

					#if the new inventory was not accepted then something has gone wrong, and the user should be informed.
					else:
						raise ValueException("The shop inventory was not modified!")
				except Exception:
					traceback.print_exc()
					cursor.execute("ROLLBACK")
					await message.channel.send(f'\n The merchant scratches his head. "Something odd just happened. I\'m afraid I can\'t settle your purchase."')
					player.currentLocation = Location("shop")
					await player.currentLocation.describe(message, client, aPlayer)

		player.currentlyActing = False
		return

''' An operation object assigned to a player in any location. Provides a description of the players' attributes and those of any other monster or player present.
'''
class StatusOperation():
	def __init__(self):
		self.operationName = "status"

	def check(self, message):
		return message.startswith("#status")

	async def run(self, message, content, aPlayer, client):
		player = client.game.playersDict[aPlayer]
		print(f"StatusOperation.run has been called by {player.playerName}")
		if not (client.state == 'playing'):
			print(f"{player.playerName}'s operation was rejected because client.state = {client.state}")
			return
		if (player.currentlyActing):
			await message.channel.send("You must wait for your current action to end first!")
			return
		player.currentlyActing = True
		string = ""
		string += f"{player.playerName}, you are currently level {str(player.level)}. You need {str(player.levelThresholds[player.level]-player.XP)} experience points to reach the next level."
		string += f"\n You have {str(player.VP)} victory points and are carrying {str(player.gold)} gold pieces."
		string += f"\n You are carrying the following equipment: "
		for item in player.equipment:
			string += f"{player.equipment[item].itemName}, "
		string = string[:len(string)-2]
		string += "."
		string += f"\n You have {str(player.currentHP)}/{str(player.maxHP)} hit points and your attack is currently {str(player.currentAttack)}."

		#check if the player is in a location with a monster. If true, provide a description of it.
		monster = None
		for operation in player.currentLocation.operations:
			if str(type(operation)) == "<class 'world.AttackDOperation'>":
				monster = client.game.dungeonMonster
			if  str(type(operation)) == "<class 'world.AttackOperation'>":
				monster = player.currentMonster
		if monster:
			print(f"Since monster = {monster}, I will describe it")
			string += monster.getDescription(True)

		#check if the player is in a location with items for sale. If true, provide descriptions of them.
		wares = None
		for operation in player.currentLocation.operations:
			if str(type(operation)) == "<class 'world.BuyOperation'>":
					wares = client.game.shop.getWares()
		if wares:
			string += f"\n\nThe chalkboard overhanging the counter lists {str(len(wares))} items for sale:"
			print(f"Since wares = {wares}, I will describe them:")
			for item in wares:
				string += item.getDescription(True)

		#check for other players in this location. Describe any found.
		for otherPlayer in client.game.playersDict:
			otherPlayer = client.game.playersDict[otherPlayer]
			if (otherPlayer.currentLocation.locationName == player.currentLocation.locationName) and (otherPlayer != player):
				string += otherPlayer.getDescription(True)

		await message.channel.send(string)
		player.currentlyActing = False
		return

'''A class that is responsible for reading from and writing to the highscores table in the persistence database. Enables an element of persistent state in the application by saving the highest scores obtained by users, ranking them by a function of the score and game duration.'''
class HighScoreTable():
    def __init__(self):
        print('initiating a HighScoreTable')
        self.connection = sqlite3.connect('dbPersistence.db')
        self.cursor = self.connection.cursor()
        self.rawTable = self.readTable()
        self.rows = []
        for thing in self.rawTable:
            row = HighScoreTableRow(thing)
            self.rows += [row]

    #requests the records from the highscores table in the persistence database
    def readTable(self):
        raw = self.cursor.execute("SELECT * FROM highscores").fetchall()
        print('here is what I extracted from the highscore table in the persistence DB:')
        for thing in raw:
            print(thing)
        return raw

    #a factory function that populates the HighScoreTable object with HighScoreTableRows.
    def insertRow(self, aName, aScore, aDuration):
        print(f"insertRow has been called with values {aName}, {aScore}, {aDuration}")
        row = HighScoreTableRow((0,aName,aScore,aDuration))
        self.rows += [row]

    #re-orders the table in the rows list in reverse order. 
    def sortRows(self):
        self.rows.sort(key=sortFunc, reverse=True)
        for x in range(0, len(self.rows)):
            self.rows[x].position = x+1
        #trim the table to 10 places
        self.rows = self.rows[0:10]

    #converts rows back to a data format that can be written back to the database.
    def rowsToRawTable(self):
        newRawTable = []
        for row in self.rows:
            print(f"checking score of row: {row.position}")
            if row.score > 0:
                newRawTable.append((row.position,row.name,row.score,row.duration))
            else:
                newRawTable.append((row.position,None,None,None))
        print("rowsToRawTable has created a table to potentially be written:")
        for thing in newRawTable:
            print(thing)
        return newRawTable

    #disassembles an ordered list of rows and writes each to the persistence database.
    def submitNewTable(self, table):
        for row in table:
            self.cursor.execute("UPDATE highscores SET name = ?, score = ?, duration = ? WHERE position = ?", (row[1], row[2], row[3], row[0]))
        self.connection.commit()

'''A class that organises and stores each row returned from the highscores table in the persistence database. Modifies raw values to prevent divide by zero errors and other undesired output.'''
class HighScoreTableRow():
    def __init__(self, aRow):
        self.position = aRow[0]
        self.name = aRow[1]
        if aRow[2] == None:
            self.score = -1
        else:
            self.score = aRow[2]
        if aRow[3] == None:
            self.duration = 1
        else: 
            self.duration = aRow[3]

    def __str__(self):
        return [self.position, self.name, self.score, self.duration]