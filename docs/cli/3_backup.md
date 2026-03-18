# Backup Management

These commands allow you to create, trigger, and manage automated backup tasks.

## `peerstash schedule`
Configures a new recurring backup task. If the task name already exists, you will be prompted to update it unless the `--update` flag is used.

**Arguments:**
* `PEER`: The username of the peer receiving the backup.

**Options:**
* `--name`: A unique name for the task. If omitted, one is generated automatically.
* `--include`: File or directory to backup (can be used multiple times to set multiple paths). Defaults to `.`.
* `--exclude`: Regex patterns to ignore (can be used multiple times to set multiple exclusions).
* `--schedule`: A cron expression for backups. Defaults to `0 3 * * *` (3 AM daily).
* `--prune-schedule`: A cron expression for pruning. Defaults to `0 4 * * 0` (4 AM Sundays).
* `--retention`: The retention policy (e.g., `1y2m3w4d5h6r`). Defaults to `4w3d`. A full explanation of the syntax can be found in the [`architecture/backup` page](https://github.com/BPR02/PeerStash/blob/main/docs/architecture/3_backups.md).
* `--update`, `-u`: Update an existing task without prompting.

## `peerstash backup`
Manually triggers a specific backup task immediately.

**Arguments:**
* `NAME`: The name of the backup task to run.
* `OFFSET`: An optional random delay in minutes (default: 0). This is used by the scheduler to randomly offset the task to prevent heavy traffic.

## `peerstash prune`
Manually triggers a cleanup of a specific backup repository. This command removes old snapshots based on the **retention policy** set during scheduling.

**Arguments:**
* `NAME`: The name of the task to prune.
* `OFFSET`: An optional random delay in minutes (default: 0). This is used by the scheduler to randomly offset the task to prevent heavy traffic.

## `peerstash list`
Displays all scheduled backup tasks and their current configuration.

**Options:**
* `--long`, `-l`: Displays attributes such as peer, schedule, and paths.
* `--human-readable`, `-h`: Formats the output with colors and clear labels.
* `--all`, `-a`: Includes technical details such as the last run time and exit code.

## `peerstash cancel`
Removes a scheduled task from the local database and stops future runs.

**Arguments:**
* `NAME`: The name of the task to remove.
