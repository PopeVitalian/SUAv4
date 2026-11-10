# poveže ServerRoomService z WSGI aplikacijo

from spyne import Application
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from server.service import ServerRoomService

application = Application(
    services=[ServerRoomService],
    tns="serverroom.soap",
    name="ServerRoomService",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(application)