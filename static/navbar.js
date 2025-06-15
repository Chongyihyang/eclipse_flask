function sleep(ms) {
return new Promise(resolve => setTimeout(resolve, ms));
}

function hidebar(text, show_style) {
    try {
        document.getElementsByClassName(text)[0].style.display = show_style;
    } catch (error) {
        
    }
}   

function showMenu() {
    let navLinks = document.getElementById("navLinks");
    navLinks.style.right = "0";
    hidebar("tox-editor-header", "none");
    hidebar("tox-toolbar--scrolling", "none");
}

function hideMenu() {
    let navLinks = document.getElementById("navLinks");
    navLinks.style.right = "-200px";
    sleep(500).then(() => { 
        hidebar("tox-editor-header", "block");
        hidebar("tox-toolbar--scrolling", "block");
    });
}

function show_hide() {
    var click = document.getElementById("list-items");
    if (click.style.display === "none") {
        click.style.display = "block";
    } else if (click.style.display === "block") {
        click.style.display = "none";
    } else {
        click.style.display = "block";
    }
}