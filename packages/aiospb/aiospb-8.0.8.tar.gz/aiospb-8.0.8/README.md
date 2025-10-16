# Async Sparkplug B

Asyncronous implementation in python of the Sparkplug B standard for MQTT protocol


## Test and Deploy

In the  cicd directory you have scripts for helping the test of the library. It is necessary to have docker-compose and docker installed to run locally a Mqtt Broker and run integration and acceptance tests.

- run-all-tests.sh: Run all the tests
- setup-environment.sh: Open a mosquitto MQTT broker in a container to develop the test. It will clear all active containers.
- teardown-environment.sh: Close environment of testing (only the affected)

## Architecture

The application runs asyncronously some tasks:

- ~scanner~: runs the scanning proccess of the metrics.
- ~commands~: listen to commands and 

### Edge Node

The edge node has been implemented under a state machine pattern. These are the states and transitions of edge node objects:

1. `Disconnected`: Initial state, until the client has not established a session and it is not connected to mqtt server, the scanning process is not started. If the client establish a session but conne
   - `establish_session`: kj fskkk
2. `Online`: The edge node is scanning and sending messages to 
   - `lost_mqtt_server_connection`: transition to `Offline` state.
3. `Offline`: The edge node is scanning and trying to connect to Host mqtt
server. 
    - `connected_to_mqtt_server`: transition to `Online`
    - ``


## 4 bridge

The host bridge is not really a host application in the sense of Sparkplug B specification. It is a component to be used by a host application. It helps to the REAL application to comunicate to the edge nodes:

- Recieving the messages from all nodes conected to broker, following a Observer pattern.
- Send writing metric requests (lets call `` from now).

The interface with this reponsability is really easy:

- `observe_node`
- `send_command`
