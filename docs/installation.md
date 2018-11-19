## Installation

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
<br>To make binary versions from source, [PyInstaller](http://www.pyinstaller.org/) can be used with the `SecurePivxMasternode.spec` file provided.
<br>


#### Verifying the binaries
It's always advised to use the provided signature *asc* files to verify the authenticity of the downloaded package and confirm it has been signed by the author (Keybase user: [random_zebra](https://keybase.io/random_zebra/)).

__To verify the signature (with keybase app)__:
```
keybase pgp verify -d <detached signature file> -i <downloaded archive> -S random_zebra
```
e.g.
```
keybase pgp verify -d SPMT-v0.3.2a-x86_64-gnu_linux.tar.gz.asc -i SPMT-v0.3.2a-x86_64-gnu_linux.tar.gz -S random_zebra
```

__To verify it (without keybase app)__:
- Download signing key

```
curl https://keybase.io/random_zebra/pgp_keys.asc?fingerprint=ed501a1c26ce0733c33d6b00e7d8bf3b03d710a1 > random_zebra-PUBKEY.asc
```
- Import key 

```
gpg --import random_zebra-PUBKEY.asc
```
- Verify the downloaded archive with its detached signature file:

```
gpg --verify <detached signature file> <downloaded archive>
```

e.g.
```
gpg --verify SPMT-v0.3.2a-x86_64-gnu_linux.tar.gz.asc SPMT-v0.3.2a-x86_64-gnu_linux.tar.gz
```

<br>

### Setting up the Masternode VPS

To setup the remote node follow the steps described here:
[VPS Setup Guide](vpsguide.md)

<br>
