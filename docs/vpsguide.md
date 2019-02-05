## Masternode VPS setup
### Install the latest version of the PIVX wallet onto your masternode.
The current guide uses PIVX wallet version 3.1.1 as reference.
Always make sure to use the latest version which can be found at this link:<br>
https://github.com/PIVX-Project/PIVX/releases <br>
<br>
Go to your home directory:
```
cd ~
```

From your home directory, download the latest version from the PIVX GitHub repository:
```
wget https://github.com/PIVX-Project/PIVX/releases/download/v3.1.1/pivx-3.1.1-x86_64-linux-gnu.tar.gz
```

Unzip and extract:
```
tar -zxvf pivx-3.1.1-x86_64-linux-gnu.tar.gz
```

Go to your PIVX 3.1.1 bin directory:
```
cd ~/pivx-3.1.1/bin
```

>*Note*: If this is the first time running the wallet in the VPS, you’ll need to attempt to start the wallet with  `./pivxd`. This will place the config files in your `~/.pivx` data directory.<br>
Press `CTRL+C` to exit / stop the wallet then continue to next step.

<br>

### Configure the wallet
Move to the PIVX data directory:
```
cd ~/.pivx
```

Use nano (or vi, or any text editor) to create a configuration file:
```
nano pivx.conf
```

Insert the required fields.
Make sure to replace rpcuser and rpcpassword with your own, as well as the IP address of the VPS and the *mnPrivKey*  obtained from SPMT.
```
rpcuser=<long random username>
rpcpassword=<longer random password>
rpcallowip=127.0.0.1
server=1
daemon=1
listen=1
logtimestamps=1
maxconnections=256
masternode=1
externalip=<your unique public ip address>
masternodeaddr=<your unique public ip address>:51472
masternodeprivkey=<your mnPrivKey>
```

Exit and save (`CTRL+X`).

<br>

### Start the Node
Now, you need to finally start the wallet (for the second time).<br>
First go back to your installed wallet directory
```
cd ~/pivx-3.1.1/bin
```

and then start the wallet using
```
./pivxd
```

The masternode now needs to be fully synced before it can be started from the SPMT controller.
You can check the status of the sync with:
```
./pivx-cli mnsync status
```

When the output shows the following
```
  "IsBlockchainSynced": true,
  ...
  "RequestedMasternodeAssets": 999,
  "RequestedMasternodeAttempt": 0
```
The masternode is ready to be started from the controller.
