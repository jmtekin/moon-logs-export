import time
import logging
import datetime
from contextlib import ExitStack
import os
import socket

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter
)
from opentelemetry.sdk._logs import (
    LogEmitterProvider,
    LoggingHandler,
    set_log_emitter_provider,
)
from opentelemetry.sdk._logs.export import BatchLogProcessor
from opentelemetry.sdk.resources import Resource

logs_to_tail = ['ex1.log', 'ex2.log']
host = "127.0.0.1"
port = 4317


class PropagatedLogRecord(logging.LogRecord):
    def __init__(self, line, **kwargs):

        line = line.split(' ')

        ts = line[0]
        level = line[1]
        msg = line[2]

        super().__init__(name=None, level=-1, pathname=None, lineno=None,
            msg=msg, args=None, exc_info=None, func=None, sinfo=None, **kwargs)
        self.created = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
        self.levelname = level

class Follower:
    def __init__(self, logfile):
        self.logfile = logfile
        self.filename = self.logfile.name.split('.')[0]
        try:
            with open(f'latestline-{self.filename}.txt', "r") as latestline:
                start = latestline.readline()
                for line in logfile:
                    if (line == start):
                        break
        except (FileNotFoundError):
            logfile.seek(0, os.SEEK_END)


    def propagate_line(self):
        line = self.logfile.readline()
        
        # if file hasn't been updated
        if not line:
            return 1

        with open(f'latestline-{self.filename}.txt', "w") as latestline:
            latestline.write(line)
        
        print(line)
        handler.emit(PropagatedLogRecord(line))
        return 0


def check_connection():
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #presumably 
    sock.settimeout(2)
    try:
       sock.connect((host,port))
    except:
       return False
    else:
       sock.close()
       return True


if __name__ == '__main__':
    log_emitter_provider = LogEmitterProvider(
        resource=Resource.create(
            {
                "service.name": "moon-logs-export"
            }
        ),
    )
    set_log_emitter_provider(log_emitter_provider)

    exporter = OTLPLogExporter(endpoint=f"{host}:{port}", insecure=True)
    log_emitter_provider.add_log_processor(BatchLogProcessor(exporter))
    log_emitter = log_emitter_provider.get_log_emitter(__name__, "0.1")

    handler = LoggingHandler(logging.NOTSET, log_emitter)

    with ExitStack() as stack:
        logfiles = [stack.enter_context(open(fname)) for fname in logs_to_tail]
        followers = [Follower(logfile) for logfile in logfiles]
        while True:
            not_updated = 0
            for follower in followers:
                if check_connection():
                    not_updated += follower.propagate_line()
                    if not_updated == len(followers):
                        time.sleep(1)
                else:
                    print('Cannot access endpoint. Waiting...')
                    time.sleep(5)
