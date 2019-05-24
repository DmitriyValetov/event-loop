from multiprocessing import Process, Queue
import threading
import logging
import time
logging.basicConfig(level=logging.INFO)



def loggerHandler(data):
    time.sleep(5)
    logging.info("received and processed by handler: {}".format(data))


class Manager:
    def __init__(self, queue):
        self.queue = queue
        self.handlers = {}
        self.threads = []
        self.key = False

    def bind(self, event, handler):
        self.handlers[event] = handler

    def run(self):
        self.key = True
        self.run_thread = threading.Thread(target=self.listen)
        self.run_thread.start()

    def listen(self):
        while self.key:
            if not self.queue.empty():
                data = self.queue.get()
                event, package = data
                if event in self.handlers:
                    new_thread = threading.Thread(target=self.handlers[event], args=(package,))
                    new_thread.start()
                    self.threads.append(new_thread)
            time.sleep(0.1)

    def stop(self):
        self.key = False


def pulsar(queue, delta):
    while True:
        time.sleep(delta)
        queue.put(('logthis', 'some strings'))


def main():
    queue = Queue()
    queue.put(('logthis', 'init message'))

    manager = Manager(queue)
    manager.bind('logthis', loggerHandler)
    manager.run()

    p = Process(target=pulsar, args=(queue, 2,))
    print(p.is_alive())
    p.start()
    print(p.is_alive())

    try:
        while True:
            command = input()
            if command == 'stop':
                raise KeyboardInterrupt

    except KeyboardInterrupt as e:
        print('start stopping')
        p.terminate()
        manager.stop()
        for th in manager.threads:
            th.join()
        manager.run_thread.join()
        print('all stop')

if __name__ == '__main__':
    main()