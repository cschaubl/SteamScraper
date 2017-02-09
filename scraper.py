import urllib2
import bs4
import json
import sys

class Game():
	def __init__(self):
		self.title = None
		self.url = None
		self.releaseDate = None
		self.price = None
		self.discountedPrice = None
		self.discount = None
		self.review = None
		self.platforms = None

	def __getitem__(self, key):
		return self.key

	def printData(self, stream):
		stream.write(self.title.encode("utf-8") + "\n")
		stream.write(self.url.encode("utf-8") + "\n")
		stream.write(self.releaseDate.encode("utf-8") + "\n")
		stream.write("Price: " + self.price.encode("utf-8") + "\n")
		if self.discount != None:
			stream.write("Discounted Price: " + self.discountedPrice.encode("utf-8") + "\n")
			stream.write("Discount: " + self.discount.encode("utf-8") + "\n")
		stream.write(self.review.encode("utf-8") + "\n")
		stream.write("Platforms:\n")
		for platform in self.platforms:
			stream.write(' ' + platform.encode("utf-8") + "\n")
		stream.write("\n")

def urlToSoup(url):
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urllib2.urlopen(req).read()
	soup = bs4.BeautifulSoup(html, "html5lib")
	return soup

def scrapeVals(page):
	global games
	game = Game()

	game.title = page.findAll("span", {"class" : "title"})[0].text
	game.url = page.get("href")
	game.releaseDate = page.findAll("div", {"class" : "search_released"})[0].text
	game.platforms = []
	platforms = page.findAll("p")[0].findAll("span")
	for platform in platforms:
		game.platforms.append(platform["class"][1])

	prices = page.findAll("div", {"class" : "search_price"})[0]
	if len(prices) == 1:
		game.price = prices.text[9:-7]
	if len(prices) == 4:
		game.price = "$" + prices.text.split("$")[1]
		game.discountedPrice = "$" + prices.text.split("$")[2]
		game.discount = page.findAll("div" , {"class" : "search_discount"})[0].text[9:-8]
	
	review = page.findAll("span", {"class" : "search_review_summary"})
	if len(review) == 0:
		game.review = "No reviews"
	else:
		review = str(review[0]).split('data-store-tooltip="')[1].split(">")[0].split("&lt;br&gt;")
		overall = review[0]
		percent = review[1].split(" of the ")[0]
		count = review[1].split(" of the ")[1].split(" user reviews ")[0]
		game.review = overall + ", " + percent + ", " + count

	games.append(game)
	#game.printData(sys.stdout)

def getPageGames(url):
	page = urlToSoup(url)
	searchResults = page.findAll("div", {"id" : "search_result_container"})[0]
	divs = searchResults.findAll("div")[1]
	pageGames = divs.findAll("a")
	for pageGame in pageGames:
		scrapeVals(pageGame)

games = []
outputFile = "games.txt"
baseUrl = "http://store.steampowered.com/search/?page="
baseSoup = urlToSoup(baseUrl)
pageCount = int(baseSoup.findAll("div", {"class" : "search_pagination_right"})[0].findAll("a")[2].text)

for i in range(pageCount):
	page = i + 1
	link = baseUrl + str(page)
	getPageGames(link)
	sys.stdout.write("Processed pages: %d / %d\r" % (page, pageCount))
	sys.stdout.flush()
print ""
file = open(outputFile, "wb")
print "Writing game data to " + outputFile
for game in games:
	game.printData(file)

file.close()
