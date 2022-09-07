const Tail = require('tail-file');
const fs = require('fs');
const opentelemetry_api = require("@opentelemetry/api");
const opentelemetry_sdk = require("@opentelemetry/sdk-node");
const {
  getNodeAutoInstrumentations,
} = require("@opentelemetry/auto-instrumentations-node");
const {
  OTLPTraceExporter,
} = require("@opentelemetry/exporter-trace-otlp-http");


const tracer = opentelemetry_api.trace.getTracer(
  'main-tracer'
);

const sdk = new opentelemetry_sdk.NodeSDK({
    traceExporter: new OTLPTraceExporter({
      // optional - url default value is http://localhost:4318/v1/traces
      url: "http://localhost:4317/v1/tracers",
      // optional - collection of custom headers to be sent with each request, empty by default
      headers: {},
    }),
    instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

filename = 'debug.log'


function init_tail(tail){
    tail.on('error', error => {
        
        console.log('Log export failed with error code: ' + error.code)
    });
    
    tail.on('line', line => {
        fs.writeFileSync('latestline.txt', line)
        line = line.split(' ')
        var ts = line[0]
        var ms = line[1]
        tracer.startActiveSpan('log_export', span => {
            span.setAttribute('File', filename);
            span.setAttribute('log.severity', 'info')
            span.setAttribute('log.timestamp', ts)
            span.setAttribute('log.message', ms)
            span.end();
        });

    })

    return tail
}


var tail = init_tail(new Tail(filename))

var found = 1
tail.findStart(/^(.*)/, line => {
    if ( line == fs.readFileSync('latestline.txt').toString() ){
        found = 0
        return 1
    }
    return found
}).catch(err => {
    if (err.code == 'NOTFOUND'){

        console.log(err.code + ": Can't find where I left off. Starting from latest log...")

        delete tail

        var tail = init_tail(new Tail(filename));

        tail.start()
    
    }
})
