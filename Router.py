# coding=utf-8



from LoRaMeshLibrary.Route import Route
from LoRaMeshLibrary.Neighbor import Neighbor



class Router:

    def __init__(self, pycomInterface, myMac):
        self.neighbors = {}
        #self.routes = {}
        self.myMac = myMac
        self.pycomInterface = pycomInterface

    def deriveRouterData(self, message, receivedLoraStats):

        #receivedLoraStats from lora.stats() https://docs.pycom.io/firmwareapi/pycom/network/lora/
        
        if self.macIsNeighbour(message.senderMac): 
            #update knowledge
            self.neighbors[message.senderMac].rssi = receivedLoraStats.rssi
            self.neighbors[message.senderMac].time = self.pycomInterface.ticks_ms()
        else:
            #New neighbor
            self.neighbors[message.senderMac] = Neighbor(message.senderMac, receivedLoraStats.rssi, self.pycomInterface.ticks_ms())
        
        #every node up until sender (and our selves should be included)
        verifiedRoute = message.route.getUpUntil(message.senderMac) #kan vi veta att sändaren finns med?
        self.neighbors[message.senderMac].addNodesBeyond(verifiedRoute)



    def getNeighbors(self):
        return self.neighbors

    def shouldIReRoute(self, route, senderMac):
        #This message already passed through me
        if not route.notInRoute(self.myMac):
            return False

        r = route
        T = r.getTarget()
        S = senderMac
        if T in self.neighbors and T != S:
            return True

        if self.neighbors[S].hasTarget(T):
            jumpsBehindSenderToTarget = self.neighbors[S].getJumpsToTarget(T)

            fewestJumpsBehindOtherNeighborToTarget = jumpsBehindSenderToTarget+1 #larger than that
            bestNeighbor  = -1
            for n in self.neighbors:
                N = self.neighbors[n]
                if N.hasTarget(T) and n != S:
                    njtt = N.getJumpsToTarget(T)
                    if njtt < fewestJumpsBehindOtherNeighborToTarget:
                        fewestJumpsBehindOtherNeighborToTarget = njtt
                        bestNeighbor = N

            shouldRoute = fewestJumpsBehindOtherNeighborToTarget <= jumpsBehindSenderToTarget
            
            print(self.myMac, S, " JumpsBehindSender: ", jumpsBehindSenderToTarget, self.neighbors[S], bestNeighbor, ", JumpsbehindNeigh: ", fewestJumpsBehindOtherNeighborToTarget, shouldRoute, flush=True)
            return shouldRoute
        return True

    
    
    def macIsNeighbour(self, mac):
        if mac in self.neighbors:
            return True
        return False
    