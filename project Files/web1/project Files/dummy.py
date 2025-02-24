from cassandra.cluster import Cluster

try:
    cluster = Cluster(['127.0.0.1'], port=9042)
    session = cluster.connect()
    print("Connected to Cassandra successfully!")
except Exception as e:
    print(f"Error connecting to Cassandra: {e}")
finally:
    cluster.shutdown()
