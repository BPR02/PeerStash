# Contributing
Contributions are welcome! Make sure to first open an issue discussing the problem or the new feature before creating a pull request. This project uses [npm](https://www.npmjs.com) to manage development dependencies.

## Installation
While this is a docker project, [nodejs](https://nodejs.org/) is used for certain dev tools.

### Install NodeJS
NodeJS can be installed for all systems using from [their website](https://nodejs.org/).

### Install Dependencies
Once nodejs is installed, the dependencies can be installed with the following command
```bash
$ npm install
```
#### Folder Structure
This command should be run in all folders that have a `package.json` file. Each folder prepended with `peerstash-` is essentially a subproject.


## Development Deployment
To deploy this project, use the `docker-compose-dev.yml` file. A `.env` file must be created to fill out certain fields. An example environment file can be found in the `peerstash-compose` folder. If environment variables aren't working, the fields can be manually replaced in the docker compose file.

```bash
$ docker compose -f peerstash-compose/docker-compose-dev.yml up
```

### Tailscale Tunnel
Tailscale needs access to the network tunnel device. The docker compose file has the host device hardcoded to the same path (`/dev/net/tun:/dev/net/tun`), but this appears to be valid only on linux systems. If you know how to make this work on non-linux systems please make an issue and/or pull request.

## Dev Tools
There are dev tools available to check the code for syntax errors and other potential issues. Tools are split into each `peerstash-` folder, so you should `cd` into the directory of the service you're updating before running the dev tools.

### Shell Checks
`peerstash-shell` has the `shellcheck` node module to check for POSIX compliance in shell scripts. Running the command below should output nothing to the terminal if all scripts are compliant with POSIX.
```bash
$ cd peerstash-shell
$ npx shellcheck scripts/*.sh
```

## Commits
When committing code, follow the [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) style for writing commit messages:

```md
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

### Examples
- feat(shell): create adduser script
- fix(shell): update passwd script to work without sudo
- feat(web,shell): initial dockerfiles


### Types
The type is used to determine the version bump. Only one should be used per commit message. The types used have been adapted from [angular](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines):
> **type** [*version*]: description

- **feat** [*minor*]: A new feature
- **fix** [*patch*]: A bug fix
- **perf** [*patch*]: A code change that improves performance
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **test**: Adding missing or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Scopes
The scope is used to determine the service that was changed to allow for separate versions of each service. Multiple can be used per commit message.
> **scope**: description

#### REQUIRED (if changed)
- **control**: peerstash-control was updated
- **shell**: peerstash-shell was updated
- **web**: peerstash-web was updated
- **compose**: peerstash-compose/docker-compose.yml was updated
#### Other
- **ci**: changes to the workflows were made
- **release**: used by semantic-release when an update is made
- **README**: changes to the readme were made
- **CONTRIBUTING**: changes to the contributing file were made

### Extras
- The start of `<body>` or `<footer>` can be `BREAKING CHANGE:` to indicate a **major** version bump
- Keep each line under 100 characters


## Versioning
This project follows the [semantic versioning](https://semver.org/) format for versioning:
- `major` reserved for breaking changes (needs maintainer approval)
- `minor` for new features and larger tweaks (usually changing user experience like adding an option to the config)
- `patch` for bug fixes and smaller tweaks (usually doesn't affect user experience)

> The commit type indicates whether a bump should be `patch` or `minor`. The version will be updated automatically based on the commit.
