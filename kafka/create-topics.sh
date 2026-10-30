#!/bin/sh
set -e

BOOTSTRAP_SERVER="kafka:29092"
KAFKA_TOPICS="/opt/kafka/bin/kafka-topics.sh"

create_topic() {
  topic_name="$1"
  partitions="$2"
  "$KAFKA_TOPICS" --bootstrap-server "$BOOTSTRAP_SERVER" \
    --create --if-not-exists \
    --topic "$topic_name" \
    --partitions "$partitions" \
    --replication-factor 1
}

create_topic events 16
create_topic email 8
create_topic push 20
create_topic email-retry-5s 8
create_topic email-retry-30s 8
create_topic email-retry-5m 8
create_topic push-retry-5s 20
create_topic push-retry-30s 20
create_topic push-retry-5m 20
create_topic events-dlq 3
create_topic email-dlq 3
create_topic push-dlq 3
create_topic user-events 2