
__all__ = ["CyclicJob"]

import threading
import logging
logger = logging.getLogger(f'core.{__name__}')

_thread_list:list[threading.Thread]=[]

class CyclicJob(threading.Thread):
    
    def __init__(self, target, interval:float, *args,  name="CyclicJob", daemon=True, stop_event=None, **kwargs):
        threading.Thread.__init__(self, name=name, daemon=daemon)
        self.daemon = daemon
        if stop_event is None:
            self.stopped_event = threading.Event()
        else:
            self.stopped_event = stop_event
        self.interval = interval
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.name = f'{self.name}-CyclicJob'
        _thread_list.append(self)

    def stop(self):
        logger.debug(f'Stop {self.name}')
        self.stopped_event.set()
        self.join(timeout=1)

    def run(self):
        logger.debug(f'Start {self.name} for {self.target}, To be called every {self.interval}s')
        while not self.stopped_event.wait(timeout=self.interval):
            try :
                self.target(*self.args, **self.kwargs)
            except RuntimeError as runtime_err :
                logger.exception(f'{runtime_err}')

if __name__ == "__main__":
    
    pass