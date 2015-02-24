function render_math_from_message(msg, element) {
    // extract math from the message
    var math_re = /\$.*?\$/g; 

    var found;
    var prev_index = 0;

    while (found = math_re.exec(msg)) {

        // insert text
        element.appendChild(document.createTextNode(found.input.substring(prev_index, found.index)));
        prev_index = math_re.lastIndex;

        var elem = document.createElement("div");
        katex.render(found[0].substr(1, found[0].length-2), elem);
        element.appendChild(elem);
    }
}
