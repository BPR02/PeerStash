# Storage: The "Semi-Trusted" Model

PeerStash is designed for **semi-trusted** environments—where you trust your friends not to maliciously delete your data, but you don't necessarily want them to have access to your raw files.

### Storage Isolation with SFTPGo
While your peers provide the physical disk space, they are isolated using **SFTPGo**:
* **Isolated Filesystems:** Each peer is registered as a unique user in SFTPGo with its own home directory. They cannot see or modify the data of other peers.
* **Strict Quotas:** You define exactly how much space a peer can use during `peerstash register`. If they exceed this quota, SFTPGo will reject further uploads.

### Daemon & Automation
The `peerstashd` daemon runs in the background of the control container. It monitors the local SQLite database and triggers `restic` based on your defined cron schedules. If a peer is offline, the daemon will retry the backup during the next scheduled window.
