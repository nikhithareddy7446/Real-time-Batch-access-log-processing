
### Real-time & batch access log processing

# Table of Contents

[**Table of Contents:**](#_6liya4y5ikq4) **2**

[**Project Team**](#_u9a9vvb997o9) **3**

[Parts of the project](#_s4hh6fb1qr8g) 3

[**Project Definition**](#_oldc9erfueth) **3**

[Key Concepts](#_i21bry9xynob) 3

[**Project Design:**](#_5ev1scqjh844) **4**

[**Project Implementation:**](#_o0qos2kb2kbb) **4**

[Step 1: Set Up the Web Server Cluster](#_e408mpvph4ds) 4

[1\. Install Web Servers:](#_loat9g7jima5) 4

[2\. Nginx configuration (docker-compose.yml](#_j9l4qyfjxlfz) 4

[HTTP Load Balancer:](#_yopacsubfvpg) 6

[Log Forwarding:](#_2ro7aaa979zx) 6

[Step 2: Install and Configure Kafka](#_3gfx45k68dpi) 7

[1\. Install Kafka:](#_6siqq4shlbwu) 7

[Start Zookeeper and Kafka brokers in the docker](#_yssjmu8tyepz) 8

[Create Kafka Topics:](#_6e5l2xmmwyxy) 8

[Set Up Kafka Producers:](#_crl5kfmasm6v) 8

[Python code to input Nginx Logs to Kafka Topic for every 5 seconds](#_5h9kj79o3bfs) 9

[Configure Kafka consumers' fan-out mode](#_sabbd348toob) 9

[Step 3: Configure Cassandra](#_p18idk7l41ok) 9

[1\. Install Cassandra:](#_ysy1xny2c8il) 9

[Set Up Tables:](#_3swaes1xikgx) 10

[Step 4: Interesting Logs into Cassandra from Kafka Topic](#_9kheq53nez1a) 10

[1\. Kafka Consumer 1 (Raw Logs to Cassandra):](#_ttrs2ksduxhy) 10

[2\. Kafka Consumer 2 (Real-Time Aggregation):](#_7dw3ijqb3eyu) 11

[Step 5: Batch Processing](#_rd37vm6mqoiv) 11

The batch [program that processes the table LOG and produces the N most visited pages:](#_u9veinqm1krn) 11

[**Implementation Limitations:**](#_fmv9qavv4x4w) **11**

[**Project demo and codebase:**](#_80aofgdhrorj) **12**

[**References:**](#_wd5sr4xd1so4) **12**



## Parts of the project

| 1   | configuring Nginx Web servers (3) |
| --- | --- |
|     |     |
| --- | --- |
| 2   | Configuring the Nginx Load balancer |
| --- | --- |
| 3   | Collecting logs from Nginx in JSON Format |
| --- | --- |
| 4   | Configuring Kafka and Zookeper |
| --- | --- |
| 5   | Creating Kafka topic and loading Nginx logs into the Kafka topic. Configure consumer pool fan out mode |
| --- | --- |
| 6   | Configure Cassandra in docker |
| --- | --- |
| 7   | Running Batch script to fetch all the logs from Kafka topic into Cassandra db (Log Table) |
| --- | --- |
| 8   | Fetch live Kafka stream using Kafka streaming and upload the results into the cassandra Results Table |
| --- | --- |

# Project Definition

The project involves designing and implementing a scalable data pipeline for processing web server access logs in batch and real-time. The objective is to calculate the most observed logs in real-time and batch mode over a configurable period. To provide fault tolerance, scalability, and efficiency, the system combines several technologies, including Kafka, Cassandra, and a cluster of replicated web servers.

### **Key Concepts**

1. **Web Server Cluster:** Replicated servers with a load balancer for high availability; logs forwarded to Kafka.
2. **Load Balancer:** Distributes traffic to prevent overload.
3. **Kafka:** Handles log streaming with:
    - **Consumer 1:** Stores raw logs in Cassandra.
    - **Consumer 2:** Aggregates top N pages every P minutes.
4. **Cassandra:** NoSQL database storing raw logs and aggregated results.
5. **Real-Time Processing:** Aggregates visits and stores/displays results instantly.
6. **Batch Processing:** Computes daily top N pages and archives in Cassandra.
7. **Scalability:** Distributed components ensure reliability and traffic handling.

# Project Design

![image alt](https://github.com/nikhithareddy7446/SENG-691-Final-Project/blob/cdf682c332373b0f90194de6b1cc79bd27d7f59b/Project%20Design.jpg?raw=true)

# Project Implementation

This implementation is broken down into specific components, below is the step-by-step implementation.

## Step 1: Set Up the Web Server Cluster

### Install Web Servers

- - Installed multiple instances of NGINX on the docker (Nginx for Windows, n.d.)
    - Configure them to serve static pages (/product1, /product2, etc.).

### Nginx configuration (docker-compose.yml



version: '3.8'

services:

\# Nginx Load Balancer

load_balancer:

image: nginx:latest

container_name: nginx_load_balancer

volumes:

\- ./nginx-load-balancer.conf:/etc/nginx/nginx.conf

ports:

\- "80:80"

depends_on:

\- web1

\- web2

\- web3

\# Web Server 1

web1:

image: nginx:latest

container_name: nginx_web1

volumes:

\- ./web1:/usr/share/nginx/html # Mount custom content for server

expose:

\- "80" # Internal port for load balancer communication

\# Web Server 2

web2:

image: nginx:latest

container_name: nginx_web2

volumes:

\- ./web2:/usr/share/nginx/html

expose:

\- "80"

\# Web Server 3

web3:

image: nginx:latest

container_name: nginx_web3

volumes:

\- ./web3:/usr/share/nginx/html

expose:

\- "80"

### HTTP Load Balancer

- Install and configure **Nginx Load Balancer** to distribute requests across the web servers.(_Best Option to Put Nginx Logs Into Kafka?_, n.d.)
- Example load balancer configuration (nginx-load-balancer.conf)

events {}

http {

upstream backend {

server web1:80;

server web2:80;

server web3:80;

}

server {

listen 80;

location / {

proxy_pass <http://backend>;

proxy_set_header Host $host;

proxy_set_header X-Real-IP $remote_addr;

proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

}

}

}

### Log Forwarding

Configure the web servers to write access logs and forward them directly to Kafka in JSON format .(_Tech Blog: How to Configure JSON Logging in Nginx? - Velebit AI_, n.d.)

log configuration in nginx-load-balancer.conf:

http {

log_format json_combined escape=json

'{ "remote_addr": "$remote_addr", '

'"time_local": "$time_local", '

'"request": "$request", '

'"status": "$status", '

'"body_bytes_sent": "$body_bytes_sent", '

'"http_referer": "$http_referer", '

'"http_user_agent": "$http_user_agent" }';

access_log /var/log/nginx/access.log json_combined;

server {

listen 80;

location / {

root /usr/share/nginx/html;

index index.html;

}

}

}

## Step 2: Install and Configure Kafka

### Install Kafka

- - Configure Kafka and Zookeeper in the docker (kafka-docker-compose.yaml)

version: '3.8'

services:

zookeeper:

image: confluentinc/cp-zookeeper:latest

container_name: zookeeper

environment:

ZOOKEEPER_CLIENT_PORT: 2181

ZOOKEEPER_TICK_TIME: 2000

kafka:

image: confluentinc/cp-kafka:latest

container_name: kafka

ports:

\- "9092:9092"

environment:

KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181

KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092

KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

### Start Zookeeper and Kafka brokers in the docker

docker-compose -f kafka-docker-compose.yml up -d

### Create Kafka Topics

- Create two topics: RAWLOG and PRODUCTS.

kafka-topics.sh --create --topic RAWLOGS --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

kafka-topics.sh --create --topic PRODUCTS --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

### Set Up Kafka Producers

- Configure web servers to send logs to Kafka using a producer script. Example Python Kafka producer:

kafka-console-producer.sh --topic RAWLOGS --bootstrap-server localhost:9092

### Python code to input Nginx Logs to Kafka Topic for every 5 seconds

Input access logs from nginx load balancer docker container to kafka topic "RAWLOGS"  
Can access the code [here](https://drive.google.com/file/d/1aqSvmPVD79z5Vnu60WjI5_S3_RzTQJUP/view?usp=sharing)

<https://drive.google.com/file/d/1aqSvmPVD79z5Vnu60WjI5_S3_RzTQJUP/view?usp=sharing>

### Configure Kafka consumers' fan-out mode

Consumer fan out mode

can acces the code [here](https://drive.google.com/file/d/1tSm4upG9con6joLEjJmpnzs_r3EesVK5/view?usp=sharing)

<https://drive.google.com/file/d/1tSm4upG9con6joLEjJmpnzs_r3EesVK5/view?usp=sharing>



## Step 3: Configure Cassandra

### Install Cassandra

- - Configure Cassandra in the docker

version: '3.8'

services:

cassandra:

image: cassandra:latest

container_name: cassandra

ports:

\- "9042:9042" # Expose Cassandra Query Language (CQL) port

environment:

\- CASSANDRA_CLUSTER_NAME=MyCluster

\- CASSANDRA_NUM_TOKENS=256

\- CASSANDRA_START_RPC=true

volumes:

\- cassandra_data:/var/lib/cassandra # Persistent storage for Cassandra data

networks:

\- cassandra_network

networks:

cassandra_network:

driver: bridge

volumes:

cassandra_data:

### Set Up Tables

- Create namespace and tables inside Cassandra:

Name-space **:** browesrlogs **,** Table: rawlogs

Python code used to create namespace and insert logs into Cassnadra

can acces the code [here](https://drive.google.com/file/d/1VsSS0VwbTvVfcfEq6AN1_QJU4AQXKxly/view?usp=sharing)

<https://drive.google.com/file/d/1VsSS0VwbTvVfcfEq6AN1_QJU4AQXKxly/view?usp=sharing>

## Step 4: Interesting Logs into Cassandra from Kafka Topic

### Kafka Consumer 1 (Raw Logs to Cassandra)

- - Write raw logs to Cassandra.(John, 2021)

<https://drive.google.com/file/d/1VsSS0VwbTvVfcfEq6AN1_QJU4AQXKxly/view?usp=sharing>

### 2. Kafka Consumer 2 (Real-Time Aggregation)

- Process logs for real-time aggregation

Real time streaming using Kafka Streaming.

Took the logs from Kafka Consumer from topic "RAWLOGS" and perform some aggregation and summary operation.

can acces the code [here](https://drive.google.com/file/d/1Nc1jQGQt9MeT9-BVkn73Y4mVOcIwYlWi/view?usp=sharing)

<https://drive.google.com/file/d/1Nc1jQGQt9MeT9-BVkn73Y4mVOcIwYlWi/view?usp=sharing>

## Step 5: Batch Processing

## Batch program that processes the table LOG and produces the N most visited pages

code to perform batch procressing can be seen [here](https://drive.google.com/file/d/1bx9YD3uaMuBRoMgqX2iz4U4eVW7oWj6j/view?usp=sharing)

<https://drive.google.com/file/d/1bx9YD3uaMuBRoMgqX2iz4U4eVW7oWj6j/view?usp=sharing>



# Implementation Limitations

1. Potential storage constraints in Cassandra due to indefinite retention of raw logs.
2. Managing distributed clusters (Kafka, Cassandra, web servers) increases complexity.
3. Risk of data loss in Kafka if replication is not properly configured.
4. Consumer failures may disrupt data ingestion or processing.
5. Complexity in end-to-end testing of the entire pipeline

# Project demo and codebase

# [Final Project Video Demonstration](https://youtu.be/dE1TS0UAGBM)

You Tube Link -<https://youtu.be/dE1TS0UAGBM>

Google Drive Link : <https://drive.google.com/file/d/16Gy3R4CPa7a3WpmgmG120CBVVthijewC/view?usp=sharing>

#

# References

1._nginx for Windows_. (n.d.). <https://nginx.org/en/docs/windows.html>

2\. _Tech Blog: How to configure JSON logging in nginx? - Velebit AI_. (n.d.). Velebit AI. <https://www.velebit.ai/blog/nginx-json-logging/>

3._best option to put Nginx logs into Kafka?_ (n.d.). Stack Overflow. <https://stackoverflow.com/questions/25452369/best-option-to-put-nginx-logs-into-kafka>

4\. John, J. (2021, June 21). _Getting started with Kafka Cassandra Connector_. digitalis.io. <https://digitalis.io/blog/apache-cassandra/getting-started-with-kafka-cassandra-connector/>

5\. _Send real time continuous log data to kafka and consume it_. (n.d.). Stack Overflow. <https://stackoverflow.com/questions/60483120/send-real-time-continuous-log-data-to-kafka-and-consume-it>
