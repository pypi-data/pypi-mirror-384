# Configuring IPF

To make configuration easier, an `ipf_configure` script is
provided in the bin directory (~/bin/ipf_configure).


If you intend to publish software module information via the extmodules 
workflow, set the environment variable MODULEPATH
to point to the location of the module files before running
ipf_configure. If you intend to publish the service workflow
set SERVICEPATH to point to the location of the service definition files
before running ipf_configure (more on this below).
As of IPF v 1.7, ipf_configure accepts command line parameters
to tell it which workflows to configure, and with which options.


An invocation of ipf_configure on a resource that wants to publish software
information might look like:

```
/usr/bin/ipf_configure --resource_name <RESOURCE_NAME> --workflows=extmodules --publish --amqp_certificate /etc/grid-security/cert_for_ipf.pem --amqp_certificate_key /etc/grid-security/key_for_ipf.pem  --modulepath /path/to/modules --lmod_cache_file /path/to/lmodcache.lua
```

These options mean:
- `--resource_name`
  - The name of your resource. To find your resource name, go to "https://operations.access-ci.org/resources/access-allocated" to find your resource, and use the "Global Resource ID" value.

- `--workflows`
  - Comma delimited list of workflows to configure.  Values can include:
    - compute
    - activity
    - extmodules
    - services

- `--publish`
  - Necessary if you wish to configure your workflow to publish to ACCESS's AMQP service for inclusion in Information Services

- `--amqp_certificate`
  -The path to the certificate to use to authenticate with ACCESS’s AMQP

- `--amqp_key`
  - The path to the key for your certificate

- `--modulepath`
  - The MODULEPATH where the modulefiles for software publishing are found.  If not specified $MODULEPATH from the user environment will be used.

- `--lmod_cache_file`
  - The location of an lmod cache file that contains exactly the set of modules you wish to publish.  If you do not specify an lmod_cache_file, IPF will fall back to its traditional behavior of walking the MODULEPATH.


Other common options:

- `--amqp_username`
- `--amqp_password`
  - If not using certificates to authenticate, use these to specify username and password

For a full list of command line options, please try
```
ipf_configure --help
```

Execute:
```
ipf_configure \<command line options shown above\>
```

If you encounter any errors or the script does not cover your situation,
Please submit an ACCESS ticket.

When the script exits, the etc/ipf/workflow/glue2/ directory will
contain a set of files named RESOURCE_NAME.json that describe the
information gathering workflows you have configured and etc/ipf/init.d
will contain ipf-RESOURCE_NAME files which are the init scripts you
have configured.

As root, copy the init scripts into `/etc/init.d`.
Your information gathering workflows can then be enabled,
started, and stopped in the usual ways. You may need to perform a
`chkconfig --add` or equivalent for each service.


### Notes

-   `ipf_configure` should be run as the user that will run the
    information gathering workflows

-    You must always specify --resource_name, and you should use the 
     "Global Resource ID" from 
     https://operations.access-ci.org/resources/access-allocated 


-   The preferred way to authenticate is via an X.509 host certificate
    and key. You can place these files wherever you like, but the
    default locations are /etc/grid-security/xdinfo-hostcert.pem and
    /etc/grid-security/xdinfo-hostkey.pem. These files must be readable
    by the user that runs the information gathering workflows.


-   Submit an ACCESS ticket to authorize your server to publish ACCESS's
    RabbitMQ services. If you will authenticate via X.509, include the
    output of 'openssl x509 -in path/to/cert.pem -nameopt RFC2253
    -subject -noout' in your ticket. If you will authenticate via
    username and password, state that and someone will contact you.
