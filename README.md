# Personal Agent Toolkit

My deployment repository for the skills, MCP settings, hooks, and agents I use across multiple devices. [Skillshare](https://github.com/runkids/skillshare) manages the collection and distributes resources to my AI tools; Git keeps the shared files in sync between machines.

Personal skill sources currently live in [enihsyou/dotfiles](https://github.com/enihsyou/dotfiles). This repository brings those skills together with vendor resources for deployment.

## Usage

1. Install Skillshare using its [setup instructions](https://github.com/runkids/skillshare#readme).
2. Clone this repository into Skillshare's storage directory. On Windows, I use `%APPDATA%/skillshare`.
3. Configure each device's source paths and target tools in the local `config.yaml`, with `git_root: root`.
4. Deploy the collection:

   ```sh
   skillshare sync --all -g
   ```

After publishing changes from one device, update another with:

```sh
skillshare pull
skillshare sync --all -g
```

`config.yaml` is excluded from Git. Paths, target selections, and any MCP or hook definitions stored there must be configured on each device. Only files tracked in this repository travel between devices.

Make personal skill changes in their source repository, then update the deployed copies here.

## Vendor skill modifications

No manual modifications currently.

Record future vendor skill edits here with the skill name, affected files, reason for the change, and upstream version or commit. Keep this record current when updating vendor skills.
