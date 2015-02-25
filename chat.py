class Room:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.admins = []
        self.users = []

    def __contains__(self, user):
        return user in self.users

    # Remove a user from room
    def leave(self, user):
        if user in self.users:
            self.users.remove(user)
        if user in self.admins:
            self.admins.remove(user)

    def make_admin(self, user):
        if user not in self.users:
            self.users.append(user)
        if user not in self.admins:
            self.admins.append(user)

    # send a message to all users in the room
    def send_all(self, message):
        for user in self.users:
            user.socket.write_message(message)

    # send a message to all users but one
    def send_all_but(self, message, this_user):
        for user in filter(lambda x : x != this_user, self.users):
            user.socket.write_message(message)

    def add_user(self, user):
        if user not in self.users:
            self.users.append(user)



class User:
    def __init__(self, name):
        self.name = name
        self.socket = None
        self.rooms = []
        self.connected = False

    def __str__(self):
        return self.name + ":" + str(self.socket)
        
    def send_message(self, message):
        self.socket.write_message(message)

    def disconnect(self):
        for room in self.rooms:
            room.leave(self)

    def join(self, room):
        if room not in self.rooms:
            self.rooms.append(room)
        room.add_user(self)
