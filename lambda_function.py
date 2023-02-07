
import requests
# from botocore.vendored import requests
from bs4 import BeautifulSoup
import json

#lambda function
def lambda_handler(event, context):
  queryParams = event["queryStringParameters"]  
  #   print(queryParams)

  if 'eventId' in queryParams and 'clubId' in queryParams:
    url = "https://system.gotsport.com/org_event/events/{}/schedules?club={}".format(queryParams['eventId'],queryParams['clubId'])
  else:
    print("'eventId' or 'clubId' are missing in query params. Needs to be like this '?eventId=18280/&clubId=3694'", queryParams)      
    url = "https://system.gotsport.com/org_event/events/18280/schedules?club=3694"    
    print("Using default URL", url)
  
  response = getHtml(url)

  if( response["success"] == False ):
      return {
        'statusCode': 200,
        'data': response
  }


  games = parseHtml(response["data"])
  return games
  # return {
  #       'statusCode': 200,
  #       'data':games
  # }


def getHtml(url):
  try:
    print("Calling url:", url)
    webpage = requests.get(url)
    print(webpage)
    
    if webpage.status_code == 200:
      webpage_bs = BeautifulSoup(webpage.text, 'html.parser')
      # webpage_bs = BeautifulSoup(webpage.content, 'html.parser')
      # print("Success")
      # print(webpage_bs.prettify())
      print("Success getting HTML")
      return {"success": True, "data": webpage_bs }
    else:
      # print(webpage.status_code+" "+url)
      return {"success": False, "data": webpage.status_code+" "+url }
  except Exception as e:
    # print("requests does not work : "+url)
    return {"success": False, "data": e }

    

# <div class='hidden-xs'>
# <h4 class='text-muted'>Sunday, September 18, 2022</h4>
# <div class='table-responsive'>
# <table class='table table-bordered table-condensed table-hover'>
# <thead>
def parseHtml(html):
  games = []
  # <h4 class='text-center'>Wednesday, November 09, 2022</h4>
  datesTags = html.find_all("h4", {"class": "text-center"})
  dates = [d.text for d in datesTags]
  # print("PARSING RESPONSE: Dates found:", len(dates), dates)

  # <table class='table table-bordered table-condensed table-hover'>
  gamesGroupedByDate = html.find_all("table", {"class": "table table-bordered table-condensed table-hover"})
  
  print("PARSING RESPONSE: gamesGroupedByDate items", len(gamesGroupedByDate))
  #loop over dates, the index of date matches the index of gamesGroupedByDate
  for index, gamesInADate in enumerate(gamesGroupedByDate):
    table_body = gamesInADate.find('tbody')
    rows = table_body.find_all('tr')
    # print("PARSING RESPONSE: index",index, dates[index], len(rows))
    for row in rows:        
      cols = row.find_all('td')
      cols = [ele.text.strip() for ele in cols]
      # print("Adding matchNum", cols[0])
      game = {'date':dates[index], 
              'matchNum': cols[0],
              'time': cols[1].replace("\n\nScheduled",""),
              # 'home': cols[2].replace("Freehold SL Freehold SL ", " "),
              'result': cols[3],
              # 'away': cols[4].replace("Freehold SL Freehold SL ", " "),
              'location': cols[5],
              'division': cols[6],
              'homeGame': 'HOME' if "Freehold SL" in cols[2] else 'AWAY',
              'year': cols[6].split(" ")[0],
              'sex': cols[6].split(" ")[1]
             }
      team1 = cols[2].replace("Freehold SL Freehold SL ", "")
      team2 = cols[4].replace("Freehold SL Freehold SL ", "")
      
      game['freeholdTeam'] = team1 if game['homeGame'] == 'HOME' else team2
      game['opponent'] = team1 if game['homeGame'] != 'HOME' else team2
      
      try:
        homeField, homeFieldNum = game['location'].rsplit("-", 1)
        game['field'] = homeField.strip()
        game['fieldNum'] = homeFieldNum.strip()
      except:
        game['field'] = ''
        game['fieldNum'] = ''
        
      games.append(game)
    
    # print("games", len(games))
    #   for g in games:
    #     print(g)
  return games

# url = "https://system.gotsport.com/org_event/events/18280/schedules?club=3694"
# html = getHtml(url)
# games = parseHtml(html)
