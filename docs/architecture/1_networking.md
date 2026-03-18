# Networking: Secure P2P with Tailscale

PeerStash solves the "friend-to-friend" backup problem by creating a private, encrypted mesh network that bypasses the need for port forwarding or static IPs.

### The Role of Tailscale
Tailscale is embedded directly into the PeerStash control container. It uses the WireGuard protocol to establish point-to-point encrypted tunnels between peers.

### The Identity & Invitation System
* **Automated ACLs:** During `peerstash setup`, the tool automatically modifies your Tailscale Access Control List (ACL) to ensure that only authenticated PeerStash nodes can communicate, following a principle of least privilege. It also generates and stores a tailscale multi-use invite code to make the share process simpler.
* **Unique Identity:** Each node generates a unique share key using `peerstash id`, which encodes the node's public keys, username, and tailscale invite code.
* **One-Time Invites:** When you run `peerstash register`, the tool prints the Tailscale "invite URL". Once you accept this invite, their machine is added to your private tailnet securely.
