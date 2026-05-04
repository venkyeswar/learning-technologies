from confluent_kafka import Consumer

config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-tracker", # instance id-> there may be multiple instances running for customer service
    "auto.offset.reset": "earliest"
}

consumer = Consumer(config)

consumer.subscribe(["orders"])


print("consumer is running and subsribed to order topic")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Error:", msg.error())
            continue
        value = msg.value().decode("utf-8")
        print(f"Received: {value}")
except KeyboardInterrupt:
    print("Key word Exception")

finally:
    consumer.close()