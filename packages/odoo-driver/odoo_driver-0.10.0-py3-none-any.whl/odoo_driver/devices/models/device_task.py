import uuid
from datetime import datetime


class DeviceTask:
    def __init__(self, data):
        self.create_date = datetime.now()
        self.uuid = uuid.uuid4()
        self.data = data
        self.error = False
