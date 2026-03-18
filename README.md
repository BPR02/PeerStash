# PeerStash: The P2P NAS Backup Tool
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


## 🚀 Current Development Status
PeerStash is currently in active development. The design specifications can be found [here](https://docs.google.com/document/d/12tKH2wguz-OzgiXsKYCllzRssa6628woeOXamTWgD_4/edit?usp=sharing).

**Infrastructure:** A `docker-compose.yml` and example `.env` file is provided to connect the storage and control containers.

**CI/CD Pipeline:** GitHub Actions workflows are implemented to automatically build the Docker image for the control container. Commits to `main` trigger a stable build, while commits to `dev` trigger a development build for easy pushing and testing on local NAS devices. Development is done on the `dev` branch and tested before pushing to `main`. 

**CLI Tooling:** A custom Typer-based CLI has been built in Python. Below are the most important commands.
* `peerstash setup`: Sets up the necessary tailscale configurations from a short-lived API access token.
* `peerstash id`: Encodes the username and public key into a single base64 string for easy sharing. 
* `peerstash register`: Decodes the base64 string and registers the connection by interfacing with the SFTPGo API and the local SQLite database. 
* `peerstash schedule`: Schedules a backup to be run continuously.

**Next Steps:** Set up automated testing and proper PR workflows (i.e. get rid of the dev branch sequential change necessity and switch to creating temporary docker builds for each new PR).

**Future Plans:** Web UI and Erasure Coding
* A simple Web UI is planned for better UX than the CLI
* A "mesh" like system is planned so a group of users can set up storage with erasure coding, similar to RAID, but across the mesh.
