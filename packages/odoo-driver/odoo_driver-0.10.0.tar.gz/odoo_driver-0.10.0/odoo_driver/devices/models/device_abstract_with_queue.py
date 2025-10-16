import time
from queue import Queue
from threading import Thread

from .device_abstract import DeviceAbstract
from .device_task import DeviceTask


class DeviceAbstractWithQueue(DeviceAbstract, Thread):
    has_queue = True

    def __init__(self, interface, options, delay=0, max_queue_size=0):
        """Initialize a new Device.
        delay: time between processing two messages, in seconds.
        """
        DeviceAbstract.__init__(self, interface, options)
        Thread.__init__(self)
        self.errored_tasks = []
        self._queue = Queue(max_queue_size)
        self.delay = delay

    @property
    def queue_size(self):
        return self._queue.qsize()

    @property
    def max_queue_size(self):
        return self._queue.maxsize

    @property
    def errored_tasks_qty(self):
        return len(self.errored_tasks)

    # ###########################
    # Thread / Task Section
    # ###########################
    def run(self):
        while True:
            if self._usb_device:
                current_size = self._queue.qsize()
                if current_size:
                    self._logger("INFO", f"Process one of the {current_size} task(s).")
                else:
                    self._logger("INFO", "Waiting for message ...")
                task = self._queue.get(True)
                self._process_task_abstract(task)
                time.sleep(self.delay)
            else:
                time.sleep(1)

    def _process_task_abstract(self, task):
        self._logger("DEBUG", f"Processing task {task.uuid} ...")
        try:
            if self.use_serial:
                with self._get_serial() as serial:
                    self._process_task_serial(serial, task)
            else:
                self._process_task(task)
            if task in self.errored_tasks:
                self.errored_tasks.remove(task)
            self._logger("SUCCESS", f"Task processed. UUID: {task.uuid}.")

        except Exception as e:
            self._logger("ERROR", f"Task {task.uuid}. Error{e}")
            task.error = e
            if task not in self.errored_tasks:
                self._logger("INFO", f"Reenqueing task. UUID: {task.uuid} ...")
                self.errored_tasks.append(task)
                self._queue.put(task)
            if self._usb_device:
                self._interface._hook_usb_device_removed(self._usb_device, e)

    def add_task(self, data):
        if self.max_queue_size:
            while self._queue.qsize() >= self._queue.maxsize:
                self._logger("WARNING", "Removing obsolete task in queue.")
                self._queue.get_nowait()
        task = DeviceTask(data)
        self._queue.put(task)
        self._logger(
            "INFO",
            f"Task Enqueued ({self._queue.qsize()}/{self._queue.maxsize})."
            f" UUID: {task.uuid}",
        )
