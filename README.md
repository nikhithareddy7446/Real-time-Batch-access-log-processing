

# Real-time & batch access log processing


## TableofContents:.......................................................................................................................

## Tableof Contents:

- TableofContents:.......................................................................................................................
- ProjectTeam................................................................................................................................
   - Partsoftheproject...................................................................................................................
- ProjectDefinition.........................................................................................................................
      - KeyConcepts.....................................................................................................................
- ProjectDesign:............................................................................................................................
- ProjectImplementation:..............................................................................................................
   - Step1:SetUptheWebServerCluster...................................................................................
      - 1.InstallWebServers:.......................................................................................................
      - 2.Nginxconfiguration(docker-compose.yml.....................................................................
      - HTTPLoadBalancer:........................................................................................................
      - LogForwarding:.................................................................................................................
   - Step2:InstallandConfigureKafka.........................................................................................
      - 1.InstallKafka:..................................................................................................................
      - StartZookeeperandKafkabrokersinthedocker.............................................................
      - CreateKafkaTopics:..........................................................................................................
      - SetUpKafkaProducers:...................................................................................................
      - PythoncodetoinputNginxLogstoKafkaTopicforevery 5 seconds...............................
      - ConfigureKafkaconsumers'fan-outmode........................................................................
   - Step3:ConfigureCassandra..................................................................................................
      - 1.InstallCassandra:..........................................................................................................
      - SetUpTables:..................................................................................................................
   - Step4:InterestingLogsintoCassandrafromKafkaTopic....................................................
      - 1.KafkaConsumer 1 (RawLogstoCassandra):............................................................
      - 2.KafkaConsumer 2 (Real-TimeAggregation):..............................................................
   - Step5:BatchProcessing.......................................................................................................
   - ThebatchprogramthatprocessesthetableLOGandproducestheNmostvisitedpages:.
- ImplementationLimitations:.....................................................................................................
- Projectdemoandcodebase:....................................................................................................
- References:................................................................................................................................



### Partsoftheproject...................................................................................................................

```
1 configuringNginxWebservers(3)
```
```
2 ConfiguringtheNginxLoadbalancer
3 CollectinglogsfromNginxinJSONFormat
4 ConfiguringKafkaandZookeper
5 CreatingKafkatopicandloadingNginxlogsintotheKafkatopic.Configure
consumerpoolfanoutmode
6 ConfigureCassandraindocker
7 RunningBatchscripttofetchallthelogsfromKafkatopicintoCassandradb(Log
Table)
8 FetchliveKafkastreamusingKafkastreaminganduploadtheresultsintothe
cassandraResultsTable
```
## ProjectDefinition.........................................................................................................................

Theprojectinvolvesdesigningandimplementingascalabledatapipelineforprocessingweb
serveraccesslogsinbatchandreal-time.Theobjectiveistocalculatethemostobservedlogs
inreal-timeandbatchmodeoveraconfigurableperiod.Toprovidefaulttolerance,scalability,
andefficiency,thesystemcombinesseveraltechnologies,includingKafka,Cassandra,anda
clusterofreplicatedwebservers.

#### KeyConcepts.....................................................................................................................

1. **WebServerCluster:** Replicatedserverswithaloadbalancerforhighavailability;logs
    forwardedtoKafka.
2. **LoadBalancer:** Distributestraffictopreventoverload.
3. **Kafka:** Handleslogstreamingwith:
    ○ **Consumer1:** StoresrawlogsinCassandra.
    ○ **Consumer2:** AggregatestopNpageseveryPminutes.


4. **Cassandra:** NoSQLdatabasestoringrawlogsandaggregatedresults.
5. **Real-TimeProcessing:** Aggregatesvisitsandstores/displaysresultsinstantly.
6. **BatchProcessing:** ComputesdailytopNpagesandarchivesinCassandra.
7. **Scalability:** Distributedcomponentsensurereliabilityandtraffichandling.

## ProjectDesign:............................................................................................................................

## ProjectImplementation:..............................................................................................................

Thisimplementationisbrokendownintospecificcomponents,belowisthestep-by-step
implementation.

### Step1:SetUptheWebServerCluster...................................................................................

#### 1.InstallWebServers:.......................................................................................................

```
○ InstalledmultipleinstancesofNGINX onthedocker(NginxforWindows,n.d.)
○ Configurethemtoservestaticpages(/product1,/product2,etc.).
```

Unset

#### 2.Nginxconfiguration(docker-compose.yml.....................................................................

version: '3.8'

services:
# NginxLoadBalancer
load_balancer:
image:nginx:latest
container_name:nginx_load_balancer
volumes:

- ./nginx-load-balancer.conf:/etc/nginx/nginx.conf
ports:
- "80:80"
depends_on:
- web
- web
- web

```
# WebServer 1
web1:
image:nginx:latest
container_name:nginx_web
volumes:
```
- ./web1:/usr/share/nginx/html # Mountcustom contentfor server
expose:
- "80" #Internal portfor loadbalancercommunication

```
# WebServer 2
web2:
image:nginx:latest
container_name:nginx_web
volumes:
```
- ./web2:/usr/share/nginx/html
expose:
- "80"

```
# WebServer 3
web3:
image:nginx:latest
container_name:nginx_web
volumes:
```
- ./web3:/usr/share/nginx/html


```
Unset
```
```
expose:
```
- "80"

#### HTTPLoadBalancer:........................................................................................................

```
● Installandconfigure NginxLoadBalancer todistributerequestsacrosstheweb
servers.( BestOptiontoPutNginxLogsIntoKafka? ,n.d.)
● Exampleloadbalancerconfiguration(nginx-load-balancer.conf)
```
```
events {}
```
```
http{
upstreambackend{
server web1:80;
server web2:80;
server web3:80;
}
```
```
server{
listen 80;
```
```
location / {
proxy_passhttp://backend;
proxy_set_header Host$host;
proxy_set_header X-Real-IP$remote_addr;
proxy_set_header X-Forwarded-For$proxy_add_x_forwarded_for;
}
}
}
```
#### LogForwarding:.................................................................................................................

ConfigurethewebserverstowriteaccesslogsandforwardthemdirectlytoKafkainJSON
format.( _TechBlog:HowtoConfigureJSONLogginginNginx?-VelebitAI_ ,n.d.)

logconfigurationinnginx-load-balancer.conf:


```
Unset
```
```
Unset
```
```
http{
log_formatjson_combined escape=json
'{"remote_addr":"$remote_addr", '
'"time_local":"$time_local",'
'"request": "$request", '
'"status": "$status",'
'"body_bytes_sent":"$body_bytes_sent",'
'"http_referer": "$http_referer", '
'"http_user_agent":"$http_user_agent" }';
```
```
access_log/var/log/nginx/access.logjson_combined;
```
```
server{
listen 80;
location / {
root/usr/share/nginx/html;
indexindex.html;
}
}
}
```
### Step2:InstallandConfigureKafka.........................................................................................

#### 1.InstallKafka:..................................................................................................................

```
○ ConfigureKafkaandZookeeperinthedocker
(kafka-docker-compose.yaml)
```
```
version: '3.8'
services:
zookeeper:
image:confluentinc/cp-zookeeper:latest
container_name:zookeeper
environment:
ZOOKEEPER_CLIENT_PORT: 2181
ZOOKEEPER_TICK_TIME: 2000
```

```
Unset
```
```
Unset
```
```
Unset
```
```
kafka:
image:confluentinc/cp-kafka:latest
container_name:kafka
ports:
```
- "9092:9092"
environment:
KAFKA_ZOOKEEPER_CONNECT:zookeeper:
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

#### StartZookeeperandKafkabrokersinthedocker.............................................................

```
docker-compose-fkafka-docker-compose.ymlup-d
```
#### CreateKafkaTopics:..........................................................................................................

```
● Createtwotopics:RAWLOGandPRODUCTS.
```
```
kafka-topics.sh--create --topicRAWLOGS--bootstrap-server localhost:
--partitions 3 --replication-factor 1
```
```
kafka-topics.sh--create --topicPRODUCTS --bootstrap-serverlocalhost:
--partitions 3 --replication-factor 1
```
#### SetUpKafkaProducers:...................................................................................................

```
● ConfigurewebserverstosendlogstoKafkausingaproducerscript.ExamplePython
Kafkaproducer:
```
```
kafka-console-producer.sh--topic RAWLOGS--bootstrap-serverlocalhost:
```

```
Python
```
```
Python
```
```
Unset
```
#### PythoncodetoinputNginxLogstoKafkaTopicforevery 5 seconds...............................

```
Input access logs from nginx load balancer docker container to
kafka topic "RAWLOGS"
Can access the code here
https://drive.google.com/file/d/1aqSvmPVD79z5Vnu60WjI5_S3_RzTQJUP/view?usp=shar
ing
```
#### ConfigureKafkaconsumers'fan-outmode........................................................................

```
Consumer fan out mode
can acces the code here
https://drive.google.com/file/d/1tSm4upG9con6joLEjJmpnzs_r3EesVK5/view?usp=shar
ing
```
### Step3:ConfigureCassandra..................................................................................................

#### 1.InstallCassandra:..........................................................................................................

```
○ ConfigureCassandrainthedocker
```
```
version: '3.8'
```
```
services:
cassandra:
image: cassandra:latest
container_name: cassandra
ports:
```
- "9042:9042" # Expose Cassandra Query Language (CQL) port
environment:
- CASSANDRA_CLUSTER_NAME=MyCluster


```
Unset
```
##### - CASSANDRA_NUM_TOKENS=

- CASSANDRA_START_RPC=true
volumes:
- cassandra_data:/var/lib/cassandra # Persistent storage
for Cassandra data
networks:
- cassandra_network

```
networks:
cassandra_network:
driver: bridge
```
```
volumes:
cassandra_data:
```
#### SetUpTables:..................................................................................................................

```
● CreatenamespaceandtablesinsideCassandra:
```
```
Name-space : browesrlogs , Table:rawlogs
```
```
Python codeusedtocreate namespaceandinsert logsintoCassnadra
can accesthe codehere
https://drive.google.com/file/d/1VsSS0VwbTvVfcfEq6AN1_QJU4AQXKxly/view?usp=shar
ing
```
### Step4:InterestingLogsintoCassandrafromKafkaTopic....................................................

#### 1.KafkaConsumer 1 (RawLogstoCassandra):............................................................

```
○ WriterawlogstoCassandra.(John,2021)
```

```
Unset
```
```
Unset
```
```
Unset
```
```
https://drive.google.com/file/d/1VsSS0VwbTvVfcfEq6AN1_QJU4AQXKxly/view?usp=shar
ing
```
#### 2.KafkaConsumer 2 (Real-TimeAggregation):..............................................................

```
● Processlogsforreal-timeaggregation
```
```
RealtimestreamingusingKafka Streaming.
Tookthe logsfromKafkaConsumer fromtopic"RAWLOGS"and performsome
aggregation andsummary operation.
can accesthe codehere
https://drive.google.com/file/d/1Nc1jQGQt9MeT9-BVkn73Y4mVOcIwYlWi/view?usp=shar
ing
```
### Step5:BatchProcessing.......................................................................................................

### BatchprogramthatprocessesthetableLOGandproducestheNmostvisitedpages:

```
codetoperformbatch procressing canbeseenhere
https://drive.google.com/file/d/1bx9YD3uaMuBRoMgqX2iz4U4eVW7oWj6j/view?usp=shar
ing
```
## ImplementationLimitations:.....................................................................................................

1. PotentialstorageconstraintsinCassandraduetoindefiniteretentionofrawlogs.
2. Managingdistributedclusters(Kafka,Cassandra,webservers)increasescomplexity.
3. RiskofdatalossinKafkaifreplicationisnotproperlyconfigured.
4. Consumerfailuresmaydisruptdataingestionorprocessing.
5. Complexityinend-to-endtestingoftheentirepipeline


## Projectdemoandcodebase:....................................................................................................

## Final Project VideoDemonstration

YouTubeLink-https://youtu.be/dE1TS0UAGBM
GoogleDriveLink:
https://drive.google.com/file/d/16Gy3R4CPa7a3WpmgmG120CBVVthijewC/view?usp=sharing

## References:................................................................................................................................

1. _nginxforWindows_ .(n.d.).https://nginx.org/en/docs/windows.html
2. _TechBlog:HowtoconfigureJSONlogginginnginx?-VelebitAI_ .(n.d.).VelebitAI.
https://www.velebit.ai/blog/nginx-json-logging/
3. _bestoptiontoputNginxlogsintoKafka?_ (n.d.).StackOverflow.
https://stackoverflow.com/questions/25452369/best-option-to-put-nginx-logs-into-kafka
4.John,J.(2021,June21). _GettingstartedwithKafkaCassandraConnector_.
digitalis.io.
https://digitalis.io/blog/apache-cassandra/getting-started-with-kafka-cassandra-connecto
r/
5. _Sendrealtimecontinuouslogdatatokafkaandconsumeit_ .(n.d.).StackOverflow.
https://stackoverflow.com/questions/60483120/send-real-time-continuous-log-data-to-ka
fka-and-consume-it


