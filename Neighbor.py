class Neighbor:
    def __init__(self, mac, rssi, time):
        self.mac = mac
        self.rssi = rssi
        self.time = time
        self.nodesBeyondSet = {}

    def addNodesBeyond(self, route):
        #print(self)
        #print(route)
        #This is called when we get a message from the sender self.mac
        if not self.mac in route.getBytes():
            #We are not in the verified route... but this must be wrong since we sent it
            route = route.addToEnd(self.mac)

        totalNodes = len(route.getBytes())
        if totalNodes > 2: #beyond, Sender, self
            for index, r in enumerate(route.getBytes()):
                if self.mac is r:
                    break

                distance = totalNodes-index-1
                #if (distance == 0):
                #    print(self.mac, route, totalNodes, index, flush=True)
                assert(distance > 0)
                if r in self.nodesBeyondSet:
                    self.nodesBeyondSet[r] = min(self.nodesBeyondSet[r], distance)
                else:
                    self.nodesBeyondSet[r] = distance
        #print(self)


    def hasTarget(self, node):
        return node in self.nodesBeyondSet

    def getJumpsToTarget(self, node):
        return self.nodesBeyondSet[node]
    
    def __repr__(self):
        routeStr = "N" + str(self.mac)
        for b in self.nodesBeyondSet:
            routeStr += "[" + str(b) + "," + str(self.nodesBeyondSet[b]) + "]"
        return routeStr

