var ws;
var url = "ws://localhost:8888/connect";

window.onload = function() {
    ws = new WebSocket(url);

    ws.onopen = function() {
    };

    ws.onmessage = function (evt) {
        console.log(evt.data);
        var message = JSON.parse(evt.data);

        if (message.type === "chat_message") {
            var elem = document.createElement("li");

            var child = document.createElement("div");
            child.className = "user";
            child.innerHTML = message.user;
            elem.appendChild(child);

            child = document.createElement("div");
            child.className = "message";
            render_math_from_message(message.message,child);
            elem.appendChild(child);

            var messagebox = document.getElementById("messagebox");
            messagebox.insertBefore(elem, messagebox.firstChild);

        } else if (message.type === "notification") {
            alert(message.message);
        }
    };

    document.getElementById("msg_form").addEventListener('submit', function (evt) {
        evt.preventDefault();
        send_message();
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

function send_message() {
    var field = document.getElementById("msg");
    ws.send(JSON.stringify({"type":"chat_message", "message":field.value}));
    field.value = "";
}
