import docker
from kafka import KafkaProducer
import json
import re
import time

def fetch_latest_logs_from_docker(container_name, last_position=0):
    """
    Fetch the latest logs from a Docker container starting from the last position.
    """
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        logs = container.logs(stream=False, tail='all').decode('utf-8')  # Fetch all logs
        log_lines = logs.splitlines()  # Split logs into lines
        new_logs = log_lines[last_position:]  # Get new logs since last position
        return new_logs, len(log_lines)  # Return new logs and updated last position
    except Exception as e:
        print(f"Error fetching logs from {container_name}: {e}")
        return [], last_position

def parse_nginx_log(log_line):
    """Parse Nginx log line into JSON format."""
    log_pattern = (
        r'(?P<ip>[\d.]+) - - '
        r'\[(?P<timestamp>[^\]]+)\] '
        r'"(?P<request_method>\w+) (?P<url>[^\s]+) (?P<http_version>[^"]+)" '
        r'(?P<status_code>\d+) (?P<response_size>\d+) '
        r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
    )
    match = re.match(log_pattern, log_line)
    if match:
        return match.groupdict()
    else:
        return {"raw_log": log_line}

def send_logs_to_kafka(logs, topic, kafka_bootstrap_server='localhost:9092'):
    """Send logs to a Kafka topic."""
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_server,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    for log in logs:
        log_entry = parse_nginx_log(log)  # Parse log line into JSON
        print(log_entry)
        producer.send(topic, log_entry)
    producer.flush()
    print(f"Logs successfully sent to Kafka topic: {topic}")

if __name__ == "__main__":
    # Docker container name for the Nginx load balancer
    container_name = "nginx_load_balancer"  # Replace with your Nginx container name
    
    # Kafka topic name
    kafka_topic = "RAWLOGS"
    
    # Last log position
    last_position = 0
    
    # Infinite loop to fetch logs every 5 seconds
    try:
        while True:
            # Fetch the latest logs
            logs, last_position = fetch_latest_logs_from_docker(container_name, last_position)
            if logs:
                print(f"Fetched {len(logs)} new logs from {container_name}.")
                # Send logs to Kafka
                send_logs_to_kafka(logs, kafka_topic)
            else:
                print(f"No new logs found for container: {container_name}.")
            
            # Wait for 5 seconds before fetching logs again
            time.sleep(5)
    except KeyboardInterrupt:
        print("Log fetching stopped by user.")
