from LoRaMeshLibrary.ThreadSafeLoraSocket import ThreadSafeLoraSocket
from LoRaMeshLibrary.PycomInterface import PycomInterface
from LoRaMeshLibrary.PymeshAdapter import PymeshAdapter

class MeshFacade:
    def __init__(self, view, callback):
        self.pma = PymeshAdapter(view, ThreadSafeLoraSocket(), PycomInterface(), callback)

    def getMyAddress(self):
        return self.pma.getMyAddress()

    def sendMessage(self, target_ip, message):
        self.pma.sendMessage(target_ip, message)

    def getKnownNodes(self):
        return self.pma.getKnownNodes()

    def getMessagesInSendQue(self):
        return self.pma.getMessagesInSendQue()

    def getNeighbors(self):
        return self.pma.getNeighbors()
    
    def getRoutes(self):
        return self.pma.getRoutes()

    def pingNeighbors(self):
        return self.pma.pingNeighbors()
