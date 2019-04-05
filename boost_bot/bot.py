from api import Api
import time, datetime
import math, random
from pprint import pprint
import collections

class Bot():
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.api = Api()
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
        #print(req.content)
        return False

    def _update_bot(self, board):
        for bot in board["bots"]:
            if bot["name"] == self.name:
                self.oldPosition["x"] = self.position["x"]
                self.oldPosition["y"] = self.position["y"]
                self.position["x"] = bot["position"]["x"]
                self.position["y"] = bot["position"]["y"]
                self.home["x"] = bot["base"]["x"]
                self.home["y"] = bot["base"]["y"]

                self.inventory = bot["diamonds"]

                if bot["millisecondsLeft"] < board["minimumDelayBetweenMoves"]:
                    self.should_rejoin = True
                else:
                    self.should_rejoin = False

                break

    def _rejoin(self):
        return self.join_board(self.board_id)

    def _go_home(self, board):
        board2 = self.create_graph(board)
        path = self.bfs(board2, (int(self.position["x"]),int(self.position["y"])), "home_base")
        pprint(path)
        if len(path) > 1:
            goal = path[1]
        else:
            goal = path[0]
        """
        lowest = {"r": 10000, "object": None, "type": None}
        lowest["r"] = self._getDelta(self.position, self.home)
        lowest["object"] = self.home
        #deltaX = self.position["x"] - self.home["x"]
        #deltaY = self.position["y"] - self.home["y"]

        for o in board["gameObjects"]:
            r = self._getDelta(self.home, {"x": o["position"]["x"], "y": o["position"]["y"]})

            if o["name"] == "Teleporter":
                #Find the other teleporter
                for o2 in board["gameObjects"]:
                    if o2 != o and o2["name"] == "Teleporter":
                        r2 = self._getDelta(self.home, {"x": o2["position"]["x"], "y": o2["position"]["y"]})
                        if (r2+r) < lowest["r"]:
                            #print("TA TELEPORT HEM")
                            lowest["r"] = r2+r
                            lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}




   


        if random.randint(0,2) == 1:
            if self.position["x"] > lowest["object"]["x"]:
                return "West"
            elif self.position["x"] < lowest["object"]["x"]:
                return "East"
            elif self.position["y"] > lowest["object"]["y"]:
                return "North"
            else:
                return "South"
        else:
        if self.position["y"] > lowest["object"]["y"]:
            return "North"
        elif self.position["y"] < lowest["object"]["y"]:
            return "South"
        elif self.position["x"] > lowest["object"]["x"]:
            return "West"
        else:
            return "East"
        """
        
        if goal[0] < self.position["x"]:
            return "West"
        elif goal[0] > self.position["x"]:
            return "East"
        elif goal[1] < self.position["y"]:
            return "North"
        elif goal[1] > self.position["y"]:
            return "South"
        else:
            print("dafuq")

    def _getDelta(self, _from, to):
        deltaX = to["x"] - _from["x"]
        deltaY = to["y"] - _from["y"]
        return math.sqrt(pow(deltaX,2) + pow(deltaY,2))

    def _does_exist(self, board, target):
        for o in board["diamonds"]:
            if target["x"] == o["x"] and target["y"] == o["y"]:
                return True
        return False

    def bfs(self, grid, start, goal):
        queue = collections.deque([[start]])
        width = 15
        height = 12
        seen = set([start])
        while queue:
            path = queue.popleft()
            x, y = path[-1]
            if grid[x][y]["type"] == goal:
                return path
            for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
                if 0 <= x2 < width and 0 <= y2 < height and (grid[x2][y2]["type"] == "path" or grid[x2][y2]["type"] == "diamond" or grid[x2][y2]["type"] == "diamond_button")  and (x2, y2) not in seen:
                    queue.append(path + [(x2, y2)])
                    seen.add((x2, y2))

    def create_graph(self, board):
        graph = []
        count = 0
        for x in range(0, board["width"]):
            graph.append([])
            for y in range(0, board["height"]):
                n = {
                    "x": x,
                    "y": y,
                    "type": "path",
                    "edges": []
                }
                
                for diamond in board["diamonds"]:
                    if diamond["x"] == x and diamond["y"] == y:
                        check = True
                        n["type"] = "diamond"
                        break

                graph[x].append(n)
                    
        for bot in board["bots"]:
            if bot["name"] == self.name:
                graph[int(bot["base"]["x"])][int(bot["base"]["y"])]["type"] = "home_base"
                continue
                
            graph[int(bot["position"]["x"])][int(bot["position"]["y"])]["type"] = "bot"
            graph[int(bot["base"]["x"])][int(bot["base"]["y"])]["type"] = "bot_base"

        for gameObject in board["gameObjects"]:
            if gameObject["name"] == "Teleporter":
                graph[int(gameObject["position"]["x"])][int(gameObject["position"]["y"])]["type"] = "teleporter"
            elif gameObject["name"] == "DiamondButton":
                graph[int(gameObject["position"]["x"])][int(gameObject["position"]["y"])]["type"] = "diamond_button"
            
        return graph


    def _where_to(self, board):
        board2 = self.create_graph(board)
        path = self.bfs(board2, (int(self.position["x"]),int(self.position["y"])), "diamond_button")

        pprint(path)
        if len(path) > 1:
            goal = path[1]
        else:
            goal = path[0]

        
        '''
        if self.position == self.oldPosition:
            return random.choice(["North", "West", "South", "East"])

        else:
            lowest = {"r": 10000, "object": None, "type": None}
            for diamond in board["diamonds"]:
                r = self._getDelta(self.position, diamond)
                if r < lowest["r"]:
                    lowest["r"] = r
                    lowest["object"] = diamond
                    lowest["type"] = "diamond"


            for o in board["gameObjects"]:
                r = self._getDelta(self.position, {"x": o["position"]["x"], "y": o["position"]["y"]})

                if o["name"] == "Teleporter":
                    #Find the other teleporter
                    for o2 in board["gameObjects"]:
                        if o2 != o and o2["name"] == "Teleporter":
                            for diamond in board["diamonds"]:
                                r2 = r + self._getDelta({"x": o2["position"]["x"], "y": o2["position"]["y"]}, diamond)
                                if r2 < lowest["r"]:
                                    lowest["object"] = {"x": o2["position"]["x"], "y": o2["position"]["y"]}
                                    lowest["type"] = "tp"
                                    lowest["r"] = r2
                elif r/2 < lowest["r"]:
                    if o["name"] == "DiamondButton":
                        lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}
                        lowest["type"] = "gen"
                        lowest["r"] = r/2


            diamond = lowest["object"]
            if self.target != None and self._does_exist(board, self.target["object"]) and (self.target["object"]["x"] is not diamond["x"] or self.target["object"]["y"] is not diamond["y"]):
                if lowest["type"] == "diamond" and self.target["type"] == "diamond":
                    if self.target["object"]["points"] < diamond["points"] and self.inventory < 4:
                        self.target = lowest
                    else:
                        #print("forstatt mot gamla")
                        diamond = self.target["object"]
            elif self.target == None:
                self.target = lowest

            print("Gar till: X:" + str(diamond["x"]) + " Y: " + str(diamond["y"]))

            if lowest["type"] == "diamond" and self.inventory + diamond["points"] > 5:
                return self._go_home(board)

            deltaX = self.position["x"] - diamond["x"]
            deltaY = self.position["y"] - diamond["y"]


        if random.randint(0,2) == 1:
            if self.position["x"] > diamond["x"]:
                return "West"
            elif self.position["x"] < diamond["x"]:
                return "East"
            elif self.position["y"] > diamond["y"]:
                return "North"
            else:
                return "South"
        '''
        if goal[0] < self.position["x"]:
            return "West"
        elif goal[0] > self.position["x"]:
            return "East"
        elif goal[1] < self.position["y"]:
            return "North"
        elif goal[1] > self.position["y"]:
            return "South"
        else:
            print("dafuq")


        """
        if self.position["y"] > diamond["y"]:
            return "North"
        elif self.position["y"] < diamond["y"]:
            return "South"
        elif self.position["x"] > diamond["x"]:
            return "West"
        else:
            return "East"
        """


    def game_loop(self):
        board = self.get_board_info()
        while(True):

            if(not board):
                print("Kan inte hamta board")
                self._rejoin()
                #time.sleep(100/1000)
                board = self.get_board_info()
                continue

            self.timeStart = datetime.datetime.now()
            self._update_bot(board)
            #time.sleep(board["minimumDelayBetweenMoves"] / 1000)
            #time.sleep(20/1000)
            if(self.should_rejoin):
                self._rejoin()

            time.sleep(50 / 1000)

            board = self.move(self._where_to(board))
            self.timeEnd = datetime.datetime.now()
            self.timeDelta = self.timeEnd - self.timeStart
