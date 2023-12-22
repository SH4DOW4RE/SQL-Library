function load() {
    var textInput = document.getElementById('query');
    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            document.getElementById('query-frm').submit();
        }
    });

    document.getElementById('filters-frm').addEventListener("submit", function(event) {
        event.preventDefault();
    })
}

function send_frm() {
    document.getElementById('filters-frm').submit();
}

function reset_frm(lang) {
    document.getElementById('author').value = "";
    document.getElementById('editor').value = "";
    document.getElementById('av-yes').checked = false;
    document.getElementById('av-no').checked = false;

    if (lang == 'fr') {
        document.getElementById('query-frm').action = "/fr/search";
    } else {
        document.getElementById('query-frm').action = "/search";
    }

    document.getElementById('query-frm').submit();
}

function changePage(direction) {
    let idx = parseInt(document.getElementById('page').value);
    
    if (direction == 'n') {
        idx = parseInt(document.getElementById('page').value) + 1;
    } else if (direction == 'p') {
        idx = parseInt(document.getElementById('page').value) - 1;
    } else {

    }
    if (idx < 0) {
        idx = 0;
    }
    document.getElementById('page').value = idx;

    document.getElementById('filters-frm').submit();
}
