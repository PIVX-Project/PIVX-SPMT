## Masternode VPS setup
### Install the latest version of the PIVX wallet onto your masternode.
The lastest version can be found here: https://github.com/PIVX-Project/PIVX/releases <br>
<br>
Go to your home directory:
```
cd ~
```

From your home directory, download the latest version from the PIVX GitHub repository:
```
wget https://github.com/PIVX-Project/PIVX/releases/download/v3.1.0.2/pivx-3.1.0.2-x86_64-linux-gnu.tar.gz
```

Make sure you choose the correct version of the core wallet.
Unzip and extract:
```
tar -zxvf pivx-3.1.0.2-x86_64-linux-gnu.tar.gz
```

Go to your PIVX 3.0.0 bin directory:
```
cd ~/pivx-3.1.0/bin
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

Inser the required fields.
Make sure to replace rpcuser and rpcpassword with your own, as well as the vps IP and the *mnPrivKey*  obtained from SPMT.
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
bind=<your unique public ip address>
masternodeaddr=<your unique public ip address>:51472
masternodeprivkey=<your mnPrivKey>
```

Exit and save (`CTRL+X`).

<br>

### Start the Node
Now, you need to finally start the wallet (for the second time).<br>
First go back to your installed wallet directory
```
cd ~/pivx-3.1.0/bin
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
