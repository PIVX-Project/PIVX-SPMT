## Features

### <a name="features1"></a>Getting masternode status

Click on `Get Status For All Masternodes` to inspect the status of all masternode entries.<br>

<img src="img/features_01.png" width="670"><br>

<p>To inspect the status details click on the little magnifying glass icon.</p>

<img src="img/features_02.png" width="670"><br>
<br>
<img src="img/features_03.png" width="670"><br>
<br>

### <a name="features2"></a>Starting masternode

Click `Start All Masternodes` to send a start-message for all masternode entries or click the little rocket icon next to a particular entry to start that one masternode.<br>

<img src="img/features_04.png" width="670"><br>

Click `yes` to confirm<br>

<img src="img/features_05.png" width="670"><br>

<p>Double check the masternode message hash both on screen and on the display of the device.<br>
Then click "yes" on the hardware device.</p>

<img src="img/features_06.png" width="670"><br>

SPMT presents the decoded message.<br>
Double check it and then click `Yes`.<br>

<img src="img/features_07.png" width="670"><br>

<p>After broadcasting the message, SPMT presents a confirmation dialog.</p>

<img src="img/features_08.png" width="670"><br>
<br>

### <a name="features3"></a>Spending masternode rewards

Select the `Transfer Rewards Tab` to go to the rewards panel (or use the shortcut, money icon, to simultaneously change tab and select the node).<br>

<img src="img/features_09.png" width="670"><br>

<p>Use the dropdown menu to select the masternode you wish to send rewards from.</p>

<img src="img/features_10.png" width="670"><br>

Click on `Show Collateral` if you wish to select and spend it.<br>
Click on `Hide Collateral` to hide it again.<br>

<img src="img/features_11.png" width="670"><br>

<p>Select those UTXOs you wish to spend.<br>
The suggested fee is automatically adjusted based on the TX size and the average fee of the last 200 blocks.<br>
Adjust it as preferred.</p>

Then insert the PIVX `Destination Address` and click on `Send`<br>

<img src="img/features_12.png" width="670"><br>

<p>Preparing the TX is an expensive operation. The more rewards included, the more time is needed. A progress bar gives the current status of the operation.</p>

<img src="img/features_13.png" width="670"><br>

<p>Verify the details of the TX both on screen and on the display of the Nano S.<br>
If everything checks out, click "yes" (right button) on the device.</p>

<img src="img/features_14.png" width="670"><br>

<p>Signing all the inputs is time consuming as well.<br>
The dialog shows the percentage of completion.</p>

<img src="img/features_15.png" width="670"><br><br>

<p>The transaction is now assembled and signed.<br>
SPMT asks one more time to check the details before broadcasting the transaction (thus spending the selected rewards).<br>
Click `Show Details` to inspect the decoded raw transaction.</p>

<img src="img/features_16.png" width="670"><br>

<p>Click `Yes` to finally broadcast the transaction to the PIVX network.</p>

Click `Show Details` to get the TX-id that identify the transaction.<br>
It should appear on the Block Explorers and on the receiving wallet after a few seconds.<br>
<br>


#### <a name="features4"></a>Sweeping all masternode rewards

