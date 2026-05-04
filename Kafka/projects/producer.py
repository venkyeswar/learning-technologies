from confluent_kafka import Producer
import uuid
import json
# telling kafka to send events to that endpint

# producer = Producer({"bootstrap.server": "localhost:9092"})


producer_config = {
    "bootstrap.servers": "localhost:9092"
}

producer = Producer(producer_config)

def delivery_report(err, msg): 
    if err:
        print(f"Delivery report error: {err}")
    else:
        print(f"Delivered : {msg.value().decode("utf-8")}")


order = {
    "order_id": str(uuid.uuid4()),
    "user": "venky",
    "item": "mushroom pizza",
    "quantity": 2
}


# need to convert dictionary/object dtype to json
try:
    while True:
        item  = input("Enter Item: ")
        if item == "quite":
            break
        order["item"] = item
        value = json.dumps(order).encode('utf-8')

        # If topics are not present it creats one and stores event
        producer.produce(topic="orders", value=value,
                        callback= delivery_report)
except Exception as e:
    print(e)
finally:
    producer.flush()

