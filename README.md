# PeerStash: The P2P NAS Backup Tool
**Secure decentralized backups between friends**

PeerStash is a plug-and-play solution for securely sending backups between semi-trusted machines (e.g., your NAS and a friend's NAS). While existing tools exist to back up to cloud providers or fully trusted remote machines, PeerStash fills the gap for peer-to-peer storage with zero-config networking.

## 🏗️ Architecture
This project uses Docker to support a wide variety of operating systems. It consists of 2 docker containers: a storage container, and a control container. 

* **Storage:** [SFTPGo](https://sftpgo.com) is used as a fully featured SFTP server that has a built in user manager with configurable quotas. 

* **Control:** The control container is what is being developed. It will create and send the backups. A lightweight docker container will be created that will provide a simple CLI tool to schedule backups created using [restic](https://restic.net). [Tailscale](https://tailscale.com) is embedded in this container and used to connect each device to each other, creating a unified and secure network. 


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
