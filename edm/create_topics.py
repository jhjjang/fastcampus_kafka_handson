#!/usr/bin/env python3
from confluent_kafka.admin import AdminClient, NewTopic

conf = {'bootstrap.servers': 'kafka1:19092'}
admin = AdminClient(conf=conf)
admin.create_topics([NewTopic('order', 1, 1), NewTopic('inventory', 1, 1), NewTopic('payment', 1, 1)])
print(admin.list_topics().topics)

