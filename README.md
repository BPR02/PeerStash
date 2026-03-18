# PeerStash: The P2P NAS Backup Tool
[![GHCR Pulls](https://ghcr-badge.elias.eu.org/shield/BPR02/PeerStash/peerstash-control?label=pulls&color=blue)](https://github.com/BPR02/PeerStash/pkgs/container/peerstash-control)

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/BPR02/PeerStash?label=version)](https://github.com/BPR02/PeerStash/tags)
[![Docker Image Version (latest semver)](https://img.shields.io/github/v/tag/BPR02/PeerStash?filter=peerstash-control-v*&label=ghcr&color=blue&logo=github)](https://github.com/BPR02/PeerStash/pkgs/container/peerstash-control)
[![Open Issues](https://img.shields.io/github/issues/BPR02/PeerStash?color=orange)](https://github.com/BPR02/PeerStash/issues)
[![tests](https://github.com/BPR02/PeerStash/actions/workflows/tests.yml/badge.svg)](https://github.com/BPR02/PeerStash/actions/workflows/tests.yml)
[![license: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Secure decentralized backups between friends**

PeerStash is a plug-and-play solution for securely sending backups between semi-trusted machines (e.g., your NAS and a friend's NAS). While existing tools exist to back up to cloud providers or fully trusted remote machines, PeerStash fills the gap for peer-to-peer storage with zero-config networking.

## ⚙️ Key Features
* **Zero-Config Networking:** Uses Tailscale to create a secure, encrypted mesh network between peers without port forwarding.
* **Automated Backups:** Leverages restic for efficient, deduplicated, and encrypted backups.
* **Isolated Storage:** Creates separate users within SFTPGo for isolated access and strict quotas.
* **Granular Control:** Manage schedules, retention policies, and pruning via a simple CLI.
* **Direct Access:** Mount remote repositories locally to browse and restore files instantly.
* **Privacy-First:** Self-hosted with no telemetry, no central API, and zero-trust encryption.

## 🏗️ Architecture
This project uses Docker to support a wide variety of operating systems and provide isolation from the host machine.

* **Storage:** [SFTPGo](https://sftpgo.com) is used as a fully featured SFTP server that has a built in user manager with configurable quotas. It ensures users uploading to your machine can only see their files and cannot exceed a hard quota storage limit.

* **Control:** The "brain" of PeerStash. A CLI tool schedules backups using [restic](https://restic.net). [Tailscale](https://tailscale.com) is embedded to connect each device to each other, creating a unified and secure network. 

## 🚀 Getting Started
1.  **Prerequisites:** Ensure you have [Docker](https://www.docker.com/) and [Tailscale](https://tailscale.com/) installed with a Tailscale account created.
2.  **Configuration:** Copy the `docker-compose.yml`, and the `example.env` to `.env` from the [peerstash-compose](https://github.com/BPR02/PeerStash/tree/main/peerstash-compose) folder to a local folder. Configure your credentials and storage paths in the `.env` file.
3.  **Deploy:** Navigate to the folder and deploy with docker compose.
    ```bash
    docker compose up -d
    ```
4.  **Log Into the Container:** SSH into the container using the port, username and password set in the `.env` file.
    ```bash
    ssh -p <port> <username>@<NAS_IP>
    ```
5.  **Use the PeerStash CLI:** You can now use the PeerStash CLI inside the container. The `setup` command should be used to set up tailscale.
    ```bash
    peerstash setup
    ```

## 🛠️ CLI Usage

PeerStash provides a comprehensive CLI built with Python and Typer. For in-depth documentation, visit the [docs](https://github.com/BPR02/PeerStash/blob/main/docs/README.md).

### Core Commands

  * `peerstash id`: Generates your unique share key for peers.
  * `peerstash register`: Adds a friend's share key to establish a connection.
  * `peerstash schedule`: Creates a recurring backup task with custom cron schedules and retention policies.
  * `peerstash list`: Displays all scheduled backup tasks and their current status.

### Management & Recovery

  * `peerstash snapshots`: Lists all available backup snapshots for a specific task.
  * `peerstash restore`: Restores files from a specific snapshot.
  * `peerstash mount`: Mounts a remote repository to `/tmp/peerstash_mnt` for easy file browsing.
  * `peerstash peers`: Lists all registered peers and displays their disk usage/quotas.

## 🤖 AI Transparency
PeerStash was developed with the assistance of Google Gemini, used primarily as a productivity tool for boilerplate code, debugging, some ideation, and a majority of the test suite.

The core system architecture (Tailscale/SFTPGo/restic) was designed by BPR, and all high-level architectural decisions were made by BPR. Every line of code was manually reviewed, edited, and verified. AI was never granted direct repository access; all contributions were manually integrated and committed.

## 📝 Future Plans
* A simple Web UI is planned for better UX than the CLI
* A "mesh" like system is planned so a group of users can set up storage with erasure coding, similar to RAID, but across the mesh.
