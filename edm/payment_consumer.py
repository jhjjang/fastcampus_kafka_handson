#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import json
import logging

from confluent_kafka import Producer, Consumer

import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def process_consumer(is_pg_api_call_succeeded):
    conf_producer = {'bootstrap.servers': 'kafka1:19092'}
    producer = Producer(conf_producer)
    conf_consumer = {'bootstrap.servers': 'kafka1:19092', 'group.id': 'payment_consumer_group', 'auto.offset.reset': 'earliest'}
    consumer = Consumer(conf_consumer)

    inbound_event_channel = 'payment'
    outbound_success_event_channel = 'order'
    outbound_failure_event_channel = 'inventory'

    try:
        consumer.subscribe([inbound_event_channel])
        while True:
            message = consumer.poll(timeout=3)
            if message is None:
                continue

            event = message.value()
            if event:
                logging.debug(event)
                evt = json.loads(event)
                if is_pg_api_call_succeeded == 'True':
                    evt['status'] = 'PAYMENT_COMPLETE'
                    producer.produce(outbound_success_event_channel, value=json.dumps(evt))
                else:
                    evt['status'] = 'ORDER_CANCEL'
                    producer.produce(outbound_failure_event_channel, value=json.dumps(evt))
            else:
                continue

    finally:
        consumer.close()    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Please put a required argument: is_pg_api_call_succeeded(True/False)")
        sys.exit()

    is_pg_api_call_succeeded = sys.argv[1]

    process_consumer(is_pg_api_call_succeeded)
