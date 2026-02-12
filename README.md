# PeerStash: A NAS P2P Backup Tool
Peerstash is a user-friendly project to securely send backups between friends (i.e. semi-trusted machines). 

This project exists as a solution to backups between friends. While some tools exist to send backups to cloud providers or fully trusted remote NAS machines, there is currently no plug-and-play tool to handle sending backups to semi-trusted machines.

## 🏗️ Architecture
This project uses Docker to support a wide variety of operating systems. It consists of 3 docker containers: a networking container, a storage container, and a control container. 

* **Networking:** [Tailscale](https://tailscale.com) is used to connect each device to each other, creating a unified and secure network. 

* **Storage:** [SFTPGo](https://sftpgo.com) is used as a fully featured SFTP server that has a built in user manager with configurable quotas. 

* **Control:** The control container is what is being developed. It will create and send the backups. A lightweight docker container will be created that will provide a simple CLI tool to schedule backups created using [restic](https://restic.net). 


## 🚀 Current Development Status
PeerStash is currently in active development. The design specifications can be found [here](https://docs.google.com/document/d/12tKH2wguz-OzgiXsKYCllzRssa6628woeOXamTWgD_4/edit?usp=sharing).

**Infrastructure:** A `docker-compose.yml` is provided to connect the networking, storage, and control containers.

**CI/CD Pipeline:** GitHub Actions workflows are implemented to automatically build the Docker image for the control container. Commits to `main` trigger a stable build, while commits to `dev` trigger a development build for easy pushing and testing on local NAS devices. Development is done on the `dev` branch and tested before pushing to `main`. 

**CLI Tooling:** A custom Typer-based CLI has been built in Python.
* `peerstash id`: Encodes the username and public key into a single base64 string for easy sharing. 
* `peerstash register`: Decodes the base64 string and registers the connection by interfacing with the SFTPGo API and the local SQLite database. 

**Next Steps:** Integrating Restic and systemd to schedule and execute automated, encrypted snapshot backups.

**Future Plans:** Web UI and Erasure Coding
* A simple Web UI is planned for better UX than the CLI
* A "mesh" like system is planned so a group of users can set up storage with erasure coding, similar to RAID, but across the mesh.
