############################################################################
#Importing Tools#
############################################################################
from riotwatcher import LolWatcher, ApiError
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

############################################################################
#!!API KEY GOES HERE!!                                                     #
############################################################################
_riotAPIKey = "RGAPI-c43cd41c-a6b1-449d-8af1-d01524de027c"

#DISCLAIMER: THE SCRIPT MIGHT TAKE A LONG TIME TO LOAD, UP TO 30MINUTES!#
#ITS BECAUSE THE API IS RATE LIMITED AT 100 REQUESTS PER 2 MINUTES, AND I AM ACCESSING 1000 MATCHES#

############################################################################
#Converting data from the API into DataFrames                              #
############################################################################
#Setting up the Watcher Tool
_watcher = LolWatcher(_riotAPIKey)

#Region
platformRoutingValue = "EUW1"

participantlist = ["FIeshy", "Kieran Tierney", "Patrik22", "Drututt", "supaaaaaaaaaaaaa", "FFDP", "Emerald Dragon", "Kaor1", "Hεy lol", "Exakiiick1"]
#EUW Summoner Names: ["FIeshy", "Kieran Tierney", "Patrik22", "Drututt", "supaaaaaaaaaaaaa", "FFDP", "Emerald Dragon", "Kaor1", "Hεy lol", "Exakiiick1", "Dzu", "SLEYERCOOL", "DRX BuZz", "AHaHaCiK", "MetroArcher"]
#https://www.leagueofgraphs.com/rankings/summoners/euw

#Queue IDs: https://static.developer.riotgames.com/docs/lol/queues.json (basically serves to filter the type of game mode being played, in this case: Queue ID 400 is 5v5 draft pick games)
_queueId = 420

#The List of Match IDs
matches = []
#The List of Matches as data
matchesdf = []

#looks into the participant list and extracts their matches 
for _participant in participantlist:
    _participantpuuid = _watcher.summoner.by_name(platformRoutingValue, _participant)["puuid"]   
    matchlists = _watcher.match.matchlist_by_puuid(platformRoutingValue, _participantpuuid, 0, 100, _queueId)
    for _match in matchlists:
        matches.append(_match)
    
#gets the match dictionaries from the list of matches from the api
for _matchid in matches:
    _matchdata = _watcher.match.by_id(platformRoutingValue, _matchid)
    matchesdf.append(_matchdata)

dfs = []
participantdfs = []
for match in matchesdf:
    
    #reading the teams data from the match data
    _df = pd.json_normalize(data = match["info"], record_path = "teams", meta = ["gameId"])
    dfs.append(_df)
    #reading the participant data from the match data
    _dfp = pd.json_normalize(data = match["info"], record_path = "participants", meta = ["gameId"])
    participantdfs.append(_dfp)

teamdata = pd.concat(dfs, ignore_index = True)
playerdata = pd.concat(participantdfs, ignore_index = True) 

############################################################################
#Does the jungle’s performance play a role in getting the first dragon?    #
############################################################################
def FirstDragontoPlayer(player):
    team = player["teamId"]
    game = player["gameId"]
    
    filter = (teamdata["teamId"] == team) & (teamdata["gameId"] == game)
    singleteam = teamdata[filter]

    return singleteam.iloc[0]["objectives.dragon.first"]
    
playerdata["firstDragon"] = playerdata.apply(FirstDragontoPlayer, axis = 1)

#Filtering the playerdata with the players that played jungle
junglerdata = playerdata[playerdata["lane"] == "JUNGLE"]

#two databases with the junglers that took first dragon and the ones that did not
junglerdatafd = junglerdata[junglerdata["firstDragon"] == True]
junglerdatanfd = junglerdata[~junglerdata["firstDragon"] == True]

