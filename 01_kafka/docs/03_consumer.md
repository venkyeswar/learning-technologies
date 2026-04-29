

```py
from confluent_kafka import Consumer

consumer_config = {
    "bootstrap.servers": 'localhost:9092',
    "group.id": "order-tracker",
    "auto.offset.reset": "earliest"
}

```

## auto.offset.reset 

What to do when there is no initial offset in kafka or if the current offset does not exist any more on the server (eg. because that data has been deleted):

- earliest: automatically reset the offset to the earliest offset.
- latest: automatically reset the offset to the latest offset.
- by_duration: < duration > : automatically reset the offset to a configured < duration > from the current timestamp.
- none: throw exception to the consumer if no previous offset is found for the consumer's group

