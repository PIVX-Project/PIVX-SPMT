# SPMT
SPMT: Secure Pivx Masternode Tool is a software to securely manage multiple PIVX masternodes while keeping the collateral safely stored on a Ledger Nano S hardware wallet.

## Installation
This application does not require installation.
However, if you are running it from the source code, you will need Python 3 and several libraries (listed in `requirements.txt`).<br> 
If you are using a binary version instead, just unzip the folder anywhere you like and use the shortcut to start the application.

## Updating
When updating to a new version of the SPMT application, copy the following files from the old folder to the new in order to preserve your rpc and masternodes configuration:
- rpcServer.json
- masternodes.json

## Setup
#### Setting up the RPC server
In order to interact with the PIVX blockchain, the SPMT needs a local PIVX wallet running alongside (any empty pivx-cli wallet will do).
Edit your local `pivx.conf` inserting rpcuser, rpcpassword, rpcport and rpcallowip. 
Example:
```bash
server=1
rpcuser=myUsername
rpcpassword=myPassword
rpcport=45458
rpcallowip=127.0.0.1
```

Configure the RPC server by clicking on the menu
![1](doc/img/00-click_setup.png)

and inserting the same data
![1](doc/img/01-setup_rpc.png)

#### Connecting
Connect the hardware device and open pivx app on it.
Click the connection buttons on the SPMT to connect to both the cli-wallet and the hardware device.
![1](doc/img/02-click_connectHW.png)

#### Setting up a Masternode configuration
Click on `NEW MASTERNODE` and fill all the informations of the remote node: 
*masternode name 
*ip Address and port.
Insert masternode private key (same as `masternodeprivkey` on `pivx.conf` of remote node) or generate a new one (then copy it to the config file of the remote node).
![1](doc/img/03-mnsetup01.png)

Insert the PIVX Address holding the collateral and relative account number (if you have just one account on your Ledger wallet, leave it to 0).
Click `>>` to look for path and public key.
![1](doc/img/04-mnsetup02.png)

Click `Lookup` to find the collateral TxHash or click edit and fill it manually.
![1](doc/img/05-mnsetup03.png)


## Usage
...
coming soon
...


## Credits
This work is based on the following projects for Dash:
- https://github.com/chaeplin/dashmnb
- https://github.com/Bertrand256/dash-masternode-tool


## Donations
If you like this tool, feel free to coffee me:
*DMEC4jnPmFjuVFsbGU2tX6V4ncUDD27dxo*
