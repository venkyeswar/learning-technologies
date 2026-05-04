# Running Kafka
## Run kafka using docker composer
```yaml
version: '3.8'

services:
    kafka:
        image: confluentinc/cp-kafka:7.8.3
        container:name: kafka
        ports:
        - "9092:9092"
        
        environment:
        KAFKA_KRAFT_MODE: 'True'
        CLUSTER_ID: '1L6g7nGhU-eAKfL--X25wo' 
        KAFKA_NODE_ID: 1 

        KAFKA_PROCESS_ROLES: broker, controller #tells the broker that defined in kafka-node will act as broker and controller
        KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
        KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

        KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092, CONTROLLER://0.0.0.0:9093
        KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092

        KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER

        KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
    volumes:
        - kafka_kraft:/var/lib/kafka/data
volumes:
kafka_kraft:


```
## 1. Start a python project

- In the product the kafka will deploy as a cluster (that contains collection of brokers)
- For those brokers there will be one controller broker that makes the following things:
  - Managing the cluster's state
  - Tracking which broker is the leader
  - Reassigning parititons in case o broker failures
  - Handling all the cluster administration tasks.
  - At any given time only one broker is an active controller if the existing controller broker crashes the another broker will take controller role.

  ## Running docker
  - right click on yaml file and run the docker composer

  ## Get kafka terminal

```powershell
  docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# To get details of topics in depth
docker exec -it kafka kafka-topics  --bootstrap-server localhost:9092 --describe --topic orders

# to get list of events
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders --from-beginning

```

