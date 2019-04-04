from api import Api
import time, datetime
import math, random

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
        self.oldPosition = { "x": 0, "y": 0 }
        self.waiting = False

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
        lowest = {"r": 10000, "object": None, "type": None}
        lowest["r"] = self._getDelta(self.position, self.home)
        lowest["object"] = self.home
        #deltaX = self.position["x"] - self.home["x"]
        #deltaY = self.position["y"] - self.home["y"]

        for o in board["gameObjects"]:
            r = self._getDelta(self.position, {"x": o["position"]["x"], "y": o["position"]["y"]})

            if o["name"] == "Teleporter":
                #Find the other teleporter
                for o2 in board["gameObjects"]:
                    if o2 != o and o2["name"] == "Teleporter":
                        r2 = self._getDelta(self.home, {"x": o2["position"]["x"], "y": o2["position"]["y"]})
                        if (r2+r) < lowest["r"]:
                            #print("TA TELEPORT HEM")
                            lowest["r"] = r2+r
                            lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}





        #print("Gar hem")
        if self.position["x"] > lowest["object"]["x"]:
            return "West"
        elif self.position["x"] < lowest["object"]["x"]:
            return "East"
        elif self.position["y"] > lowest["object"]["y"]:
            return "North"
        else:
            return "South"

    def _getDelta(self, _from, to):
        deltaX = to["x"] - _from["x"]
        deltaY = to["y"] - _from["y"]
        return math.sqrt(pow(deltaX,2) + pow(deltaY,2))

    def _does_exist(self, board, target):
        for o in board["diamonds"]:
            if target["x"] == o["x"] and target["y"] == o["y"]:
                return True
        return False

    def _where_to(self, board):
        #print("pos: " + str(self.position) + " old: " + str(self.oldPosition))
        if self.position == self.oldPosition and not self.waiting:
            return random.choice(["North", "West", "South", "East"])
        if self.inventory >= 6:
            return self._go_home(board)
        else:
            lowest = {"r": 10000, "object": None, "type": None}
            for o in board["gameObjects"]:
                r = self._getDelta(self.position, {"x": o["position"]["x"], "y": o["position"]["y"]})
                if o["name"] == "DiamondButton":
                    lowest["object"] = {"x": o["position"]["x"], "y": o["position"]["y"]}
                    lowest["type"] = "gen"
                    lowest["r"] = r


            diamond = lowest["object"]

            deltaX = self.position["x"] - diamond["x"]
            deltaY = self.position["y"] - diamond["y"]

            for bot in board["bots"]:
                if bot["name"] == "GustavFilip":
                    if lowest["r"] == 1 and self._diamonds_around_object(board, bot["base"]) >= 1:
                        self.waiting = True
                        return "Stop"
            self.waiting = False

            if self.position["x"] > diamond["x"]:
                return "West"
            elif self.position["x"] < diamond["x"]:
                return "East"
            elif self.position["y"] > diamond["y"]:
                return "North"
            else:
                return "South"


    def _diamonds_around_object(self, board, o):
        count = 0
        for diamond in board["diamonds"]:
            r = self._getDelta(diamond, o)
            if r < 2:
                count += 1

        print(count)
        return count
            

    def game_loop(self):
        board = self.get_board_info()
        while(True):
            if(not board):
                print("Kan inte hamta board")
                self._rejoin()
                time.sleep(100/1000)
                board = self.get_board_info()
                continue


            self._update_bot(board)
            #time.sleep(board["minimumDelayBetweenMoves"] / 1000)
            #time.sleep(20/1000)
            if(self.should_rejoin):
                self._rejoin()

            time.sleep(100/1000)

            direction = self._where_to(board)
            if direction != "Stop":
                board = self.move(self._where_to(board))
            else:
                board = self.get_board_info()
