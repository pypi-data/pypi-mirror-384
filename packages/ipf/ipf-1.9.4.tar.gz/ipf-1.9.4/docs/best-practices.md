# Software Module Publishing Best Practices


The IPF Software Module workflow publishes information about locally
installed software available through modules or Lmod. IPF tries to make
intelligent inferences from the system installed modules files when it
publishes software information. There are some easy ways, however, to
add information to your module files that will enhance/override the
information otherwise published.


The ExtModules workflow, as of IPF 1.8 has two methods for discovering the 
modules you wish to publish.  The recommended method, for any site using Lmod, 
is to point the workflow at an lmod cache file that represents exactly what
you wish to publish.  It will then publish every module in the spiderT table
from the cache file, except modules listed in the hiddenT table.

If you are not using Lmod, or do not wish to use lmod cache files, the
workflow will fall back to the traditional method of walking the MODULEPATH.
The workflow then traverses your MODULEPATH and infers fields such
as Name and Version from the directory structure/naming conventions of
the module file layout. IPF default behavior is to treat each 
directory in your MODULEPATH as a top level directory, under which all of
the subdirectory structure is semantically significant (and part of the
inferred name of the module).  An alternative behavior, if desired, can be
enabled with by configuring the extmodules workflow with the --modules_recurse
argument. (TODO: Define the alternative behavior?)

Depending on the exact workflow steps, fields such as Description may be 
blank, or inferred from the stdout/stderr text of the module. However, the 
following fields can always be explicitly added to a module file:

    Name:
    Version:
    Description:
    URL:
    Category:
    Keywords:
    SupportStatus:
    SupportContact:


Each field is a key: value pair. The IPF workflows are searching the
whole text of each module file for these fields. They may be placed in a
module-whatis line, or in a comment, and IPF will still read them.
