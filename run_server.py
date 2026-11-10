#!/usr/bin/env python3
# poženi server

from wsgiref.simple_server import make_server

from server.app import wsgi_app


HOST = "127.0.0.1"
PORT = 8007

wsdl_url = "http://" + HOST + ":" + str(PORT) + "/?wsdl"

print("Server Room SOAP service")
print("Listening on   http://" + HOST + ":" + str(PORT))
print("WSDL available http://" + HOST + ":" + str(PORT) + "/?wsdl")
print("Press Ctrl+C to stop.")

server = make_server(HOST, PORT, wsgi_app)
server.serve_forever()