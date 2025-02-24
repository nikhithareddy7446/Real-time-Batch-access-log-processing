from cassandra.cluster import Cluster
import random
from datetime import datetime, timedelta
import uuid
import json

# Function to generate random log entry
def generate_log_entry():
    ip_base = "172.19.0."
    log_entry = {
        "id": uuid.uuid4(),  # Generate a unique ID for each log entry
        "ip": f"{ip_base}{random.randint(1, 255)}",
        "timestamp": (datetime.utcnow() - timedelta(seconds=random.randint(0, 86400))).strftime('%d/%b/%Y:%H:%M:%S +0000'),
        "request_method": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "url": random.choice(["/", "/home", "/about", "/contact", "/api/data"]),
        "http_version": "HTTP/1.1",
        "status_code": str(random.choice([200, 404, 500, 302])),
        "response_size": str(random.randint(50, 1500)),
        "referrer": random.choice(["-", "https://example.com"]),
        "user_agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/117.0 Safari/537.36"
        ])
    }
    return log_entry

# Connect to Cassandra
def connect_to_cassandra():
    cluster = Cluster(['127.0.0.1'], port=9042)  # Adjust IP if Cassandra is running elsewhere
    session = cluster.connect()
    session.set_keyspace('web_logs')  # Ensure the keyspace exists
    return session

# Insert data into Cassandra
def insert_log_entry(session, log_entry):
    query = """
    INSERT INTO logs (id, ip, timestamp, request_method, url, http_version, status_code, response_size, referrer, user_agent)
    VALUES (%(id)s, %(ip)s, %(timestamp)s, %(request_method)s, %(url)s, %(http_version)s, %(status_code)s, %(response_size)s, %(referrer)s, %(user_agent)s)
    """
    session.execute(query, log_entry)

# Main function
def main():
    session = connect_to_cassandra()

    # Generate and insert 100 random log entries
    for _ in range(100):
        log_entry = generate_log_entry()
        insert_log_entry(session, log_entry)
        print(json.dumps(log_entry, indent=4))  # Print each entry in JSON format

if __name__ == "__main__":
    main()
