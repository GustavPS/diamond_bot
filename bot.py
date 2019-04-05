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
    MAX_INVENTORY = 4
    RED_DIAMOND_EXTRA_DISTANCE = 3
    MINIMUM_TIME_LEFT = 1500 # milliseconds
    
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.api = Api()
        self.graph = Graph(name)
        self.board_id = 1
        self.position = { "x": 0, "y": 0 }
        self.home = {"x": 0, "y": 0}
        self.inventory = 0
        self.target = None
        self.timeDelta = 0
        self.timeStart = None
        self.timeEnd = None
        self.oldPosition = { "x": 0, "y": 0 }
        self.should_rejoin = False


    def register_bot(self, email, name):
        data = {
            "email": email,
            "name": name
        }

        self.api.set_data(data)
        req = self.api._req("/bots", "POST")
        if(req.status_code == 200):
            return req.json()
        return False

    def join_board(self, board):
        data = {
            "botToken": self.token
        }
        self.api.set_data(data)
        req = self.api._req("/boards/"+str(board)+"/join", "POST")
        if(req.status_code == 200):
            self.board_id = board
            return True
        return False

    def get_board_info(self):
        req = self.api._req("/boards/"+str(self.board_id), "GET")
        if(req.status_code == 200):
            return req.json()
        return False

    def move(self, direction):
        data = {
            "botToken": self.token,
            "direction": direction
        }
        self.api.set_data(data)
        req = self.api._req("/boards/"+str(self.board_id)+"/move", "POST")
        if req.status_code == 200:
            return req.json()
        return False

    def update_bot(self, board):
        for bot in board["bots"]:
            if bot["name"] == self.name:
                self.oldPosition["x"] = self.position["x"]
                self.oldPosition["y"] = self.position["y"]
                self.position["x"] = bot["position"]["x"]
                self.position["y"] = bot["position"]["y"]
                self.home["x"] = bot["base"]["x"]
                self.home["y"] = bot["base"]["y"]
                self.inventory = bot["diamonds"]
                self.timeLeft = bot["millisecondsLeft"]
                if bot["millisecondsLeft"] < board["minimumDelayBetweenMoves"]:
                    self.should_rejoin = True
                else:
                    self.should_rejoin = False
                break

    def rejoin(self):
        return self.join_board(self.board_id)

    def go_home(self, board):
        graph = self.graph.create_graph(board)
        path = self.graph.bfs(graph, (int(self.position["x"]),int(self.position["y"])), "home_base")
        if path is None:
            return self.STAY
        
        
        goal = path[1] if len(path) > 1 else path[0]
        if goal[0] < self.position["x"]:
            return self.WEST
        elif goal[0] > self.position["x"]:
            return self.EAST
        elif goal[1] < self.position["y"]:
            return self.NORTH
        elif goal[1] > self.position["y"]:
            return self.SOUTH

    def should_go_home(self, board):
        if self.inventory >= self.MAX_INVENTORY or \
           self.timeLeft <= self.MINIMUM_TIME_LEFT:
            return True
        return False

    def where_to(self, board):
        if self.should_go_home(board):
            return self.go_home(board)

        graph = self.graph.create_graph(board)
        path_blue = self.graph.bfs(graph, (int(self.position["x"]),int(self.position["y"])), "blue_diamond")
        path_red  = self.graph.bfs(graph, (int(self.position["x"]),int(self.position["y"])), "red_diamond")
        if path_blue is None and path_red is None:
            return self.STAY
        if path_red != None and len(path_red) < len(path_blue) + self.RED_DIAMOND_EXTRA_DISTANCE:
            if len(path_red) > 1:
                goal = path_red[1]
            else:
                goal = path_red[0]
        else:
            if len(path_blue) > 1:
                goal = path_blue[1]
            else:
                goal = path_blue[0]

        if goal[0] < self.position["x"]:
            return self.WEST
        elif goal[0] > self.position["x"]:
            return self.EAST
        elif goal[1] < self.position["y"]:
            return self.NORTH
        elif goal[1] > self.position["y"]:
            return self.SOUTH

    def game_loop(self):
        board = self.get_board_info()
        while(True):
            if(not board):
                print("Kan inte hamta board")
                self.rejoin()
                board = self.get_board_info()
                continue

            self.update_bot(board)
            if(self.should_rejoin):
                self.rejoin()


            time.sleep(40/1000)
            """
            WAIT_TIME_SECONDS = 0.1
            target = self.where_to(board)
            print(target)

            ticker = threading.Event()
            while not ticker.wait(WAIT_TIME_SECONDS):
                print(1)
                if target is not "Stay":
                    board = self.move(target)
                else:
                    board = self.update_bot(board)
            """
            direction = self.where_to(board)
            if direction is self.STAY:
                board = self.get_board_info()
            else:
                board = self.move(direction)
   