#first dragon/not first dragon kills
fdj = junglerdatafd["kills"].describe()
nfdj = junglerdatanfd["kills"].describe()
#first dragon/not first dragon assists
fdja = junglerdatafd["assists"].describe()
nfdja = junglerdatanfd["assists"].describe()
#first dragon/not first dragon deaths
fdjd = junglerdatafd["deaths"].describe()
nfdjd = junglerdatanfd["deaths"].describe()

#T-Testing#
t1_kills = stats.ttest_ind(junglerdatafd["kills"], junglerdatanfd["kills"])
t2_assists = stats.ttest_ind(junglerdatafd["assists"], junglerdatanfd["assists"])
t3_deaths = stats.ttest_ind(junglerdatafd["deaths"], junglerdatanfd["deaths"])

#Graphs#
figurek, axis = plt.subplots(1,2, sharex=True, sharey=True)
figurek.suptitle("Jungler Kills Based On First Dragon Kill")
axis[0].hist(junglerdatafd["kills"], bins = 25)
axis[0].set(xlabel='First Dragon Kills', ylabel='Frequency')
axis[1].hist(junglerdatanfd["kills"], bins = 25, color="red")
axis[1].set(xlabel='Not-First Dragon Kills')
plt.show()

#Graphs#
figurea, axis = plt.subplots(1,2, sharex=True, sharey=True)
figurea.suptitle("Jungler Assists Based On First Dragon Kill")
axis[0].hist(junglerdatafd["assists"], bins = 20)
axis[0].set(xlabel='First Dragon Assists', ylabel='Frequency')
axis[1].hist(junglerdatanfd["assists"], bins = 20, color="red")
axis[1].set(xlabel='Not-First Dragon Assists')
plt.show()


#Graphs#
figured, axis = plt.subplots(1,2, sharex=True, sharey=True)
figured.suptitle("Jungler Deaths Based On First Dragon Kill")
axis[0].hist(junglerdatafd["deaths"], bins = 16)
axis[0].set(xlabel='First Dragon Deaths', ylabel='Frequency')
axis[1].hist(junglerdatanfd["deaths"], bins = 16, color="red")
axis[1].set(xlabel='Not-First Dragon Deaths')
plt.show()


############################################################################
#Does the first dragon increase chances of victory?                        #
############################################################################
fdragondata = teamdata[teamdata["objectives.dragon.first"] == True]
nfdragondata = teamdata[teamdata["objectives.dragon.first"] == False]

FDWins = fdragondata.groupby(fdragondata["win"]).size()
fdWinrate = (FDWins[True] / (FDWins[True] + FDWins[False])) * 100

NFDWins = nfdragondata.groupby(nfdragondata["win"]).size()
nfdWinrate = (NFDWins[True] / (NFDWins[True] + NFDWins[False])) * 100

#chi squared# 
_fdragondict = pd.DataFrame({"Win": [FDWins[True], NFDWins[True]], "Lose": [FDWins[False], NFDWins[False]]})
t4_winrate = stats.chi2_contingency(_fdragondict, 0)

myPlot = FDWins.plot(kind = "pie", title = "Dragon Win Rates") 
plt.show()

myPlot2 = NFDWins.plot(kind = "pie", title = "No Dragon Win Rates")
plt.show()


############################################################################
#Does the first dragon increase Team Kills?                                #
############################################################################
fDTeamKills = fdragondata["objectives.champion.kills"].describe()
nFDTeamKills = nfdragondata["objectives.champion.kills"].describe()

figuretk, axis = plt.subplots(1,2, sharex=True, sharey=True)
figuretk.suptitle("Team Kills Based On First Dragon Kill")
axis[0].hist(fdragondata["objectives.champion.kills"], bins = 25)
axis[0].set(xlabel='First Dragon Team Kills', ylabel='Frequency')
axis[1].hist(nfdragondata["objectives.champion.kills"], bins = 25, color="red")
axis[1].set(xlabel='Not-First Dragon Team Kills')
plt.show()

t5_teamkills = stats.ttest_ind(fdragondata["objectives.champion.kills"], nfdragondata["objectives.champion.kills"])

