<img src="img/splashscreen.png"><br><br>

# SPMT
SPMT: Secure Pivx Masternode Tool is a software to securely manage multiple PIVX masternodes while keeping the collateral safely stored on Ledger Nano S hardware wallets.

* [Installation](#installation)
* [Setup](#setup)
  - [Setting up the RPC server](#setup1)
  - [Connections](#setup2)
  - [Setting up a Masternode configuration](#setup3)
* [Features](#features)
  - [Getting masternode status](#features1)
  - [Starting masternode](#features2)
  - [Spending masternode rewards](#features3)
    - [Sweeping all masternode rewards](#features4)
* [Coming Soon](#comingsoon)
* [Credits](#credits)

## <a name="installation"></a>Installation

This application does not require installation.<br>
If you are using a [binary version](https://github.com/PIVX-Project/PIVX-SPMT/releases), just unzip the folder anywhere you like and use the executable to start the application:
- *Linux*: double-click `SecurePivxMasternodeTool` file inside the `app` directory
- *Windows*: double-click `SecurePivxMasternodeTool.exe` file inside the `app` directory
- *Mac OsX*: double-click `SecurePivxMasternodeTool.app` application folder

If you are running SPMT from the source-code instead, you will need Python3 and several libraries installed.<br>
Needed libraries are listed in `requirements.txt`.<br>
From the `SPMT` directory, launch the tool with:
```bash
python3 spmt.py
```
To make binary versions from source, [PyInstaller](http://www.pyinstaller.org/) can be used with the `SecurePivxMasternode.spec` file provided.

## <a name="setup"></a>Setup

<b>NOTE:</b> :warning: make sure to have the latest firmware installed on your Nano S device.<br>

#### <a name="setup1"></a>Setting up the RPC server
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

<br><img src="doc/img/01.png" width="670"><br><br>

and inserting the same data.
You can leave ip `127.0.0.1` if the wallet is on the same machine as the SPMT.<br>
Otherwise set the IP address of the machine running the Core PIVX wallet.
<br><img src="doc/img/02.png" width="670"><br><br>

#### <a name="setup2"></a>Connections
If the IP and the credentials of the PIVX wallet are correct, it should connect with SPMT instantly.<br>
Otherwise use the `Connect` button next to "PIVX RPC server: Local Wallet".<br>
Connect the hardware device to USB and open the PIVX-App on it.<br>

Click the button `Connect` next to "Hardware Device: Ledger Nano S" to connect to the hardware device.
<br><img src="doc/img/03.png" width="670"><br><br>

Once successfully connected, it gives a confirmation message and the light turns purple.
<br><img src="doc/img/04.png" width="670"><br><br>

#### <a name="setup3"></a>Setting up a Masternode configuration
Click `New Masternode` (big button below the list) and fill all the informations of the remote node: 
 - <b>Name</b> : an alias for the masternode entry
 - <b>IP Address / IP Port</b> : Public IP address and port of the remote masternode
 - <b>MN Priv Key</b> : masternode private key. If you have already seup the remote node, copy here the `masternodeprivkey` from the pivx.conf file.<br>
If you don't have one yet, you can generate a new masternode private key clicking on `Generate` (then copy it to the config file of the remote node).


Insert the PIVX Address holding the collateral (and relative account number)<br>
If you have just one account in your Ledger wallet, leave account number to `0`.<br>
Then click `>>` to look for path and public key.
<br><img src="doc/img/05.png" width="670"><br><br>

The tool looks for the public key and path of the given address (in batches of 10 paths per scan, asking confirmation to continue if needed). 
When found, a notification message is displayed.
<br><img src="doc/img/05b.png" width="670"><br><br>

If the user already knows the correct `spath_id` (address number) he can, instead, insert it and click `<<` to look for the corresponding address and public key.<br><br>

Click `Lookup` to find the collateral TxHash or click `Edit` to fill it manually, and then `OK`.<br>
Click `Save` to save the configuration and go back to main view.
<br><img src="doc/img/06.png" width="670"><br><br>


## <a name="features"></a>Features
### <a name="features1"></a>Getting masternode status
Click on `Get Status For All Masternodes` to inspect the status of all masternode entries.
<br><img src="doc/img/07.png" width="670"><br><br>

To inspect the status details click on the little magnifying glass icon.
<br><img src="doc/img/08.png" width="670"><br><br>
<br><img src="doc/img/09.png" width="670"><br><br>

### <a name="features2"></a>Starting masternode
Click `Start All Masternodes` to send a start-message for all masternode entries or click the little rocket icon next to a particular entry to start that one masternode.
<br><img src="doc/img/10.png" width="670"><br><br>

Click `yes` to confirm
<br><img src="doc/img/11.png" width="670"><br><br>

Double check the masternode message hash both on screen and on the display of the device.<br>
Then click "yes" (right button) on the ledger nano S.
<br><img src="doc/img/12.png" width="670"><br><br>

SPMT presents the decoded message.<br>
Double check it and then click `Yes`.
<br><img src="doc/img/13.png" width="670"><br><br>

After broadcasting the message, SPMT presents a confirmation popup.
<br><img src="doc/img/14.png" width="670"><br><br>

### <a name="features3"></a>Spending masternode rewards
Select the `Transfer Rewards Tab` to go to the rewards panel (ore use the shortcut, money icon, to simultaniously change tab and select the node).
<br><img src="doc/img/15.png" width="670"><br><br>

Use the dropdown menu to select the masternode you wish to send rewards from.
<br><img src="doc/img/16.png" width="670"><br><br>

Click on `Show Collateral` if you wish to select and spend it.<br>
Click on `Hide Collateral` to hide it again.
<br><img src="doc/img/17.png" width="670"><br><br>

Select those UTXOs you wish to spend.<br>
The suggested fee is automatically adjusted based on the TX size and the average fee of the last 200 blocks.<br>
Adjust it as preferred.<br>
Then insert the PIVX `Destination Address` and click on `Send`
<br><img src="doc/img/18.png" width="670"><br><br>

Verify the details of the TX both on screen and on the display of the Nano S.<br>
If everything checks out, click "yes" (right button) on the device.
<br><img src="doc/img/19.png" width="670"><br><br>

The transaction is now assembled and signed.<br>
SPMT asks one more time to check the details before broadcasting the transaction (thus spending the selected rewards).<br>
Click `Show Details` to inspect the decoded raw transaction.
<br><img src="doc/img/20.png" width="670"><br><br>

Click `Yes` to finally broadcast the transaction to the PIVX network.<br>
Click `Show Details` to get the TX-id that identify the transaction.<br>
It should appear on the Block Explorers and on the receiving wallet after a few seconds.
<br><img src="doc/img/21.png" width="670"><br><br>


#### <a name="features4"></a>Sweeping all masternode rewards
With this feature it is possible to send all rewards from all masternodes in list with a single TX (provided it doesn't get too big).<br>
<br>
Click on `Sweep All Rewards` to open the summary dialog.
<br><img src="doc/img/22.png" width="670"><br><br>

Insert the destination address, adjust the fee and click `Send`
<br><img src="doc/img/23.png" width="670"><br><br>

Preparing the TX is an expensive operation. The more rewards included, the more time is needed. 
<br><img src="doc/img/24.png" width="670"><br><br>

Eventually SPMT shows the confirmation dialog
<br><img src="doc/img/25.png" width="670"><br><br>

Signing all the inputs is time consuming as well.<br>
If the operation takes too long, the number of inputs is probably too high. try sending separate TXs first.<br>
After some time it prompts the usual message
<br><img src="doc/img/26.png" width="670"><br><br>


## <a name="comingsoon"></a>Coming soon
- Voting
- Lite Connection
...


## <a name="credits"></a>Credits
A huge part of this work is inspired by the following Dash projects:
- https://github.com/chaeplin/dashmnb
- https://github.com/Bertrand256/dash-masternode-tool

