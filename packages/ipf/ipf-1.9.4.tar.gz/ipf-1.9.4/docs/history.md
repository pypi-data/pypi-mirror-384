# History of IPF

The Information Publishing Framework (IPF) is a generic framework used by resource operators to gather and publish dynamic resource information in [GLUE 2 serialized format](http://www.ogf.org/documents/GFD.147.pdf). IPF was used by the TeraGrid, XSEDE, XSEDE 2, and is now currently being used by the ACCESS-CI program to publish high-performance compute cluster information.

IPF gathers and publishes information using simple workflows. These workflows are defined using JSON (see the etc/workflows directory) and steps in the workflows are implemented as Python classes. Each step in the workflow can require input Data, can produce output Data, and can publish Representations of Data. A typical workflow consists of a number of information gathering steps and a few steps that publish representations to
files or to remote services (e.g. REST, messaging).

Workflow steps specify what Data they require and what Data they produce. This allows IPF to construct workflows based on partial information - in the case where there are not steps that produce the same Data, an entire workflow can be constructed from a single publish step and its required input Data. At the other extreme, workflows can be exactly specified with specific steps identified and the outputs of steps bound to the inputs of other steps. A typical workflow (e.g. GLUE 2) specifies what steps to include but lets IPF automatically link outputs to inputs of these steps.

Workflows can run to completion relatively quickly or they can continuously run. The first type of workflow can be used to run a few commands or look at status files and publish that information. The second type of workflow can be used to monitor log files and publish entries written to those files. Workflows are typically run periodically as cron jobs. The program run_workflow.py is for executing workflows that complete quickly and the program run_workflow_daemon.py is used to manage long-running workflows.
