from api import Api
import time, datetime
import math, random

class Bot():
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.api = Api()
        self.board_id = 2
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
        for gameObj in board["data"]["gameObjects"]:
            if gameObj["type"] == "BotGameObject" and gameObj["properties"]["name"] == self.name:
                self.oldPosition["x"] = self.position["x"]
                self.oldPosition["y"] = self.position["y"]
                self.position["x"] = gameObj["position"]["x"]
                self.position["y"] = gameObj["position"]["y"]
                self.home["x"] = gameObj["properties"]["base"]["x"]
                self.home["y"] = gameObj["properties"]["base"]["y"]

                self.inventory = gameObj["properties"]["diamonds"]
                if gameObj["properties"]["millisecondsLeft"] < board["data"]["minimumDelayBetweenMoves"]:
                    self.should_rejoin = True
                else:
                    self.should_rejoin = False
                break

    def _rejoin(self):
        return self.join_board(self.board_id)

    def _go_home(self, board):
        lowest = {"r": 10000, "object": None, "type": None}
        lowest["r"] = self._getDelta(self.position, {"position": {"x": self.home["x"], "y": self.home["y"]}})
        lowest["object"] = self.home
        #deltaX = self.position["x"] - self.home["x"]
        #deltaY = self.position["y"] - self.home["y"]
        for o in board["data"]["gameObjects"]:
            r = self._getDelta(self.home, o)

            if o["type"] == "TeleportGameObject":
                #Find the other teleporter
                for o2 in board["data"]["gameObjects"]:
                    if o2 != o and o2["type"] == "TeleportGameObject":
                        r2 = self._getDelta(self.home, o2)
                        if (r2+r) < lowest["r"]:
                            #print("TA TELEPORT HEM")
                            lowest["r"] = r2+r
                            lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}





        if random.randint(0,2) == 1:
            if self.position["x"] > lowest["object"]["x"]:
                return "West"
            elif self.position["x"] < lowest["object"]["x"]:
                return "EAST"
            elif self.position["y"] > lowest["object"]["y"]:
                return "NORTH"
            else:
                return "SOUTH"
        else:
            if self.position["y"] > lowest["object"]["y"]:
                return "NORTH"
            elif self.position["y"] < lowest["object"]["y"]:
                return "SOUTH"
            elif self.position["x"] > lowest["object"]["x"]:
                return "West"
            else:
                return "EAST"

    def _getDelta(self, _from, to):
        deltaX = to["position"]["x"] - _from["x"]
        deltaY = to["position"]["y"] - _from["y"]
        return math.sqrt(pow(deltaX,2) + pow(deltaY,2))

    def _does_exist(self, board, target):
        for o in board["data"]["gameObjects"]:
            if target["x"] == o["position"]["x"] and target["y"] == o["position"]["y"]:
                return True
        return False

    def _where_to(self, board):
        #print("pos: " + str(self.position) + " old: " + str(self.oldPosition))
        if self.position == self.oldPosition:
            return random.choice(["NORTH", "WEST", "SOUTH", "EAST"])
        if self.inventory >= 4:
            return self._go_home(board)
        else:
            lowest = {"r": 10000, "object": None, "type": None}
            for obj in board["data"]["gameObjects"]:
                if obj["type"] == "DiamondGameObject":
                    r = self._getDelta(self.position, obj)
                    if r < lowest["r"]:
                        lowest["r"] = r
                        lowest["object"] = {"x": obj["position"]["x"], "y": obj["position"]["y"], "points": obj["properties"]["points"]}
                        lowest["type"] = "diamond"


            for o in board["data"]["gameObjects"]:
                r = self._getDelta(self.home, o)

                if o["type"] == "TeleportGameObject":
                    #Find the other teleporter
                    for o2 in board["data"]["gameObjects"]:
                        if o2 != o and o2["type"] == "TeleportGameObject":
                            for diamond in board["data"]["gameObjects"]:
                                if diamond["type"] == "DiamondGameObject":
                                    r2 = r + self._getDelta({"x": o2["position"]["x"], "y": o2["position"]["y"]}, diamond)
                                    if r2 < lowest["r"]:
                                        lowest["object"] = {"x": o2["position"]["x"], "y": o2["position"]["y"]}
                                        lowest["type"] = "tp"
                                        lowest["r"] = r2
                elif r/2 < lowest["r"]:
                    if o["type"] == "DiamondButtonGameObject":
                        lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}
                        lowest["type"] = "gen"
                        lowest["r"] = r/2


            diamond = lowest["object"]
            if self.target != None and self._does_exist(board, self.target["object"]) and (self.target["object"]["x"] is not diamond["x"] or self.target["object"]["y"] is not diamond["y"]):
                if lowest["type"] == "diamond" and self.target["type"] == "diamond":
                    print(self.target)
                    print("**********")
                    print(diamond)
                    if self.target["object"]["points"] < diamond["points"] and self.inventory < 4:
                        self.target = lowest
                    else:
                        #print("forstatt mot gamla")
                        diamond = self.target
            elif self.target == None:
                self.target = lowest

            #print("Gar till: X:" + str(diamond["x"]) + " Y: " + str(diamond["y"]))

            if lowest["type"] == "DiamondGameObject" and self.inventory + diamond["properties"]["points"] > 5:
                return self._go_home(board)

            deltaX = self.position["x"] - diamond["x"]
            deltaY = self.position["y"] - diamond["y"]

          
            if self.position["y"] > diamond["y"]:
                return "NORTH"
            elif self.position["y"] < diamond["y"]:
                return "SOUTH"
            elif self.position["x"] > diamond["x"]:
                return "WEST"
            else:
                return "EAST"


    def game_loop(self):
        board = self.get_board_info()
        #print(board["path"])
        while(True):

            if(board is False):
                print("Kan inte hamta board")
                self._rejoin()
                time.sleep(100/1000)
                board = self.get_board_info()
                continue

            self.timeStart = datetime.datetime.now()
            self._update_bot(board)
            #time.sleep(board["data"]["minimumDelayBetweenMoves"] / 1000)
            #time.sleep(40/1000)
            if(self.should_rejoin):
                self._rejoin()

            time.sleep(60 / 1000)

            board = self.move(self._where_to(board))
            self.timeEnd = datetime.datetime.now()
            self.timeDelta = self.timeEnd - self.timeStart
