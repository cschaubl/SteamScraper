import bs4
import datetime
import os
import pickle
import sqlite3
import sys
import urllib2

def retry(limit):
	def retryWrapper(func):
		def functionWrapper(*args, **kwargs):
			attempts = 0
			while attempts < limit:
				try:
					rtnVal = func(*args, **kwargs)
					return rtnVal
				except:
					attempts += 1
			print "Too many failed attempts"
			sys.exit(0)
		return functionWrapper
	return retryWrapper

#print nothing if value is None
def nonePrint(val):
	if val is None:
		return ""
	else:
		return val

#set value to none if is empty string
def nullCheck(val):
	if val == "":
		return None
	else:
		return val

class Game():
	#initialize member variables to None
	def __init__(self):
		self.title = None
		self.url = None
		self.appID = None
		self.itemType = None
		self.releaseDate = None
		self.fullPrice = None
		self.currentPrice = None
		self.discount = None
		self.review = None
		self.platforms = None

	#print values to supplied output stream
	#platforms are printed on seperate lines
	def printData(self, stream):
		stream.write("Title: " + nonePrint(self.title).encode("utf-8") + "\n")
		stream.write("Url: " + nonePrint(self.url).encode("utf-8") + "\n")
		stream.write("AppID: " + nonePrint(self.appID).encode("utf-8") + "\n")
		stream.write("Type: " + nonePrint(self.itemType).encode("utf-8") + "\n")
		stream.write("ReleaseDate: " + nonePrint(self.releaseDate).encode("utf-8") + "\n")
		stream.write("Full Price: " + nonePrint(self.fullPrice).encode("utf-8") + "\n")
		stream.write("Current Price: " + nonePrint(self.currentPrice).encode("utf-8") + "\n")
		stream.write("Discount: " + nonePrint(self.discount).encode("utf-8") + "\n")
		stream.write("Review: " + nonePrint(self.review).encode("utf-8") + "\n")
		stream.write("Platforms:\n")
		for platform in self.platforms:
			stream.write(' ' + nonePrint(platform.encode)("utf-8") + "\n")
		stream.write("\n")

	#insert data into sqlite table
	def toSQL(self, table):
		title = nullCheck(self.title)
		url = nullCheck(self.url)
		appID = int(nullCheck(self.appID))
		itemType = nullCheck(self.itemType)
		releaseDate = nullCheck(self.releaseDate)
		fullPrice = nullCheck(self.fullPrice)
		currentPrice = nullCheck(self.currentPrice)
		discount = nullCheck(self.discount)
		#if no discount, discount is set to 0%,
		#discounted price is set equal to current price
		if fullPrice is not None:
			if currentPrice is None:
				currentPrice = fullPrice
				discount = 0
			else:
				discount = int(discount.replace("%", ""))
		"""
		month = int(time.strptime(self.releaseDate.split(" ")[0], "%b").tm_mon)
		day = int(self.releaseDate.split(" ")[1].replace(",", ""))
		year = int(self.releaseDate.split(" ")[2])
		releaseDate = str("%04d-%02d-%02d" % (year, month, day))
		"""
		#parse review parameters from review string
		quality = self.review.split(", ")[0]
		if self.review == "No reviews":
			reviewPercent = None
			reviewCount = None
		else:
			reviewPercent = int(self.review.split(", ")[1].replace("%", ""))
			reviewCount = int(self.review.split(", ")[2].replace(",", ""))
		#platforms are concatenated into comma separated string
		platforms = ""
		for platform in self.platforms:
			platforms += platform + ","
		platforms = platforms[:-1]
		platforms = nullCheck(platforms)
		#insert values into table
		table.execute("INSERT INTO games (title, url, appID, type, releaseDate, fullPrice, currentPrice, discount, quality, reviewCount, reviewPercent, platforms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (title, url, appID, itemType, releaseDate, fullPrice, currentPrice, discount, quality, reviewCount, reviewPercent, platforms))

#create soup from url
@retry(5)
def urlToSoup(url):
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urllib2.urlopen(req).read()
	soup = bs4.BeautifulSoup(html, "html5lib")
	return soup

#get game values from page entry
def scrapeVals(page):
	#page causes an error save the url in broken and continue
	game = Game()
	#scrape data from page
	game.title = page.findAll("span", {"class" : "title"})[0].text.strip()
	game.url = page.get("href").split("?")[0].strip()
	game.appID = game.url.split("/")[-2]
	game.itemType = game.url.split("/")[-3]
	game.releaseDate = page.findAll("div", {"class" : "search_released"})[0].text.strip()
	#store platforms in list
	game.platforms = []
	platforms = page.findAll("p")[0].findAll("span")
	for platform in platforms:
		game.platforms.append(platform["class"][1].strip())
	#get all price text as string
	prices = page.findAll("div", {"class" : "search_price"})[0]
	#check if game has a discount
	if len(page.findAll("div", {"class" : "discounted"})) == 0:
		#if no discount full price is only result
		game.fullPrice = prices.text.strip()
	else:
		#if discount parse values from price entry
		game.fullPrice = prices.findAll("strike")[0].text.strip()
		game.discount = page.findAll("div" , {"class" : "search_discount"})[0].text.strip()
		game.currentPrice = prices.text.strip()[len(game.fullPrice):]
	#get review string from page
	review = page.findAll("span", {"class" : "search_review_summary"})
	if len(review) == 0:
		#if no review store "No reviews"
		game.review = "No reviews"
	else:
		#if review parse data from review string
		review = str(review[0]).split('data-store-tooltip="')[1].split(">")[0].split("&lt;br&gt;")
		overall = review[0].strip()
		percent = review[1].split(" of the ")[0].strip()
		count = review[1].split(" of the ")[1].split(" user reviews ")[0].strip().replace(",", "")
		#concatenate parameters into comma separated string 
		game.review = overall + ", " + percent + ", " + count

	#store game object into list
	global games
	games.append(game)

#get game entries from a search result page
def getPageGames(url):
	page = urlToSoup(url)
	searchResults = page.findAll("div", {"id" : "search_result_container"})[0]
	divs = searchResults.findAll("div")[1]
	pageGames = divs.findAll("a")
	for pageGame in pageGames:
		scrapeVals(pageGame)

#global lists
games = []
broken = []
#output files
outputFile = "games.txt"
outputDatabase = "games.db"
outputDump = "games.dmp"
#url to build links off of
baseUrl = "http://store.steampowered.com/search/?sort_by=Name_ASC&page="
baseSoup = urlToSoup(baseUrl)
#get number of pages to itterate over from base page
pageCount = int(baseSoup.findAll("div", {"class" : "search_pagination_right"})[0].findAll("a")[2].text)
#check if database file already exists in directory, if true exit
if os.path.exists(outputDatabase):
	print "File " + outputDatabase + " exists in directory, please remove it before running"
	sys.exit(1)

start = datetime.datetime.now()
#begin itterating over all pages
for i in range(pageCount):
	#create url by appending page number
	page = i + 1
	link = baseUrl + str(page)
	#scrape and store data
	getPageGames(link)
	#print progress bar each iteration
	sys.stdout.write("Processed pages: %d / %d\r" % (page, pageCount))
	sys.stdout.flush()
print ""
end = datetime.datetime.now()
#print number of seconds elapsed
print "Data scraped in " + str((end - start).seconds) + " seconds"
#create database
conn = sqlite3.connect(outputDatabase)
table = conn.cursor()
table.execute('create table games \
	(id integer primary key, \
	title text, \
	url text, \
	appID intger, \
	type text, \
	releaseDate text, \
	fullPrice real, \
	currentPrice real, \
	discount integer, \
	quality text, \
	reviewCount integer, \
	reviewPercent integer, \
	platforms text)')
#create plain text file
file = open(outputFile, "wb")
#write data to text file/database
print "Writing text data to " + outputFile + " file"
for game in games:
	game.printData(file)
print "Writing sql data to " + outputDatabase + " databse"
for game in games:
	game.toSQL(table)
#close files
file.close()
conn.commit()
conn.close()
#dump game to serialized file
print "Writing raw data to " + outputDump + " file"
pickle.dump(games, open(outputDump, "wb"))
#if errors print urls that caused error
if len(broken) > 0:
	print "Bad Pages:"
	for page in broken:
		print " " + page.get("href")
