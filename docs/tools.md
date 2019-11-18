## Tools

Version `0.5.1` adds a "Tools" section to the main menu.

<img src="img/tools_01.png" width="470"><br>
<br>

### <a name="tools1"></a>Sign text messages

<p>Select 'Sign/Verify message' from the 'Tools' menu, to open the dialog.</p>

<p>The 'Sign message' tab is already selected.<br>
If you want to sign with the key of a masternode (collateral address), select the masternode name from the dropdown menu. The masternode collateral address will be shown in the top right corner.<br>
If you want to use another address, instead, select "Generic address..." to look for it.</p>

<img src="img/tools_02.png" width="470"><br>
<br>

<p>Searching for the public key of a generic address is done in the same way as in the masternode collateral setup.<br>
Insert the account number and the address, the click on 'Search HW' to look for the account addresses (in batches of ten, asking confirmation to continue) until it finds one that matches.<br>
If, instead, you know already the address number, select the 'search from BIP44 path' radio button, insert the number next to 'spath_id' and click 'Search HW' to retrieve the key.</p>

<img src="img/tools_03.png" width="470"><br>
<br>

<p>Once found, the address is displayed in the upper right corner.<br>
Insert the message to sign and click 'Sign Message'</p>

<img src="img/tools_04.png" width="470"><br>
<br>

<p>Double check the message (or message hash, for Ledger) on the device LCD and confirm the signature.</p>

<img src="img/tools_05.png" width="470"><br>
<br>

<p>After performing the operation on the hardware device, the signature is displayed in the text area below the sign button. Click 'Copy' to copy it to the clipboard, or click 'Save' to save it to a text file.</p>

<img src="img/tools_06.png" width="470"><br>
<br>

### <a name="tools2"></a>Verify signatures

<p>This feature allows the user to verify messages signed with the private keys of PIVX mainnet or testnet addresses.<br>

<p>Select 'Sign/Verify message' from the 'Tools' menu, to open the dialog and click the 'Verify message signature' tab to activate it.<br>
Insert the address, the message, the signature, and click 'Verify Message'.<br>
The result is displayed below.</p>

<img src="img/tools_07.png" width="470"><br>
<br>

<img src="img/tools_08.png" width="470"><br>
<br>
