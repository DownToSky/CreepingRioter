import networkx as nx
import time
import requests
import json


class Crawler():
    def __init__(self, api_key, name, region):
        self.G = nx.Graph()
        self.source = name
        self.region = region
        self.KEY = api_key
        self.REQ_RATE = 600/500
        self.LAST_REQ_TIME = 0
        self.API_BASE = "https://{region}.api.pvp.net"
        self.SUMMONER_BYNAME_URL = "/api/lol/{region}/v1.4/summoner/by-name/{summoner}"
        self.SUMMONER_BYID_URL = "/api/lol/{region}/v1.4/summoner/{ids}"
        self.NAMES_BYID_URL = "/api/lol/{region}/v1.4/summoner/{ids}/name"
        self.MATCH_URL = "/api/lol/{region}/v2.2/match/{matchid}"
        self.GAME_URL = "/api/lol/{region}/v1.3/game/by-summoner/{summonerId}/recent"
        self.API_KEY_URL = "?api_key={key}"

    def wait_for_api_ready(self):
        curr_time = time.time()
        if self.REQ_RATE+self.LAST_REQ_TIME > curr_time:
            time.sleep(self.REQ_RATE+self.LAST_REQ_TIME-curr_time)
        self.LAST_REQ_TIME = time.time()

    def get_summoner_names(self, names_list):
        names_list = [str(ID) for ID in names_list]
        names_dict = dict()
        for i in range(0,len(names_list),40):
            if i+40>len(names_list):
                requested_names = ','.join(names_list[i:])
            else:
                requested_names = ','.join(names_list[i:i+40])
            status = None
            while status != 200:
                self.wait_for_api_ready()
                req = requests.request('GET', (self.API_BASE + self.NAMES_BYID_URL + self.API_KEY_URL)
                        .format(region = self.region, ids = requested_names, key = self.KEY))
                status = req.status_code
                if status == 200:
                    names_dict = {**names_dict, **req.json()}
                req.close()
        return names_dict

    def get_summoner_id(self, summoner):
        req = requests.request('GET', (self.API_BASE + self.SUMMONER_BYNAME_URL + self.API_KEY_URL)
                        .format(region = self.region, summoner = summoner, key = self.KEY))
        if req.status_code == 200:
            summoner_dict = req.json()
            name_key = [x for x in summoner_dict]
            req.close()
            return summoner_dict[name_key[0]]["id"]
        else:
            req.close()
            return None

    def get_match_history(self, summonerId):
        req = requests.request('GET', (self.API_BASE + self.GAME_URL + self.API_KEY_URL)
                        .format(region = self.region , summonerId = summonerId, key = self.KEY))
        if req.status_code == 200:
            players_dict = dict()
            games_dict = req.json()
            for game in games_dict["games"]:
                summoner_team_id = game["teamId"]
                if "fellowPlayers" not in game:
                    print(summonerId)
                    continue
                for player in game["fellowPlayers"]:
                    if player["teamId"] == summoner_team_id:
                        if player["summonerId"] in players_dict:
                            players_dict[player["summonerId"]].add(game["gameId"])
                        else:
                            players_dict[player["summonerId"]] = set([game["gameId"]])
            req.close()
            return players_dict
        else:
            req.close()
            return None

    def process(self, search_level):
        source_id = None
        while source_id == None:
            source_id = self.get_summoner_id(self.source)
        self.G.add_node(source_id)
        q = [source_id]
        q_next=[]
        for i in range(0, search_level):
            while len(q)!= 0:
                self.wait_for_api_ready()
                neighbors = self.get_match_history(q[-1])
                if neighbors != None:
                    s = q.pop()
                    for n in neighbors:
                        if n in self.G[s]:
                            for game_id in neighbors[n]:
                                if not game_id in self.G[s][n]["games"]:
                                    self.G[s][n]["games"].add(game_id)
                                    self.G[s][n]["weight"]+=1
                        else:
                            q_next.append(n)
                            self.G.add_edge(s ,n ,weight=len(neighbors[n]) ,games=neighbors[n])
            q = q_next
            print(q)
            q_next = list()
        #Getting their summoner names
        names_dict = self.get_summoner_names(self.G.nodes())
        names_dict = {int(k):t for k,t in names_dict.items()}
        for ID in names_dict:
            nx.set_node_attributes(self.G, "name", names_dict)

    def Draw(self):
        D = nx.Graph()
        names = nx.get_node_attributes(self.G, "name")
        for e in self.G.edges(data=True):
            D.add_edge(names[e[0]], names[e[1]], weight = e[2]['weight'])
        nx.write_graphml(D, "test.graphml")

