function load() {
    var textInput = document.getElementById('query');
    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            document.getElementById('query-frm').submit();
        }
    });
}