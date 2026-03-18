# Node Setup

The `setup` command is the first step to using PeerStash. It handles the authentication with Tailscale and initializes your local security credentials.

## `peerstash setup`
Initializes and authenticates the node. This command performs several critical tasks:
* Generates a unique, deterministic password for your local **restic** repositories.
* Configures Tailscale Access Control (ACL) policies for the PeerStash network.
* Registers the device and generates a unique invite code for peers.

**Options:**
* `--token`: A Tailscale API Access Token. If provided, the setup skips interactive instructions.
* `--overwrite`, `-o`: Force-runs the setup again. Use this only if you need to repair a corrupted Tailscale configuration.
