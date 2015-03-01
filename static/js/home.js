window.onload = function() {
    var maths_elements = document.getElementsByClassName("math");
    for (a = 0; a < maths_elements.length; a++) {
        katex.render(maths_elements[a].innerHTML, maths_elements[a]);
    }
};
