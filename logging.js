var fs = require('fs');
var util = require('util');
var logrotate = require('logrotator');

var log_file = fs.createWriteStream(__dirname + '/debug.log', {flags : 'a'});
var log_stdout = process.stdout;

console.log = function(d) { //
  log_file.write(util.format(d) + '\n');
  log_stdout.write(util.format(d) + '\n');
};


// use the global rotator
var rotator = logrotate.rotator;

// or create a new instance
// var rotator = logrotate.create();

// check file rotation every 5 minutes, and rotate the file if its size exceeds 10 mb.
// keep only 3 rotated files and compress (gzip) them.
rotator.register('/var/log/debug.log', {
  schedule: '1m', 
  size: '1k', 
  compress: true, 
  count: 3, 
  format: function(index) {
    var d = new Date();
    return d.getDate()+"-"+d.getMonth()+"-"+d.getFullYear();
  }
});

setInterval(function() {
    time = new Date().toISOString()
    console.log(`${time} ${parseInt(Math.random() * 100)}`)
}, 5000)