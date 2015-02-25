class Room:
    def __init__(self, name):
        self.name = name
        self.admins = []
        self.users = []

    def __contains__(self, user):
        return user in self.users

    def join(self, user):
        self.users.append(user)

    def make_admin(self, user):
        if user in self.users:
            self.admins.append(user)

    def send_all(self, message):
        for user in self.users:
            user.socket.write_message(message)

    def send_all_but(self, message, this_user):
        for user in filter(lambda x : x != this_user, self.users):
            user.socket.write_message(message)

class User:
    def __init__(self, name, socket):
        self.name = name
        self.socket = socket
        self.rooms = []

    def __str__(self):
        return self.name + ":" + str(self.socket)
        
    def send_message(self, message):
        self.socket.write_message(message)
