from logging.handlers import RotatingFileHandler
import multiprocessing, threading, logging, sys, traceback
import os

handler_list = []
class SmoresFileLog(logging.Handler):
    def __init__(self, name, mode, maxsize=0, backup=1):
        global handler_list
        logging.Handler.__init__(self)
        self._handler = RotatingFileHandler(name, mode, maxBytes=maxsize, backupCount=backup, encoding='UTF-8')
        if self.name not in handler_list:
            handler_list.append(name)
            try:
                self._handler.doRollover()
            except (PermissionError, ValueError):
                pass

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def _format_record(self, record):
        # ensure that exc_info and args have been stringified. Removes any
        # chance of unpickleable things inside and possibly reduces message size
        # sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None
        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self._handler.emit(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self._handler.close()
        logging.Handler.close(self)


class MultiProcessingLog(logging.Handler):

    def __init__(self, name, mode, maxsize=0, backup=1):
        global handler_list
        logging.Handler.__init__(self)
        self._handler = RotatingFileHandler(name, mode, maxBytes=maxsize, backupCount=backup, encoding='UTF-8')
        self.queue = multiprocessing.Queue(-1)
        if self.name not in handler_list:
            handler_list.append(name)
            try:
                self._handler.doRollover()
            except (PermissionError, ValueError):
                pass

        t = threading.Thread(target=self.receive)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while True:
            try:
                record = self.queue.get()
                self._handler.emit(record)
                # print('received on pid {}'.format(os.getpid()))
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s):
        self.queue.put_nowait(s)

    def _format_record(self, record):
        # ensure that exc_info and args have been stringified. Removes any
        # chance of unpickleable things inside and possibly reduces message size
        # sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self._handler.close()
        logging.Handler.close(self)
