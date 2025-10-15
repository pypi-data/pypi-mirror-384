# IPF - Information Publishing Framework

## Overview

IPF is a Python program that gathers resource information, formats it in a [GLUE2 standard format (5)](#glue2), and publishes it to a RabbitMQ service. IPF is configured to run one or more “workflows” each defining the steps that IPF executes to collect, format, and publish a specific type of resource information.


## Quickstart

#### Install
1. [Installation Guide](docs/install.md)

#### Configure Workflows
1. [Configure Software Modules Publishing](docs/configure-extmodules-workflow.md)
1. ( other workflows coming soon )

## Additional Information

* [Best practices for reporting accurate Software Module information](docs/best-practices.md)
* [FAQ](docs/faq.md)

## Support Information

This software is currently maintained by the ACCESS CONECT project.

The source is maintained in the [ACCESS-CI GitHub](https://github.com/access-ci-org/ipf).  ACCESS-CI resource providers and other members of the ACCESS-CI community are encourage to contribute bug fixes and improvements.

Software bugs may be reported as GitHub issues.  ACCESS-CI related support requests should be submitted through the ACCESS-CI ticket system.

## License

[LICENSE](LICENSE)

## Acknowledgements

This work was supported by the TeraGrid, XSEDE, FutureGrid, XSEDE 2, and ACCESS CONECT projects under
National Science Foundation grants 0503697, 1053575, 0910812, 1548562, and 2138307.
