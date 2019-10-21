<img src="img/splashscreen.png"><br><br>

# SPMT

**SPMT: Secure Pivx Masternode Tool is a software to securely manage multiple PIVX masternodes while keeping the collateral safely stored on hardware wallets.<br>Currently supported wallets:**
 - [LEDGER](https://www.ledger.com) Nano S / Nano X
 - [TREZOR](https://trezor.io) One / Model T

<p>Running a PIVX masternode usually requires setting up two PIVX full nodes: </p>

1) the *Masternode*, that runs 24/7 (usually on a VPS) and holds no funds

2) the *Control Wallet*, that holds the collateral and does not need to be always on-line. <br>
It is used only to spend rewards, to vote on proposals, or to send a message (signed with the key of the collateral) to activate the remote node when it needs to be started.

<p>SPMT allows the user to store the keys of the collateral on an hardware wallet thus replaces the control wallet, allowing the user:</p>

- to sign with the collateral private key the start-message for the remote node and broadcast it.
- to spend masternode rewards without inadvertently including the collateral.
- to interact with the PIVX governance system reviewing proposals and budgets, and casting votes.

The tool connects to the PIVX blockchain through public remote servers but it's also possible to use a local running PIVX full node as RPC server or add customized remote servers. <br>


* [Installation](docs/installation.md)
  - [Setting up the Masternode VPS](docs/vpsguide.md)
* [Setup](docs/setup.md)
  - [Connections](docs/setup.md#setup1)
    - [Hardware Wallet Connection](docs/setup.md#setup2)
    - [RPC Server Connections](docs/setup.md#setup3)
      * Public Servers
      * Local wallet
      * Custom Private Servers
  - [Masternodes configurations](docs/setup.md#setup4)
    - [Setting up a masternode configuration](docs/setup.md#setup5)
    - [Import external masternode file](docs/setup.md#setup6)
* [Features](docs/features.md)
  - [Getting masternode status](docs/features.md#features1)
  - [Starting masternode](docs/features.md#features2)
  - [Spending masternode rewards](docs/features.md#features3)
    - [Sweeping all masternode rewards](docs/features.md#features4)
  - [Governance](docs/features.md#features5)
    - [Reviewing the budget](docs/features.md#features6)
    - [Casting votes](docs/features.md#features7)
  - [Resetting Application Data](docs/features.md#features8)


<br>

#### Additional References:
For an overview of how "traditional" masternodes work (without hardware wallets), see the knowledge-base guide:<br>
[Masternode Setup Guide](https://pivx.org/knowledge-base/masternode-setup-guide/)

For a self-hosted masternode setup with SPMT check the following guide:<br>
[Self-hosted MN from scratch (by TheEconomist)](https://forum.pivx.org/t/setting-up-a-self-hosted-mn-from-scratch-automatic-backup-crash-notification-spmt-tool/4229)

For an ODROID XU4 masternode setup with SPMT, check the following video tutorial:<br>
[How to setup a PIVX Masternode using SPMT and a Nano Ledger on an ODROID XU4 (by Cryptoshock LLC)](https://www.youtube.com/watch?v=lbIYh1upJJ8)
