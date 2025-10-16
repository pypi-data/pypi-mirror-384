function makeReconnectingWebSocket(path) {
    // https://github.com/pladaria/reconnecting-websocket/issues/91#issuecomment-431244323
    var ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    var ws_path = ws_scheme + '://' + window.location.host + path;
    var socket = new ReconnectingWebSocket(ws_path);
    socket.onclose = function (e) {
        if (e.code === 1011) {
            // this may or may not exist in child pages.
            var serverErrorDiv = document.getElementById("websocket-server-error");
            if (serverErrorDiv) {
                // better to put the message here rather than the div, otherwise it's confusing when
                // you do "view source" and there's an error message.
                serverErrorDiv.innerText = "Server error. Check the server logs or Sentry.";
                serverErrorDiv.style.visibility = "visible";
            }
        }
    };
    return socket;
}

document.addEventListener('DOMContentLoaded', function () {
    let bodyTitle = document.getElementById('_otree-title');
    let bodyTitleText = bodyTitle ? bodyTitle.textContent : '';
    let tabTitle = document.querySelector('title');
    if (bodyTitleText && !tabTitle.textContent) {
        tabTitle.textContent = bodyTitleText;
    }
});
