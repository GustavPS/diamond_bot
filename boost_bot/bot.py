from api import Api
from graph import Graph
import time
import math, random
from pprint import pprint
import threading

class Bot():
    NORTH = "North"
    WEST  = "West"
    SOUTH = "South"
    EAST  = "East"
    STAY  = "Stay"
    MAX_INVENTORY = 3
    RED_DIAMOND_EXTRA_DISTANCE = 3
    MINIMUM_TIME_LEFT = 1000 # milliseconds
    
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.api = Api()
        self.graph = Graph(name)
        self.board_id = 1
        self.board = []
        self.position = { "x": 0, "y": 0 }
        self.home = {"x": 0, "y": 0}
        self.inventory = 0
        self.score = 0
        self.target = None
        self.timeDelta = 0
        self.timeStart = None
        self.timeEnd = None
        self.oldPosition = { "x": 0, "y": 0 }
        self.should_rejoin = False
        self.millisecondsLeft = 70000


    def register_bot(self, email, name):
        data = {
            "email": email,
            "name": name
        }

        self.api.set_data(data)
        req = self.api._req("/bots", "POST")
        if(req is not False and req.status_code == 200):
            return req.json()
        return False

    def join_board(self, board):
        data = {
            "botToken": self.token
        }
        self.api.set_data(data)
        req = self.api._req("/boards/"+str(board)+"/join", "POST")
        if(req is not False and req.status_code == 200):
            self.board_id = board
            return True
        return False

    def get_board_info(self):
        req = self.api._req("/boards/"+str(self.board_id), "GET")
        if(req is not False and req.status_code == 200):
            # TEST:
            new = req.json()
            for bot in new["bots"]:
                if bot["name"] == self.name:
                    if len(self.board) == 0 or int(bot["millisecondsLeft"]) < self.millisecondsLeft:
                        self.millisecondsLeft = int(bot["millisecondsLeft"])
                        self.board = req.json()
            return req.json()
        self.should_rejoin = True
        return False

    def move(self, direction):
        data = {
            "botToken": self.token,
            "direction": direction
        }
        self.api.set_data(data)
        req = self.api._req("/boards/"+str(self.board_id)+"/move", "POST")
        if req is not False and req.status_code == 200:
            #TEST:
            new = req.json()
            for bot in new["bots"]:
                if bot["name"] == self.name:
                    if len(self.board) == 0 or int(bot["millisecondsLeft"]) < self.millisecondsLeft:
                        self.millisecondsLeft = int(bot["millisecondsLeft"])
                        self.board = req.json()
            return req.json()
        self.should_rejoin = True
        return False

    def update_bot(self):
        for bot in self.board["bots"]:
            if bot["name"] == self.name:
                self.oldPosition["x"] = self.position["x"]
                self.oldPosition["y"] = self.position["y"]
                self.position["x"] = bot["position"]["x"]
                self.position["y"] = bot["position"]["y"]
                self.home["x"] = bot["base"]["x"]
                self.home["y"] = bot["base"]["y"]
                self.inventory = bot["diamonds"]
                self.score = bot["score"]
                self.timeLeft = bot["millisecondsLeft"]
                if bot["millisecondsLeft"] < self.board["minimumDelayBetweenMoves"]:
                    self.should_rejoin = True
                else:
                    self.should_rejoin = False
                break

    def rejoin(self):
        return self.join_board(self.board_id)

    def go_home(self):
        graph = self.graph.create_graph(self.board)
        path = self.graph.bfs(graph, (int(self.position["x"]),int(self.position["y"])), "home_base")
        if path is None:
            return self.STAY
        
        
        goal = path[1] if len(path) > 1 else path[0]
        if goal[0] < self.position["x"]:
            self.position["x"] -= 1
            return self.WEST
        elif goal[0] > self.position["x"]:
            self.position["x"] += 1
            return self.EAST
        elif goal[1] < self.position["y"]:
            self.position["y"] -= 1
            return self.NORTH
        elif goal[1] > self.position["y"]:
            self.position["y"] += 1
            return self.SOUTH

    def should_go_home(self):
        if self.inventory >= self.MAX_INVENTORY or \
           self.timeLeft <= self.MINIMUM_TIME_LEFT:
            return True
        return False

    def where_to(self):
        graph = self.graph.create_graph(self.board)
        path = self.graph.bfs(graph, (int(self.position["x"]),int(self.position["y"])), "diamond_button")
        if path is None:
            return self.STAY
        if len(path) > 1:
            goal = path[1]
        else:
            goal = path[0]

                
        if goal[0] < self.position["x"]:
            self.position["x"] -= 1
            return self.WEST
        elif goal[0] > self.position["x"]:
            self.position["x"] += 1
            return self.EAST
        elif goal[1] < self.position["y"]:
            self.position["y"] -= 1
            return self.NORTH
        elif goal[1] > self.position["y"]:
            self.position["y"] += 1
            return self.SOUTH

    def update_bot_position(self):
        direction = self.where_to()
        if direction is self.STAY:
            self.board = self.get_board_info()
        else:
            self.board = self.move(direction)

    def game_loop(self):
        self.millisecondsLeft = 70000
        self.board = self.get_board_info()

        timeout = time.time() + 62
        while(True):
            if time.time() > timeout:
                return self.score
            
            self.update_bot()

            direction = self.where_to()
            if direction is self.STAY:
                threading.Thread(target=self.get_board_info ).start()
                #board = self.get_board_info()
            else:
                threading.Thread(target=self.move, args=(direction,)).start()
                #board = self.move(direction)
            time.sleep(100/1000)
