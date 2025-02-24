import docker
from confluent_kafka import Producer
import json
import time

#RAWLOGS


# Kafka Configuration
KAFKA_BROKER = "localhost:9092"  # Update with your Kafka broker address
KAFKA_TOPIC = "RAWLOGS"  # Kafka topic for Nginx logs

# Nginx Containers
CONTAINER_NAMES = ["nginx_load_balancer", "nginx_web1", "nginx_web2", "nginx_web3"]
#CONTAINER_ID = ["9cff25446723", "12452b41440f", "8f573360c275", "1da0faa55a3a"]


# Kafka Producer
producer = Producer({'bootstrap.servers': KAFKA_BROKER})

print("Started")
def fetch_logs_from_containers(client, container_names):
    """
    Fetch logs from Docker containers.

    Args:
        client: Docker client object.
        container_names: List of container names.

    Returns:
        logs: Dictionary with container names as keys and their logs as values.
    """
    logs = {}
    for container_name in container_names:
        try:
            container = client.containers.get(container_name)
            log_content = container.logs(tail=100, stdout=True, stderr=False, since=int(time.time() - 10)).decode("utf-8")
            logs[container_name] = log_content
        except Exception as e:
            print(f"Error fetching logs for container {container_name}: {e}")
    return logs


def send_logs_to_kafka(logs):
    """
    Send logs to Kafka topic.

    Args:
        logs: Logs dictionary (container_name -> log content).
    """
    for container, log_content in logs.items():
        for line in log_content.splitlines():
            try:
                message = {
                    "container": container,
                    "log": line,
                    "timestamp": time.time(),
                }
                producer.produce(KAFKA_TOPIC, json.dumps(message))
                print(f"Sent log from {container}: {line}")
            except Exception as e:
                print(f"Error sending log to Kafka: {e}")
    producer.flush()


def main():
    # Connect to Docker
    client = docker.from_env()

    while True:
        # Fetch logs
        logs = fetch_logs_from_containers(client, CONTAINER_NAMES)
        print(logs)

        # Send logs to Kafka
        send_logs_to_kafka(logs)
        print("End")

        # Sleep for 10 seconds before fetching logs again
        time.sleep(10)


if __name__ == "__main__":
    main()
