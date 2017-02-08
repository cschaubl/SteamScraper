import urllib2
import bs4
import json
import time

def urlToSoup(url):
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urllib2.urlopen(req).read()
	soup = bs4.BeautifulSoup(html, "html5lib")
	return soup


def scrapeVals(game):
	title = game.findAll("span", {"class" : "title"})[0].text
	releaseDate = game.findAll("div", {"class" : "search_released"})[0].text
	platforms = game.findAll("p")[0].findAll("span")
	plats = ["win", "mac", "linux", "razerosvr", "htcvive", "oculusrift", "hmd_separator", "streamingvideo"]

	prices = game.findAll("div", {"class" : "search_price"})[0]
	if len(prices) == 1:
		price = prices.text[9:-7]
		discountedPrice = price
	if len(prices) == 4:
		price = "$" + prices.text.split("$")[1]
		discountedPrice = "$" + prices.text.split("$")[2]

	discount = game.findAll("div" , {"class" : "search_discount"})[0]
	if len(discount) == 3:
		discount = discount.text[9:-8]
	if len(discount) == 1:
		discount = "-0%"

	review = game.findAll("span", {"class" : "search_review_summary"})
	if len(review) == 0:
		review = "No reviews"
	else:
		review = str(review[0]).split('data-store-tooltip="')[1].split(">")[0].split("&lt;br&gt;")
		overall = review[0]
		percent = review[1].split(" of the ")[0]
		count = review[1].split(" of the ")[1].split(" user reviews ")[0]
		review = overall + ", " + percent + ", " + count + " reviews"

	print title
	print releaseDate
	print "Price: " + price
	if price != discountedPrice:
		print "Discounted Price: " + discountedPrice
		print "Discount: " + discount
	print review
	print "Platforms:"
	for platform in platforms:
		print ' ' + platform["class"][1]
	print ""

	global output
	output.write(title.encode("utf-8") + "\n")
	output.write(releaseDate.encode("utf-8") + "\n")
	output.write("Price: " + price.encode("utf-8") + "\n")
	if price != discountedPrice:
		output.write("Discounted Price: " + discountedPrice.encode("utf-8") + "\n")
		output.write("Discount: " + discount.encode("utf-8") + "\n")
	output.write(review.encode("utf-8") + "\n")
	output.write("Platforms:\n")
	for platform in platforms:
		output.write(' ' + platform["class"][1].encode("utf-8") + "\n")
	output.write("\n")


def getPageGames(url):
	global games
	page = urlToSoup(url)
	searchResults = page.findAll("div", {"id" : "search_result_container"})[0]
	divs = searchResults.findAll("div")[1]
	pageGames = divs.findAll("a")
	for game in pageGames:
		scrapeVals(game)
		games.append(game)

games = []
baseUrl = "http://store.steampowered.com/search/?page="
baseSoup = urlToSoup(baseUrl)
pageCount = int(baseSoup.findAll("div", {"class" : "search_pagination_right"})[0].findAll("a")[2].text)

output = open("games.txt", "wb")
for i in range(1, pageCount + 1):
	link = baseUrl + str(i)
	getPageGames(link)
output.close()

file = open("data.txt", "wb")
for game in games:
	file.write(game.prettify().encode("utf-8") + "\n")
file.close()