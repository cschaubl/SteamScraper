import urllib2
import bs4
import json
import thread

games = []
pageCount = 1080
basePage = "http://store.steampowered.com/search/?page="

def urlToSoup(url):
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urllib2.urlopen(req).read()
	soup = bs4.BeautifulSoup(html, "html5lib")
	return soup

def getPageGames(url):
	print url
	global games
	page = urlToSoup(url)
	searchResults = page.findAll("div", {"id" : "search_result_container"})[0]
	divs = searchResults.findAll("div")[1]
	pageGames = divs.findAll("a")
	for game in pageGames:
		games.append(game)

for i in range(1, pageCount + 1):
	link = basePage + str(i)
	getPageGames(link)

file = open("data.txt", "wb")
for game in games:
	file.write(game.prettify().encode("utf-8") + "\n")
file.close()