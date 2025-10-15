# pyshare-cli v3.0: Secure Interactive File Transfer

**pyshare** is a modern, secure, and interactive command-line tool for transferring files, folders, and text snippets across your local network. All transfers are protected with end-to-end encryption and a confirmation PIN.

## Features

* **Interactive Terminal Session**: Run `pyshare` to enter an intuitive file-sharing environment.
* **End-to-End Encryption**: All data is encrypted using a robust RSA+Fernet handshake, ensuring nobody on the network can snoop on your files.
* **Confirmation PIN**: A 4-digit PIN is displayed on the receiver's screen and must be confirmed by the sender, preventing accidental transfers.
* **Folder & Multiple File Transfers**: Send an entire folder with one command. `pyshare` automatically zips it, sends it, and unzips it on the other side.
* **Text & Clipboard Sharing**: Instantly send a text snippet or your clipboard contents with the `send --text` and `paste` commands.
* **Resumable Transfers**: If a large file transfer gets interrupted, it will automatically resume from where it left off.
* **Persistent Command History**: Press the up and down arrow keys to navigate your command history.
* **Auto-Discovery**: Automatically finds other devices on the network running `pyshare`.
* **Visual Progress Bars**: A clean `tqdm` progress bar shows the status of every transfer.

## Installation

You will need Python 3.7+ and `pip`.

```bash
pip install pyshare
```

To install locally for development from the pyshare-cli directory:

```bash
pip install -e .
```

## How to Use

### Start the Session

Open a terminal on two devices and run:

```bash
pyshare
```

You will enter the interactive `pyshare>` prompt.

### Start Receiver

On the computer that will receive the file, type:

```bash
pyshare> receive
```

The receiver will start in the background, ready to accept connections.

### Send a File, Folder, or Text

On the other computer:

To send a file:

```bash
pyshare> send "/path/to/my document.zip"
```

To send a folder:

```bash
pyshare> send "/path/to/my project folder/"
```

To send text:

```bash
pyshare> send --text "Here is the link: https://example.com"
```

To send your clipboard:

```bash
pyshare> paste
```

### Confirm the Transfer

1. The sender's terminal will discover the receiver. Select it by its ID.
2. The receiver's terminal will ask for confirmation (y/n).
3. The sender's terminal will then display a 4-digit PIN. This PIN is shown to the receiver in the previous step, but for security, you should verbally confirm it with the person at the receiver's machine.
4. Once the PIN is confirmed and the handshake is complete, the encrypted transfer will begin.

### Exit

When you are finished, type `exit` or `quit`.

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
