import threading
import time


class Manager:
    def __init__(self, queue, listen_delay=0.1):
        self.queue = queue            # data queue: ('key', 'data')
        self.handlers = {}            # func dict: {'key': handleFunc}
        self.else_handler = None      # to be used if non of the events suit the package
        self.threads = []             # a thread to execute a request
        self.listen_status = False    # a key that controls the listening cycle. If False - cycle stops
        self.listen_delay = listen_delay
        self.listen_thread = None

    def bind(self, event, handler):
        self.handlers[event] = handler

    def bind_else(self, handler):
        self.else_handler = handler

    def run(self):
        self.listen_status = True
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def listen(self):
        while self.listen_status:

            if not self.queue.empty():  # else -> sleep
                data = self.queue.get()
                event, package = data

                if event in self.handlers:
                    new_thread = threading.Thread(target=self.handlers[event], args=(package,))
                    new_thread.start()
                    self.threads.append(new_thread)

                else:
                    if self.else_handler:
                        self.else_handler(package)

            time.sleep(self.listen_delay)

    def stop(self):
        self.listen_status = False