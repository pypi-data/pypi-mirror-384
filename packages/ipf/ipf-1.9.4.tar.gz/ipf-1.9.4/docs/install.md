# Install
1. Get the setup script
    ```
    curl -o ~/ipf-setup.sh https://raw.githubusercontent.com/access-ci-org/ipf/refs/heads/master/setup.sh
    ```

1. Run the setup script
    ```
    bash ~/ipf-setup.sh
    ```
Installs into `~/ipf`.

Next: [Configure workflows](configure-extmodules-workflow.md)

# Advanced

## Custom Options

### Customize installation dir
* Set and export environment variable IPF_INSTALL_DIR (before running
  `ipf-setup.sh`)
Note: The default install dir is `~/ipf`. Remember to replace `~/ipf`
with `$IPF_INSTALL_DIR` in all the commands referenced in the docs.
