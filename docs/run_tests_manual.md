# How to run SAI-Challenger tests

First you need to install dependencies:
```
sudo apt update
sudo apt install -y git docker docker.io
sudo usermod -aG docker $USER
```


### Clone repository
```
git clone https://github.com/PLVision/SAI-Challenger.OCP
cd SAI-Challenger.OCP
git checkout dash-testing
git submodule update --init --recursive
```

### Build client and server docker images
```
./build.sh -i client
./build.sh -i server -a trident2 -t saivs
```

### Run client and server docker containers
```
./run.sh -i client -p
./run.sh -i server -a trident2 -t saivs -p
```

### Create host interfaces
```
sudo ./veth-create-host.sh sc-server-trident2-saivs-run sc-client-run
```

## Running the test

`test_l2_basic` is used as an example.
```
./exec.sh -i client pytest --setup=../setups/saivs_client_server.json -v -k "test_l2_basic"
```

In order to see the syncd log you need to connect to the `server`:
```
docker exec -it sc-server-trident2-saivs-run bash
```
And check  `/var/log/messages`

To see what the input of the redis-server you need to install tcpdump and run it while tests are running:
```
sudo apt install -y tcpdump
sudo tcpdump port 6379
```
