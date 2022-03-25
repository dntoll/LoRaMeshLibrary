from LoRaMeshLibrary.Message import Message
from LoRaMeshLibrary.Router import Router
from LoRaMeshLibrary.Route import Route
from LoRaMeshLibrary.SendQue import SendQue
from LoRaMeshLibrary.MessageChecksum import MessageChecksum

#this class implements the mesh network protocol
class MeshController:

    def __init__(self, view, myMac, pycomInterface, callback):
        self.sendQue = SendQue(pycomInterface)
        self.router = Router(pycomInterface, myMac)
        self.myMac = myMac
        self.view = view
        self.callback = callback

    def onReceive(self, message, loraStats):
        
        self.router.deriveRouterData(message, loraStats)

        route = message.getRoute()
        if route.getTarget() is self.myMac:
            self._reachedFinalTarget(message)
        else:
            self._receivedMessageMeantForOther(message)
    
    def getSendQue(self):
        return self.sendQue

    def _reachedFinalTarget(self, message):
        if message.isAcc():
            self.view.receiveAccToMe(message)
            #We acc the acc to make sure other search paths are filled
            if self.sendQue.tryToAccMessagesInQue(message):
                relayedAccMessage = Message(self.myMac, message.getRoute(), Message.TYPE_ACC, bytes(message.contentBytes))
                self.addToQue(relayedAccMessage) 
            #else:
            #    print("We should not be target of acc unless we have a message")
        else:
            #ACC Message
            self.callback(message.getRoute().getOrigin(), message.contentBytes)
            self.view.receiveMessageToMe(message)    

            accRoute = Route(bytes([self.myMac, message.getRoute().getOrigin()]))
            checksum = MessageChecksum.fromMessage(message)

            self.addToQue(Message(self.myMac, accRoute, Message.TYPE_ACC, checksum.toBytes()))

    def _receivedMessageMeantForOther(self, message):    

        route = message.getRoute()
        messageFinalTarget = route.getTarget()

        if message.isAcc():
            self.view.receiveAccToOther(message)
            if self.sendQue.tryToAccMessagesInQue(message):
                messageFinalTarget = route.getTarget()
                fromMeToTarget = Route(bytes([self.myMac, messageFinalTarget]))
                newRoute = route.expandTail(fromMeToTarget)
                relayedAccMessage = Message(self.myMac, newRoute, Message.TYPE_ACC, bytes(message.contentBytes))
                self.addToQue(relayedAccMessage)
        else:
            self.view.receivedRouteMessage(message)
            if self.router.shouldIReRoute(message.getRoute(), message.senderMac):
                self._reroute(route, message)

    def getKnownNeighbors(self):
        return self.neighbors

    def addToQue(self, message):
        self.sendQue.addToQue(message)

   
    def _reroute(self, route, message):
        #add yourself
        messageFinalTarget = route.getTarget()
        fromMeToTarget = Route(bytes([self.myMac, messageFinalTarget]))
        newRoute = route.expandTail(fromMeToTarget)

        searchMessage = Message(self.myMac, newRoute, message.messageType, bytes(message.contentBytes))
        self.view.passOnFindMessage(searchMessage)
        self.addToQue(searchMessage)