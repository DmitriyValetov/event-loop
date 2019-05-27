from multiprocessing import Process, Queue
from contextlib import redirect_stdout
import unittest
import logging
import time
import io

from manager import Manager

logging.basicConfig(level=logging.INFO)


def logger_handler(data):
    time.sleep(1)
    logging.info("received and processed by logger_handler: {}".format(data))


def logger_handler2(data):
    time.sleep(1)
    logging.info("received and processed by logger_handler2: {}".format(data))


def pulsar(queue, delta):
    while True:
        time.sleep(delta)
        queue.put(('logthis', 'some strings'))


def test_with_a_process():
    queue = Queue()
    queue.put(('logthis', 'init message'))

    manager = Manager(queue)
    manager.bind('logthis', logger_handler)
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
        manager.listen_thread.join()
        print('all stop')


def test_add_handler_in_runtime():
    queue = Queue()

    manager = Manager(queue)
    manager.bind('stdout', logger_handler)
    manager.run()

    queue.put(('stdout', 'init message'))

    time.sleep(5)
    manager.bind('stdout2', logger_handler2)
    time.sleep(2)
    queue.put(('stdout2', 'send to stdout2 in runtime'))

    time.sleep(5)
    print('ending')
    manager.stop()


class TestManager(unittest.TestCase):
    def test_init(self):
        data_queue = Queue()
        listen_delay = 1.0
        manager = Manager(data_queue, listen_delay)

        self.assertTrue(manager.queue is data_queue)
        self.assertTrue(manager.else_handler is None)
        self.assertTrue(isinstance(manager.handlers, dict))
        self.assertTrue(len(manager.handlers) == 0)
        self.assertTrue(manager.listen_status is False)
        self.assertTrue(manager.listen_delay == listen_delay)
        self.assertTrue(manager.listen_thread is None)

    def test_bind(self):
        data_queue = Queue()
        listen_delay = 1.0
        manager = Manager(data_queue, listen_delay)

        def logger_handler(data):
            time.sleep(1)
            print("received and processed by logger_handler: {}".format(data))

        manager.bind('msg', logger_handler)
        self.assertTrue(manager.handlers['msg'] is logger_handler)

        def else_logger_handler(data):
            time.sleep(1)
            print("received and processed by else_logger_handler: {}".format(data))

        manager.bind_else(else_logger_handler)
        self.assertTrue(manager.else_handler is else_logger_handler)

    def test_integral(self):

        f = io.StringIO()
        with redirect_stdout(f):

            def processor_1(data):
                return "received and processed by logger_handler: {}".format(data)

            def logger_handler(data):
                print(processor_1(data))

            def processor_else(data):
                return "received and processed by else_logger_handler: {}".format(data)

            def else_logger_handler(data):
                print(processor_else(data))

            def getBytesString(data):
                buffer = io.StringIO(newline='')
                buffer.write(data)
                result = buffer.getvalue()
                buffer.close()
                return result

            data_queue = Queue()
            listen_delay = 1.0
            manager = Manager(data_queue, listen_delay)
            manager.bind('msg', logger_handler)
            manager.bind_else(else_logger_handler)
            manager.run()

            self.assertTrue(manager.listen_status is True)
            self.assertTrue(manager.listen_thread is not None)
            self.assertTrue(manager.handlers['msg'] is logger_handler)
            self.assertTrue(manager.else_handler is else_logger_handler)

            msg_mark = 'msg'
            data_1 = 'some data'
            self.assertTrue(msg_mark in manager.handlers.keys())
            data_queue.put((msg_mark, data_1))
            time.sleep(listen_delay*2)
            got_stdout = f.getvalue()   # get stdout
            f.truncate(0)               # clear buffer
            f.seek(0)                   # clear buffer
            self.assertEqual(got_stdout, processor_1(data_1)+'\n')

            msg_mark_else = 'unregistered post mark'
            self.assertTrue(msg_mark_else not in manager.handlers.keys())
            data_else = 'some data for else'
            data_queue.put((msg_mark_else, data_else))
            time.sleep(listen_delay*2)
            got_stdout = f.getvalue()   # get stdout
            to_compare = processor_else(data_else)+'\n'
            f.truncate(0)               # clear buffer
            f.seek(0)                   # clear buffer
            self.assertEqual(len(got_stdout), len(to_compare))

            manager.stop()
            self.assertEqual(manager.listen_status, False)


    def test_bind_in_runtime(self):

        f = io.StringIO()
        with redirect_stdout(f):

            def processor_1(data):
                return "received and processed by logger_handler: {}".format(data)

            def logger_handler(data):
                print(processor_1(data))

            def processor_else(data):
                return "received and processed by else_logger_handler: {}".format(data)

            def else_logger_handler(data):
                print(processor_else(data))

            def getBytesString(data):
                buffer = io.StringIO(newline='')
                buffer.write(data)
                result = buffer.getvalue()
                buffer.close()
                return result

            data_queue = Queue()
            listen_delay = 1.0
            manager = Manager(data_queue, listen_delay)
            manager.run()
            manager.bind('msg', logger_handler)
            manager.bind_else(else_logger_handler)

            self.assertTrue(manager.listen_status is True)
            self.assertTrue(manager.listen_thread is not None)
            self.assertTrue(manager.handlers['msg'] is logger_handler)
            self.assertTrue(manager.else_handler is else_logger_handler)

            msg_mark = 'msg'
            data_1 = 'some data'
            self.assertTrue(msg_mark in manager.handlers.keys())
            data_queue.put((msg_mark, data_1))
            time.sleep(listen_delay*2)
            got_stdout = f.getvalue()   # get stdout
            f.truncate(0)               # clear buffer
            f.seek(0)                   # clear buffer
            self.assertEqual(got_stdout, processor_1(data_1)+'\n')

            msg_mark_else = 'unregistered post mark'
            self.assertTrue(msg_mark_else not in manager.handlers.keys())
            data_else = 'some data for else'
            data_queue.put((msg_mark_else, data_else))
            time.sleep(listen_delay*2)
            got_stdout = f.getvalue()   # get stdout
            to_compare = processor_else(data_else)+'\n'
            f.truncate(0)               # clear buffer
            f.seek(0)                   # clear buffer
            self.assertEqual(len(got_stdout), len(to_compare))

            manager.stop()
            self.assertEqual(manager.listen_status, False)


if __name__ == '__main__':
    # test_add_handler_in_runtime()
    unittest.main()
