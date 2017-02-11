import bs4
import datetime
import os
import pickle
import sqlite3
import sys
import time
import urllib2

def nonePrint(val):
	if val is None:
		return ""
	else:
		return val

def nullCheck(val):
	if val == "":
		return None
	else:
		return val

class Game():
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

	def toSQL(self, table):
		title = nullCheck(self.title)
		url = nullCheck(self.url)
		appID = int(nullCheck(self.appID))
		itemType = nullCheck(self.itemType)
		releaseDate = nullCheck(self.releaseDate)
		fullPrice = nullCheck(self.fullPrice)
		currentPrice = nullCheck(self.currentPrice)
		discount = nullCheck(self.discount)
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
		quality = self.review.split(", ")[0]
		if self.review == "No reviews":
			reviewPercent = None
			reviewCount = None
		else:
			reviewPercent = int(self.review.split(", ")[1].replace("%", ""))
			reviewCount = int(self.review.split(", ")[2].replace(",", ""))
		platforms = ""
		for platform in self.platforms:
			platforms += platform + ","
		platforms = platforms[:-1]
		platforms = nullCheck(platforms)
		table.execute("INSERT INTO games (title, url, appID, type, releaseDate, fullPrice, currentPrice, discount, quality, reviewCount, reviewPercent, platforms) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (title, url, appID, itemType, releaseDate, fullPrice, currentPrice, discount, quality, reviewCount, reviewPercent, platforms))

def urlToSoup(url):
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urllib2.urlopen(req).read()
	soup = bs4.BeautifulSoup(html, "html5lib")
	return soup

def scrapeVals(page):
	try:
		global games
		game = Game()

		game.title = page.findAll("span", {"class" : "title"})[0].text.strip()
		game.url = page.get("href").split("?")[0].strip()
		game.appID = game.url.split("/")[-2]
		game.itemType = game.url.split("/")[-3]
		game.releaseDate = page.findAll("div", {"class" : "search_released"})[0].text.strip()
		game.platforms = []
		platforms = page.findAll("p")[0].findAll("span")
		for platform in platforms:
			game.platforms.append(platform["class"][1].strip())
		prices = page.findAll("div", {"class" : "search_price"})[0]
		if len(page.findAll("div", {"class" : "discounted"})) == 0:
			game.fullPrice = prices.text.strip()
		else:
			game.fullPrice = prices.findAll("strike")[0].text.strip()
			game.discount = page.findAll("div" , {"class" : "search_discount"})[0].text.strip()
			game.currentPrice = prices.text.strip()[len(game.fullPrice):]

		review = page.findAll("span", {"class" : "search_review_summary"})
		if len(review) == 0:
			game.review = "No reviews"
		else:
			review = str(review[0]).split('data-store-tooltip="')[1].split(">")[0].split("&lt;br&gt;")
			overall = review[0].strip()
			percent = review[1].split(" of the ")[0].strip()
			count = review[1].split(" of the ")[1].split(" user reviews ")[0].strip().replace(",", "")
			game.review = overall + ", " + percent + ", " + count

		games.append(game)
		#game.printData(sys.stdout)
	except:
		global broken
		broken.append(page)
		print page.get("href")


def getPageGames(url):
	page = urlToSoup(url)
	searchResults = page.findAll("div", {"id" : "search_result_container"})[0]
	divs = searchResults.findAll("div")[1]
	pageGames = divs.findAll("a")
	for pageGame in pageGames:
		scrapeVals(pageGame)

games = []
broken = []
outputFile = "games.txt"
outputDatabase = "games.db"
baseUrl = "http://store.steampowered.com/search/?sort_by=Name_ASC&page="
baseSoup = urlToSoup(baseUrl)
pageCount = int(baseSoup.findAll("div", {"class" : "search_pagination_right"})[0].findAll("a")[2].text)

if os.path.exists(outputDatabase):
	print "File " + outputDatabase + " exists in directory, please delete before running"
	sys.exit(1)

start = datetime.datetime.now()
for i in range(pageCount):
	page = i + 1
	link = baseUrl + str(page)
	getPageGames(link)
	sys.stdout.write("Processed pages: %d / %d\r" % (page, pageCount))
	sys.stdout.flush()
print ""
end = datetime.datetime.now()
print "Data scraped in " + str((end - start).seconds) + " seconds"

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

file = open(outputFile, "wb")
print "Writing game data to " + outputFile
for game in games:
	game.printData(file)
	game.toSQL(table)
file.close()
conn.commit()
conn.close()
pickle.dump(games, open("data.txt", "wb"))
print "Bad Pages:"
for page in broken:
	print " " + page.get("href")
