var term = new Terminal({
  cols : 80,
  rows : 25,
  useStyle : true,
  screenKeys : true,
  cursorBlink : false,
  scrollback : 1000
});
term.on('title', function(title) { document.title = title; });
term.open(document.getElementById("terminal-area"));
term.write('\x1b[31mConnecting...\x1b[m\r\n');

function getId() { return window.location.search.substr(1); }
var ref =
    new Wilddog("https://jamesits-terminal-duplicator.wilddogio.com/sessions/" +
                getId() + "/");
var History = ref.child('history');
a = [];

(getHistory = function(start) {
  var _datetime = start;
  History.orderByChild("timestamp")
      .startAt(start)
      .limitToFirst(500)
      .once("value",
            function(snapshot) {
              snapshot.forEach(function(snap) {
                _datetime = snap.val().timestamp;
                historyReceivedCallback(snap.val());
              });
              if (_datetime !== start) {
                getHistory(_datetime);
              } else {
                historyWatcher(_datetime);
              }

            },
            function(errorObject) {
              console.log("The read failed: " + errorObject.code);
            });
  return _datetime;
})();

function historyWatcher(time) {
  History.orderByChild("timestamp")
      .startAt(time)
      .on("child_added",
          function(snapshot) { historyReceivedCallback(snapshot.val()) },
          function(errorObject) {
            console.log("The read failed: " + errorObject.code);
          });
}

function historyReceivedCallback(data) {
  document.getElementById("delay").innerHTML =
      Date.now() / 1000 - data.timestamp;
  if (!data.is_control_frame) {
    term.write(data.raw_content);
  } else {
    // console.log(data);
    // we can do nothing about it
  }
}
