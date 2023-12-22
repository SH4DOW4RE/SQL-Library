function load() {
    var textInput = document.getElementById('query');
    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            document.getElementById('query-frm').submit();
        }
    });

    document.getElementById('connect-frm').addEventListener("submit", function(event) {
        event.preventDefault();
    })
}

function showPass() {
    var x = document.getElementById("password");
    var bt = document.getElementById("button");

    if (x.type === "password") {
        x.type = "text";
        bt.innerHTML = '<i class="gg-eye"></i>';
    } else {
        x.type = "password";
        bt.innerHTML = '<i class="gg-eye-alt"></i>';
    }
}
