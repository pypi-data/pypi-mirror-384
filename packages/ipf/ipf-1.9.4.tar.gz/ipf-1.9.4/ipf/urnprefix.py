import os
import sys


#default_urn_prefix = "urn:ogf:glue2:xsede.org:"
# from discussion w/ JP
default_urn_prefix = "urn:ogf.org:glue2:access-ci.org:"

if "IPF_URN_PREFIX" in os.environ:
    IPF_URN_PREFIX = os.environ["IPF_URN_PREFIX"]
else:
    IPF_URN_PREFIX = default_urn_prefix
