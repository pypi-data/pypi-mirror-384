# hpackage command reference
This guide walks you through downloading/installing packages first, then
authoring and uploading your own. Commands are shown exactly as you’d type
them.

> Tip: run hpackage -h or hpackage &lt;subcommand&gt; -h for built-in help.

## Installing & managing packages

### Install a package
```
hpackage install mytoolkit
```
* If you don’t specify a version, the latest available version is chosen.
* Dependencies are resolved automatically. If a dependency has `max_version`,
  that version is used; otherwise the latest is used.

### Install a specific version
```
hpackage install mytoolkit==1.2.3
```

### Install from a requirements file
```
hpackage install -r hrequirements.txt
```

Where hrequirements.txt lists one package per line, e.g.:
```
coollib
otherlib==2.0
# comments and blank lines are ignored
```

### Upgrade a package to its latest version
```
hpackage install -U mytoolkit
```

### List installed packages
```
hpackage list
hpackage list --show-location   # also prints paths
```

### Uninstall a package
```
hpackage uninstall mytoolkit
```
If Houdini is running, note that dynamic libraries loaded by the package won’t
unload unless Houdini is restarted.

If other packages depend on it, you’ll be warned. To skip the prompt:
```
hpackage uninstall -y mytoolkit
```

### How downloads work
* Downloads resume automatically if interrupted.
* A progress bar is shown by default (-v controls verbosity).
* After download, the file size and MD5 are verified; a mismatch aborts install.

## Authentication
You only need to sign in if you:
* install a package that requires a grant, or
* use author upload/publish features.

### Sign in (via browser session)
```
$ hpackage auth login
Waiting for you to log in via a browser (press Ctrl+C to quit)

$hpackage auth status
username      : yourusername
email         : you@yourdomain.com
company       : Your Company Name
Login method  : Session
```

To log out of the browser session:
```
hpackage auth logout
```

### API key (non-interactive)
Create and install a key tied to your account:
```
hpackage auth installkey
```

This writes an API key to your hserver.ini file. These keys are also used by
Houdini’s licensing tools and the launcher. Commands to uninstall keys and
delete them from hpackage’s server also exist.

```
$ hpackage auth status
username      : yourusername
email         : you@yourdomain.com
company       : Your Company Name
Login method  : API Key
API client id : <your-client-id>
```

## Authoring & uploading packages

### 1) Reserve a package name and create a starter template
```
hpackage author reserve mypkg
```

This:
* verifies you are allowed to reserve the name,
* creates a starter package skeleton under your Houdini user packages directory,
* writes getting-started.txt with next steps.

If a folder/JSON already exists with that name, nothing is overwritten; you’ll
be asked to complete the required fields instead.

### 2) Verify your package JSON
```
hpackage author verifyjson mypkg
# Or provide a path to a JSON:
# hpackage author verifyjson /path/to/mypkg.json
```

This validates:
* the JSON object structure and required keys and values (including env list entries),
* version format,
* a strict minimum Houdini version via enable, e.g.:<br/>
  `"enable": "houdini_version >= '21.0'"`

If anything is wrong, you’ll get actionable error messages.

### 3) Prepare your package folder
Your package folder typically looks like:

```
mypkg.json
mypkg/
  README.md       # required by uploader
  houdini/        # items in search path (otls, scripts, etc.)
  ...             # items you reference via $PCK_MYPKG
```

Required: `README.md` in the package directory.<br/>
Remove `getting-started.txt` after you follow its steps; uploads will refuse to proceed while it exists.

### 4) Upload (chunked, resumable)
```
hpackage author upload mypkg
# or use a JSON path: hpackage author upload /path/to/mypkg.json
```

* The CLI zips your JSON + package folder, computes MD5, starts an upload, and
  streams chunks.
* If an earlier attempt partially succeeded, it automatically resumes from the
  server-reported offset.
* Server-side checks verify the zip and JSON match the metadata, and then
  queues a security scan.
* On success, the CLI prints your package page URL.
* Pass `-i` (or `-–interactive`) to fill out the contents of README.md and
  delete getting-started.txt automatically.

Make the package require a grant to download
```
hpackage author upload mypkg --requires-grant
```
(You can later grant access and publish.)

### 5) Check status (as author)
```
hpackage author getstatus mypkg
```

Shows the most recent version and its state (e.g., scanning / reviewing /
reviewed / unsafe / published).

### 6) Grant access (for packages that require a grant)
```
hpackage author grant mypkg user1@example.com user2@example.com
```

### 7) Publish
```
hpackage author publish mypkg==1.2.3
```

Publishing requires:
* your package version to be reviewed and not flagged unsafe,
* all minimum dependency versions to be published.

### 8) Unpublish (time/usage limits may apply)
```
hpackage author unpublish mypkg==1.2.3
```

The server prevents you from unpublishing if it would break other published
packages depending on this version (subject to rules you’ll see as error
messages).

### 9) Delete a version
```
hpackage author delete mypkg==1.2.3
```

If it’s published, it will first be unpublished (and must pass the same safety
checks as above).

## Configuration & flags
* Verbosity: `-v 0|1|2|3` (default 2 but 3 if `HOUDINI_PACKAGE_VERBOSE` is set)
* Timeout: `--timeout <seconds>` (default 30)
* Server: `--server <url>` (intended for internal/testing use)

## Troubleshooting
* **“You are not logged in”**<br/>
  Run hpackage auth login (or use auth installkey to set an API key).
* **Upload refused due to getting-started.txt**<br/>
  Complete the steps in that file and delete it before uploading.
* **JSON validation errors**<br/>
  Use `hpackage author verifyjson` and follow the exact messages (e.g., env
  must be a list; enable must contain a quoted two-segment Houdini version like
  `"houdini_version >= '21.0'"`).

## Examples
```
# Install the latest version of a public package
hpackage install mushroomcloud
```

```
# Install a specific version
hpackage install mushroomcloud==2.3.1
```

```
# Install everything from a requirements file
hpackage install -r hrequirements.txt
```

```
# List installed packages (with locations)
hpackage list --show-location
```

```
# Uninstall
hpackage uninstall mushroomcloud
```

```
# Author flow
hpackage auth login
hpackage author reserve freetools
hpackage author verifyjson freetools
# (edit README.md, remove getting-started.txt, add files under
# freetools/)
hpackage author upload freetools
hpackage author getstatus freetools
# (wait until the status is “reviewed”)
hpackage author publish freetools
```

```
# Paid Content Author flow
hpackage auth login
hpackage author reserve paidtools
# (edit README.md, remove getting-started.txt, add files under
# paidtools/)
hpackage author upload paidtools --requires-grant
hpackage author getstatus paidtools
# (wait until the status is “reviewed”)
hpackage author publish paidtools
# (from your commerce website:)
hpackage author grant paidtools purchaser@example.com
```
