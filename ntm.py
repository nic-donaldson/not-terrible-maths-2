import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import json
import chat

users = {}
rooms = {} 
user_id = 0

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class BaseWSHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class Debuggerino(BaseHandler):
    def get(self):
        self.write(str(users) + '\n' + str(rooms) + '\n' + str(user_id))

class UserChecker(BaseHandler):
    def get(self):
        if not self.current_user:
            self.write("nup")
        else:
            self.write("yup")

class HomeHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("home.html") 
        else:
            self.set_header("Content-Type", "text/plain")
            self.write("fark")

    def post(self):
        # create user
        user = chat.User(
                tornado.escape.xhtml_escape(self.get_body_argument("username")),
                None
        )
        # give user id
        global user_id
        user_id += 1
        self.set_secure_cookie("user_id", str(user_id))
        self.set_secure_cookie("username", tornado.escape.xhtml_escape(self.get_body_argument("username")))

        users[user_id] = user

        # create room if room does not exist
        room_name = tornado.escape.url_escape(self.get_body_argument("room_name"))
        if room_name not in rooms:
            room = chat.Room(
                    tornado.escape.url_escape(self.get_body_argument("room_name"))
            )
            # set user as admin of room
            room.admins.append(user)
            rooms[room_name] = room
        else:
            # room already exists, add user to it
            room = rooms[room_name]

        user.rooms.append(room)
        room.users.append(user)
        self.redirect("/chat/"+room_name)

class RoomHandler(BaseHandler):
    def get(self, room_name):
        room = rooms[room_name]
        self.render("room.html", room=room) 

class ChatWebSocket(BaseWSHandler):
    def open(self):
        print("WebSocket opened")

        if not self.current_user:
            self.write_message(json.dumps({"type":"notification", "message":"no nickname found"}))
            self.close()
        else:
            # save socket
            user = users[int(self.get_secure_cookie("user_id"))]
            user.socket = self

            # announce new user to all rooms they're in
            response = {"type":"new_user", "user":user.name}
            for room in user.rooms:
                room.send_all_but(json.dumps(response), user)



    def on_message(self, message):
        message = json.loads(message)

        if message["type"] == "chat_message":
            room_name = message["room"]
            user_id = int(self.get_secure_cookie("user_id"))
            user = users[user_id]
            room = rooms[room_name]

            if user not in room:
                response = {"type":"notification", "message":"you are not in this room"}
                self.write_message(json.dumps(response))
                self.close()
            else:
                print("(%s) %s: %s" % (room_name, user.name, message["message"]))
                # send message to everyone in room!
                response = {"type":"chat_message", "user":user.name, "message":message["message"]}
                for other_user in room.users:
                    other_user.socket.write_message(json.dumps(response))
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
    (r"/checker", UserChecker),
    (r"/debug", Debuggerino),
    
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
