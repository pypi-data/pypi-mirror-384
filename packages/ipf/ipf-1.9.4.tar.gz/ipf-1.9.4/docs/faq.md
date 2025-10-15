# Frequently Asked Questions

## What does `no pid file` mean when starting workflows?
Not sure right now, but just check publishing status at
https://operations-api.access-ci.org/wh2/state/v1/status/
to see if the runs were published.

Also, check local process status with
```bash
bash ~/ipf/bin/wfm status
```


## How do I upgrade to the latest version?
See section "How can I start over from scratch" (below)


## How can I start over from scratch?
1. Stop any running workflows
   * ```bash
     bash ~/ipf/bin/wfm stop
     ```

1. Backup config files
   * ```bash
     bash ~/ipf/bin/save_configs.sh
     ```

1. Remove the install directory and script
   * ```bash
     rm -rf ~/ipf ~/ipf-setup.sh
     ```

1. Follow the [Installation Guide](install.md) again starting from the top

1. The backed up config files will have been restored. Generate the workflow
   files
   * ```bash
     bash ~/ipf/bin/configure_extmodules
     ```

1. Start the workflows
   * ```bash
     ~/ipf/bin/wfm start
     ```
1. Check the published data
   * See steps in [Configure Software Modules Publishing](configure-extmodules-workflow.md)


## Can I configure multiple workflows of the same type?
Yes!  The `configure_extmodules` script will look for config files matching the
naming convention `configure_extmodules*.conf`. You can create multiple config
files and a workflow definition will be created for each one. Just make sure
that `RESOURCE_NAME` is unique in each config file.


## How can I backup my workflow configs?
1. Backup workflow configs
   * ```bash
     bash ~/ipf/bin/save_configs.sh
     ```
This will do 2 things:
* make backup copies in `~/.config/ipf/`
* create symlinks to the backup copies in the ipf install dir.

On a re-install, the IPF installer will look for any backed up
config files and re-make the symlnks.
