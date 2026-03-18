# Recovery & Browsing

PeerStash makes it easy to inspect your backups and restore files either through a virtual mount or a direct restore command.

## `peerstash snapshots`
Lists every backup point (snapshot) available for a specific task.

**Arguments:**
* `NAME`: The name of the backup task.
* `SNAPSHOT_ID`: (Optional) Get detailed information about a specific snapshot.

**Options:**
* `--json`, `-j`: Outputs the snapshot list in JSON format for scripting.

## `peerstash mount`
Mounts a remote peer's repository as a local filesystem. This allows you to browse through your backed-up files as if they were local folders. This can be used to copy previously backed up files, but it is recommended to use `peerstash restore` for large file restores.

## `peerstash unmount`
Safely unmounts a previously mounted repository.

## `peerstash restore`
Directly restores files from a snapshot to your local machine.

**Arguments:**
* `NAME`: The name of the backup task.
* `SNAPSHOT`: The ID of the snapshot to restore (defaults to `latest`).

**Options:**
* `--include`: A regex pattern to restore specific files or folders.
* `--exclude`: A regex pattern to ignore specific files during the restore process.
