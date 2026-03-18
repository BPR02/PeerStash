# Welcome to PeerStash
**Secure, peer-to-peer NAS backups between friends.**
PeerStash is a plug-and-play solution designed to solve the challenge of backing up data between semi-trusted machines. While many tools exist for cloud backups or fully trusted remote machines, PeerStash creates a secure, encrypted mesh network specifically for peer-to-peer storage.

## Why PeerStash?
  * **Zero-Trust Security**: Your data is encrypted locally using **restic** before it ever leaves your machine; your peers provide storage but cannot read your files.
  * **No Port Forwarding**: Powered by **Tailscale**, PeerStash establishes secure, point-to-point connections through a private mesh network, even behind NAT or restrictive firewalls.
  * **Storage Isolation**: Utilizing **SFTPGo**, each peer is isolated in their own environment with strict storage quotas, ensuring your system remains secure and your disk space is managed.
  * **Privacy-First**: This is a strictly self-hosted project with no central API, no telemetry, and no data sharing with third parties. You own your data and decide exactly who is keeping it safe.

## Documentation Navigation
Explore the various sections of our documentation to get the most out of PeerStash:

### 🛠️ CLI Reference

Comprehensive guides for every command available in the PeerStash CLI.

  * **[Node Setup](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/cli/1_setup.md)**: Authenticate with Tailscale and initialize your security credentials.
  * **[Identity & Peers](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/cli/2_peers.md)**: Manage your Share Key and connect with friends.
  * **[Backup Management](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/cli/3_backup.md)**: Schedule, trigger, and manage automated backup tasks.
  * **[Recovery & Browsing](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/cli/4_recovery.md)**: Browse snapshots, mount remote repos, and restore your data.

### 🏗️ Architecture

Understand the underlying architecture and security models.

  * **[Networking: Secure P2P with Tailscale](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/architecture/1_networking.md)**: How Tailscale is used to build a secure P2P mesh.
  * **[Storage: The Semi-Trusted Model](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/architecture/2_storage.md)**: How SFTPGo and encryption keep your data private in shared environments.
  * **[Backups: Restic & Retention Logic](https://github.com/BPR02/PeerStash/blob/readme-prod/docs/architecture/3_backups.md)**: How restic is used for deduplication zero-trust encryption.

## Quick Start

If you are looking to get up and running immediately, please refer to the **[Getting Started section of the README](https://github.com/BPR02/PeerStash/tree/main?tab=readme-ov-file#-getting-started)** for installation steps using Docker Compose.

Once your containers are deployed and you are SSH'd into the control container, your first step will be to run:

```bash
peerstash setup
```

## License
PeerStash is proud to be open-source software, licensed under the **GNU Affero General Public License v3.0**.
