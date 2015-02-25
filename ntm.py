import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import json

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("home.html") 
    def post(self):
        print("Creating room: " + self.get_body_argument("room_name"))
        self.set_header("Content-Type", "text/plain")
        self.write("fark")

class RoomHandler(tornado.web.RequestHandler):
    def get(self, room_name):
        self.render("room.html", room_name=room_name) 

class ChatWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
        response = {"type": "chat_message", "user": "room", "message": "hello!!! $x = 2$"}
        self.write_message(json.dumps(response))

    def on_message(self, message):
        message = json.loads(message)
        if message["type"] == "chat_message":
            response = {"type":"chat_message", "user": "echo", "message":message["message"]}
            self.write_message(json.dumps(response))
        else:
            response = {"type":"notification", "message":u"You said: " + message}
            self.write_message(json.dumps(response))

    def on_close(self):
        print("WebSocket closed")

settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret":"yumyumc00k135",
    "xsrf_cookies": True,
}

application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/chat/([^/]+)", RoomHandler),
    (r"/connect", ChatWebSocket),
    
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
#class ChatRoom:
#    def __init__(self, name):
#        self.name = name
#        self.admins = []
#        self.users = []
#
#    def join(self, user):
#        self.users.append(user)
#
#    def make_admin(self, user):
#        if user in self.users:
#            self.admins.append(user)
#
#class User:
#    def __init__(self, name, socket):
#        self.name = name
#        self.socket = socket
#        
#    def send_message(self, message):
#        self.socket.send(message)
