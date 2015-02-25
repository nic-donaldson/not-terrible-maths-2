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
            # see if user still exists
            uid = int(self.get_secure_cookie("user_id"))
            username = self.get_secure_cookie("username")
            if uid not in users or users[uid].name != username:
                self.clear_cookie("user_id")
                self.clear_cookie("username")
                self.redirect("/")
            else:
                self.set_header("Content-Type", "text/plain")
                self.write("Hello " + username)

    def post(self):

        # create user
        room_name = tornado.escape.xhtml_escape(self.get_body_argument("room_name"))
        room_url = tornado.escape.url_escape(self.get_body_argument("room_name"))
        username = tornado.escape.xhtml_escape(self.get_body_argument("username"))
        user = chat.User(username)

        # give user id
        global user_id
        user_id += 1
        self.set_secure_cookie("user_id", str(user_id))
        self.set_secure_cookie("username", username)

        users[user_id] = user

        # create room if room does not exist
        if room_name not in rooms:
            room = chat.Room(room_name, room_url)

            # add to global rooms
            rooms[room_url] = room
        else:
            # room already exists, add user to it
            room = rooms[room_url]

        user.join(room) 
        self.redirect("/chat/"+room_url)

class RoomHandler(BaseHandler):
    def get(self, room_url):
        if room_url in rooms and self.current_user:
            room = rooms[room_url]
            self.render("room.html", room=room) 
        else:
            self.redirect("/")

class ChatWebSocket(BaseWSHandler):
    def open(self):
        print("WebSocket opened")

        if not self.current_user:
            self.write_message(json.dumps({"type":"notification", "message":"You are not a registered user, do you have cookies enabled?"}))
            self.close()
        else:
            user = users[int(self.get_secure_cookie("user_id"))]

            # update socket
            user.socket = self

            # send list of users to new user
            for other_user in user.room.users:
                response = json.dumps({"type":"user_join", "user":other_user.name})
                user.send_message(response)

            # announce new user
            response = json.dumps({"type":"user_join", "user":user.name})
            user.room.send_all_but(response, user)

    def on_message(self, message):
        message = json.loads(message)

        if message["type"] == "chat_message":
            room_name = message["room"]
            user_id = int(self.get_secure_cookie("user_id"))
            user = users[user_id]
            room = rooms[room_name]

            if user not in room:
                response = json.dumps({"type":"notification", "message":"You are not in this room, disconnecting"})
                self.write_message(response)
                self.close()
            else:
                print("(%s) %s: %s" % (room_name, user.name, message["message"]))
                # send message to everyone in room!
                response = json.dumps({"type":"chat_message", "user":user.name, "message":message["message"]})
                room.send_all(response)
        else:
            json.dumps(response = {"type":"error", "message":u"I don't know what that means, sorry!"})
            self.write_message(response)

    def on_close(self):
        print("Websocket closed")
        # remove user from rooms if not connected
        # remove from users
        if self.current_user:
            user_id = int(self.get_secure_cookie("user_id"))
            user = users[user_id]
            user.socket = None

            user.room.leave(user)

            print("%s disconnected" % (user.name))

            response = json.dumps({"type":"user_leave", "user":user.name, "room":user.room.name})
            user.room.send_all_but(response, user)

            if user_id in users:
                del users[user_id]

settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret":"yumyumc00k135",
    "xsrf_cookies": True,
    "debug": True
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
