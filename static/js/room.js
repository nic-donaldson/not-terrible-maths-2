var ws;
var port = 8888;
var room = "";
var users = [];


window.onload = function() {
    if (document.location.hostname != "") {
        ws = new WebSocket('ws://' + document.location.hostname + ':' + port + '/connect', []);
    } else {
        ws = new WebSocket('ws://localhost:' + port + '/connect', []);
    }

    ws.onopen = function() {
        // get room name
        var room_re = /\/([^\/]*)$/;
        room = room_re.exec(window.location)[1];
    };

    ws.onmessage = function (evt) {
        console.log(evt.data);
        var message = JSON.parse(evt.data);

        if (message.type === "chat_message") {
            receive_message(message);
        } else if (message.type === "user_join") {
            user_join(message);
        } else if (message.type === "user_leave") {
            user_leave(message);
        } else if (message.type === "new_nick") {
            new_nick(message);
        } else if (message.type === "notification") {
            alert(message.message);
        }
    };

    document.getElementById("msg_form").addEventListener('submit', function (evt) {
        evt.preventDefault();
        send_message();
    });

    document.getElementById("nick_form").addEventListener('submit', function(evt) {
        evt.preventDefault();
        set_nickname();
    });
}

function render_math_from_message(msg, element, clear) {

    if (clear === true) {
        element.innerHTML = "";
    }

    // extract math from the message
    var math_re = /\$.*?\$/g; 

    var found;
    var prev_index = 0;

    while (found = math_re.exec(msg)) {

        // insert text
        element.appendChild(document.createTextNode(msg.substring(prev_index, found.index)));
        prev_index = math_re.lastIndex;

        var elem = document.createElement("div");
        elem.className = "math";
        katex.render(found[0].substr(1, found[0].length-2), elem);
        element.appendChild(elem);
    }

    // insert any leftover text
    element.appendChild(document.createTextNode(msg.substring(prev_index, msg.length)));
}

function set_nickname() {
    var field = document.getElementById("nick");
    ws.send(JSON.stringify({"type":"nickname", "nickname":field.value}));
}

function send_message() {
    var field = document.getElementById("msg");
    var msg = field.value;
    if (msg !== "") {
        ws.send(JSON.stringify({"type":"chat_message", "room":room, "message":field.value}));
        field.value = "";
    }
}

function receive_message(message) {
    var elem = document.createElement("li");

    var child = document.createElement("div");
    child.className = "user";
    child.innerHTML = message.user;
    elem.appendChild(child);

    child = document.createElement("div");
    child.className = "message";
    render_math_from_message(message.message,child);
    elem.appendChild(child);

    var messagebox = document.getElementById("messages");
    messagebox.insertBefore(elem, messagebox.firstChild);
}

function user_join(message) {
    var user = message.user;
    users.push(user);

    var elem = document.createElement("li");
    elem.id = "user:" + user
    elem.appendChild(document.createTextNode(user));

    var userbox = document.getElementById("userlist");
    userbox.appendChild(elem);
}

function user_leave(message) {
    var user = message.user;
    var index = users.indexOf(message.user);
    if (index > -1) {
        users.splice(index, 1);
    }

    var elem = document.getElementById("user:"+user);
    elem.parentNode.removeChild(elem);
}

function new_nick(message) {
    var old_nick = message.old_nick;
    var new_nick = message.new_nick;

    var elem = document.getElementById("user:" + old_nick);
    elem.innerHTML = new_nick;
    elem.id = "user:" + new_nick;
}
