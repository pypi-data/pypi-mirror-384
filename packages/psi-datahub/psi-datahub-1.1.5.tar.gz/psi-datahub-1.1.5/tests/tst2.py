
import redis
import logging
import string
import secrets
import pickle

_logger = logging.getLogger(__name__)

class Redis():
    def __init__(self, host="localhost", port=6379, db="0"):
        self.consumer_name = 'datahub'
        self.host, self.port = host, port
        self.db = db
        self.messages = []
        self.aborted = False

    def _generate_random_string(self, length=16):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(characters) for _ in range(length))
        return random_string

    def create_group(self, r, channels):
        group_name = self._generate_random_string(16)
        try:
            pipeline = r.pipeline()
            for channel in channels:
                pipeline.xgroup_create(channel, group_name, mkstream=False)
            pipeline.execute()
        except Exception as e:
            _logger.warning(f"Error creating stream group: {str(e)}")

        return group_name

    def destroy_group(self, r, channels, group_name):
        try:
            pipeline = r.pipeline()
            for channel in channels:
                pipeline.xgroup_destroy(channel, group_name)
            pipeline.execute()
        except Exception as e:
            _logger.warning(f"Error destroying stream group: {str(e)}")

    def run(self, channels):
        with redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=False) as r:
            group_name = self.create_group(r, channels)
            try:
                streams = {channel : ">" for channel in channels}
                while not self.aborted:
                    entries = r.xreadgroup(group_name, self.consumer_name, streams, count=5 * len(channels), block=100)
                    if entries:
                        for stream, messages in entries:
                            processed_ids = []
                            try:
                                for message_id, message_data in messages:
                                    channel = message_data[b'channel'].decode('utf-8')
                                    timestamp = int(message_data[b'timestamp'].decode('utf-8'))
                                    id = int(message_data[b'id'].decode('utf-8'))
                                    data = message_data[b'value']
                                    print (len(data),)
                                    value = pickle.loads(data)
                                    print(id, timestamp, channel, value)
                                    processed_ids.append(message_id)
                            finally:
                                r.xack(stream, group_name, *processed_ids)
            finally:
                self.destroy_group(r, channels, group_name)


if __name__ == '__main__':
    r = Redis("std-daq-build")
    r.run(['channel1', 'channel2', 'channel3'])

