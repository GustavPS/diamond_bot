import collections

class Graph():
    WALKABLE = ["path", "red_diamond", "blue_diamond", "diamond_button"]

    def __init__(self, name):
        self.name = name
    
    # Returns a 2D array (the graph)
    def create_graph(self, board):
        graph = []
        for x in range(0, board["width"]):
            graph.append([])
            for y in range(0, board["height"]):
                graph[x].append({
                    "x": x,
                    "y": y,
                    "type": "path"
                })

        for diamond in board["diamonds"]:
            x = int(diamond["x"])
            y = int(diamond["y"])
            graph[x][y]["type"] = "red_diamond" if diamond["points"] == 2 else "blue_diamond"
            
        for bot in board["bots"]:
            baseX = int(bot["base"]["x"])
            baseY = int(bot["base"]["y"])
            positionX = int(bot["position"]["x"])
            positionY = int(bot["position"]["y"])
            if bot["name"] == self.name:
                graph[baseX][baseY]["type"] = "home_base"
                continue
            graph[positionX][positionY]["type"] = "bot"
            graph[baseX][baseY]["type"] = "bot_base"

        for gameObject in board["gameObjects"]:
            x = int(gameObject["position"]["x"])
            y = int(gameObject["position"]["y"])
            graph[x][y]["type"] = "teleporter" if gameObject["name"] == "Teleporter" else "diamond_button"
            
        return graph

    def bfs(self, graph, start, goal):
        queue = collections.deque([[start]])
        width = 15
        height = 12
        seen = set([start])
        while queue:
            path = queue.popleft()
            x, y = path[-1]
            if graph[x][y]["type"] == goal:
                return path
            for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
                if 0 <= x2 < width and 0 <= y2 < height and graph[x2][y2]["type"] in self.WALKABLE and (x2, y2) not in seen:
                    queue.append(path + [(x2, y2)])
                    seen.add((x2, y2))
        return None
