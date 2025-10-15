import json
import time
import logging

from confluent_kafka import Consumer, Producer, KafkaError

from ..utils.logger import Logging

Logging()


class kafkaComponent:
    def __init__(self, topic, group_id, bootstrap_servers):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe([topic])
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def receive(self):
        try:
            while True:
                logging.info("waiting...")
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        break
                message_content = json.loads(msg.value().decode('utf-8'))
                logging.info(f"接收数据：{message_content}")
                return message_content
        except KeyboardInterrupt:
            pass

    def send(self, topic, message, max_retries=3, retry_delay=1):
        attempts = 0
        while attempts < max_retries:
            delivery_success = False

            def delivery_report(err, msg):
                nonlocal delivery_success
                if err is not None:
                    logging.error(f"Message delivery failed: {err}")
                else:
                    logging.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
                    delivery_success = True

            self.producer.produce(topic, json.dumps(message, ensure_ascii=False), callback=delivery_report)
            self.producer.flush()

            while self.producer.poll(0):
                pass

            if delivery_success:
                logging.info("is3_kafka 消息发送成功！")
                return

            attempts += 1
            time.sleep(retry_delay)

        logging.error("Maximum retry attempts reached. Message delivery failed.")
