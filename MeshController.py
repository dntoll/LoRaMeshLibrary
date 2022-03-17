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
        print("hello")
        return self.sendQue
        

    def _reachedFinalTarget(self, message):
        if not message.isAcc() or message.isFind():

            self.callback(message.getRoute().getOrigin(), message.contentBytes)
            self.view.receiveMessageToMe(message)    

            route = message.getRoute()
            newRoute = route.getShortenedRoute(message.senderMac, self.myMac)

            accRoute = newRoute.getBackRoute()
            checksum = MessageChecksum.fromMessage(message)

            self.addToQue(Message(self.myMac, accRoute, Message.TYPE_ACC, checksum.toBytes()))
        elif message.isAcc():
            if self.sendQue.tryToAccMessagesInQue(message):
                self.view.receiveAccToMe(message)
                relayedAccMessage = Message(self.myMac, message.getRoute(), Message.TYPE_ACC, bytes(message.contentBytes))
                self.addToQue(relayedAccMessage)

    def _receivedMessageMeantForOther(self, message):    

        route = message.getRoute()

        messageFinalTarget = route.getTarget()
        
        if route.bothInRouteAndOrdered(message.senderMac, self.myMac):
            self._reroute(route, message)
        elif message.isFind() and route.notInRoute(self.myMac):
            self.view.receivedFindMessage(message)

            if self.router.hasRoute(self.myMac, messageFinalTarget):
                self._suggestRoute(route, message)
            else:
                self._passOnFindMessage(route, message)
        else:
            self.view.receivedNoRouteMessage(message)

        if message.isAcc():
            if self.sendQue.tryToAccMessagesInQue(message):
                self.view.receiveAccToOther(message)
                relayedAccMessage = Message(self.myMac, message.getRoute(), Message.TYPE_ACC, bytes(message.contentBytes))
                self.addToQue(relayedAccMessage)

    def getKnownNeighbors(self):
        return self.neighbors

    def addToQue(self, message):
        self.sendQue.addToQue(message)

    def _suggestRoute(self, route, message):
        messageFinalTarget = route.getTarget()
        fromMeToTarget = self.router.getRoute(self.myMac, messageFinalTarget)
        newRoute = route.expandTail(fromMeToTarget) #prevRoute, prevTarget => prevRoute + fromMetoTarget
        relayedMessage = Message(self.myMac, newRoute, Message.TYPE_MESSAGE, bytes(message.contentBytes))
        self.view.suggestRoute(relayedMessage)
        self.addToQue(relayedMessage)
    
    def _passOnFindMessage(self, route, message):
        messageFinalTarget = route.getTarget()
        fromMeToTarget = Route(bytes([self.myMac, messageFinalTarget]))
        newRoute = route.expandTail(fromMeToTarget)
        searchMessage = Message(self.myMac, newRoute, Message.TYPE_FIND, bytes(message.contentBytes))
        self.view.passOnFindMessage(searchMessage)
        self.addToQue(searchMessage)

    def _reroute(self, route, message):
        newRoute = route.getShortenedRoute(message.senderMac, self.myMac)
        relayedMessage = Message(self.myMac, newRoute, message.messageType, bytes(message.contentBytes))
        self.view.receivedRouteMessage(relayedMessage)
        self.addToQue(relayedMessage)