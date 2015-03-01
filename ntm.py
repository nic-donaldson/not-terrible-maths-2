import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import json
import chat

users = {}
rooms = {} 
callbacks = {}
user_id = 0

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

class BaseWSHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

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
            if uid not in users:
                self.clear_cookie("user_id")
                self.clear_cookie("username")
                self.redirect("/")
            else:
                self.set_header("Content-Type", "text/plain")
                self.write("Hello " + users[uid].name)

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
        if room_url not in rooms:
            room = chat.Room(room_name, room_url)

            # add to global rooms
            rooms[room_url] = room
        else:
            # room already exists, add user to it
            room = rooms[room_url]

        user.join(room) 
        print("Redirecting to: %s" % ("/chat/" + room_url))
        self.redirect("/chat/%s" % room_url)

class RoomHandler(BaseHandler):
    def get(self, room_url):

        print(room_url)
        room_url = tornado.escape.url_escape(room_url) # this is dumb why do I need this why tornado
        print(room_url)

        if room_url in rooms:
            room = rooms[room_url]
            if not self.current_user or self.current_user and not int(self.get_secure_cookie("user_id")) in users:
                # give guest name and option to set nickname!
                global user_id
                user_id += 1
                user = chat.User("Guest" + str(user_id))
                self.set_secure_cookie("user_id", str(user_id))
                self.set_secure_cookie("username", user.name)
                users[user_id] = user
                user.join(room)

            self.render("room.html", room=room) 
        else:
            self.redirect("/")


class ChatWebSocket(BaseWSHandler):
    def open(self):
        print("WebSocket opened")

        if not self.current_user:
            self.write_message(json.dumps({"type":"error", "message":"Your cookies are not set"}))
            self.close()

        else:
            user_id = int(self.get_secure_cookie("user_id"))
            if user_id in users:
                user = users[user_id]

                # update socket
                user.socket = self

                # announce
                for other_user in user.room.users:
                    user.send_message(json.dumps({"type":"user_join", "user":other_user.name}))
                user.room.send_all_but(json.dumps({"type":"user_join", "user": user.name}), user)



    def on_message(self, message):
        message = json.loads(message)
        user_id = int(self.get_secure_cookie("user_id"))
        user = users[user_id]

        if message["type"] == "chat_message":
            room_name = message["room"]
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
        elif message["type"] == "nickname":
            new_nick = message["nickname"]
            old_nick = user.name
            user.name = new_nick
            response = json.dumps({"type":"new_nick", "old_nick":old_nick, "new_nick":new_nick})
            user.room.send_all(response)

        else:
            json.dumps(response = {"type":"error", "message":u"I don't know what that means, sorry!"})
            self.write_message(response)

    def on_close(self):
        print("Websocket closed")
        # remove user from rooms if not connected
        # remove from users
        if self.current_user and int(self.get_secure_cookie("user_id")) in users:
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
    (r"/chat/([^/]+)$", RoomHandler),
    (r"/connect", ChatWebSocket),
    (r"/checker", UserChecker),
    (r"/debug", Debuggerino),
    
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