<p>With this feature it is possible to send all rewards from all masternodes in list with a single TX (provided it doesn't get too big).</p>

Click on `Sweep All Rewards` to open the summary dialog.<br>

<img src="img/features_17.png" width="670"><br>

Insert the destination address, adjust the fee and click `Send`<br>

<img src="img/features_18.png" width="670"><br>

<p>Preparing the TX is an expensive operation. The more rewards included, the more time is needed. A progress bar shows the current status.</p>

<img src="img/features_19.png" width="670"><br>

<p>Eventually SPMT shows the confirmation dialog and waits for the user to press the 'OK' button on the device.  Then starts the signature operation.<br>
Signing all the inputs is time consuming as well.<br>
The dialog shows the percentage of completion.</p>

<img src="img/features_20.png" width="670"><br>

<p>
After some time it prompts the usual message to confirm before broadcasting the signed transaction</p>

<img src="img/features_21.png" width="670"><br><br>


### <a name="features5"></a>Governance

<p>Version <b>v0.3.0</b> of SPMT introduced the ability for masternode owners to interact with the governance of the PIVX DAO (decentralized autonomous organization) directly from within the tool.</p>

To review budget proposals and vote on them, select the `Governance` Tab.<br>

<img src="img/features_22.png" width="670"><br>

#### <a name="features6"></a>Reviewing the budget

<p>If the RPC server is connected, the current proposal list will be automatically loaded and displayed.<br>
To reload the list, click on the double arrow icon in the upper right corner.</p>

<p>For each proposal is displayed: name, proposal hash, link, monthly payment, number of payments (remaining and total), network votes (yes / abstains / no) and the number of votes belonging to the user's masternodes.<br>
Each column can be ordered in both ascending and descending order.</p>

<img src="img/features_23.png" width="670"><br>

<p>In the main list, each row has the "Network Votes" cell's background highlighted to reflect its status:</p>
<ul>
<li> <em style='color:green'>GREEN</em>: Proposal currently passing (number of net yes votes is higher than 10% of the total masternodes count)</li>
<li> <em style='color:red'>RED</em>: Proposal currently not passing (number of net yes votes is negative - i.e. there are more 'no' votes than 'yes' votes)</li>
<li> <em style='color:YELLOW'>YELLOW</em>: Proposal expiring (number of remaining payments is zero)</li>
<li> <em>WHITE (no background)</em>: Proposal currently not passing (number of 'yes' net votes is positive but less than 10% of the total masternodes count)</li>
</ul>

To follow the discussion thread of a particular proposal on the PIVX forum click on the `Link` button.<br>

<img src="img/features_24.png" width="670"><br>

<p>To inspect the details of a proposal click the little magnifying glass icon.</p>

In the "Proposal Details" dialog the `Hash`, `FeeHash` and `Payment Address` fields are selectable (but of course not editable) so they can be copied and pasted elsewhere if needed.<br>

<img src="img/features_25.png" width="670"><br>

<p>To view the budget projection for the current cycle, click the list icon on the upper left corner of the Governance Tab</p>

<img src="img/features_26.png" width="670"><br>

<p>The budget overview shows the time remaining till next superblock as well as the list of proposals currently passing and the total allotted budget.</p>

<img src="img/features_27.png" width="670"><br>

<br>

#### <a name="features7"></a>Casting Votes

Click `Select Masternodes...` to select the masternode(s) you'd like to vote with.<br>

<img src="img/features_28.png" width="670"><br>

<p>Then select all proposals you'd like to vote on, clicking on the corresponding row in the table.<br>
The total number of proposals selected is shown in the bottom right corner</p>

<img src="img/features_29.png" width="670"><br>

Click `Vote YES` to vote 'yes' for the selected proposals or `Vote NO` to vote 'no' ('Abstain' option is currently disabled).<br>
A summary is presented. Click `Yes` to confirm or `No` to cancel.<br>

<img src="img/features_30.png" width="670"><br>

<p>The tool presents a popup showing the outcome of the operation.</p>


##### <a name="features7b"></a>Adding a random time offset

<p>To enhance the privacy of the masternode owner, the tool gives the ability to add a randomized delay to each vote timestamp.</p>

<p>The offset can be either positive or negative resulting in a vote slip with a timestamp either delayed or anticipated.<br>
To enable the feature, click the checkbox near the little clock icon in the bottom left corner of the Governance Tab.<br>
Set the seconds for the lower bound <em><b>LB</b></em> and the upper bound <em><b>UB</b></em>.</p>

<img src="img/features_31.png" width="670"><br>

<p>When voting, with this option enabled, a number of seconds <em><b>T</b></em>, is randomly chosen in <em><b>(-LB, UB)</b></em> for each vote and added to the current timestamp (i.e. to have only delayed votes, set <em><b>LB</b></em> to 0 seconds)</p>

<p>The random time <em><b>T</b></em> used for each vote is printed in the console log.</p>

<img src="img/features_32.png" width="670"><br>

<p>The timestamp of each personal vote can be also reviewed inside the details dialog of a proposal.</p>

<img src="img/features_33.png" width="670"><br>

<br>

### <a name="features8"></a>Resetting Application Data
To reset application data, the SPMT can be started from the command line with one of more of the following flags:
- `--clearAppData` : to clear user preferences such as window dimensions, pre-compiled fields, etc...
- `--clearMnData` : to remove all masternode's entries from the database
- `--clearRpcData` : to remove all RPC server's entries from the database
- `--clearTxCache` : to remove all saved raw transactions from the database

For example, to reset everything on a windows machine, navigate inside the app folder:
```
cd SPMT-v0.4.0a-Win64\app
```

And launch SPMT with all three flags:
```
SecurePivxMasternodeTool.exe --clearAppData --clearMnData --clearRpcData
```
