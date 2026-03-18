# Identity and Peers

These commands manage connection with friends (aka peers).

## `peerstash id`
Generates the unique identity string (Share Key) for your node. This string encodes your username, public keys, and tailscale invite code, allowing peers to register you securely.

## `peerstash register`
Registers a new peer using the Share Key they provided. This establishes a connection in the mesh and allocates storage space on your machine for their backups. If a user already exists, this can be used to update their keys and/or quota.

**Arguments:**
* `SHARE_KEY`: The base64 identity string provided by your peer.
* `QUOTA_GB`: The maximum storage limit (in GiB) you want to allow for this peer.

**Options:**
* `--yes`, `-y`: Overwrites an existing peer's configuration without prompting.

## `peerstash peers`
Lists all registered peers and displays your current disk usage relative to the quota they've assigned you.

## `peerstash evict`
Removes a peer from your node. This cancels all scheduled tasks associated with that peer and prevents them from accessing or creating backups. Note that this does **not** automatically delete their existing data from your disk; that must be done manually for safety.

**Arguments:**
* `USERNAME`: The name of the peer to evict.

**Options:**
* `--force`, `-f`: Evicts the peer immediately without a confirmation prompt.
