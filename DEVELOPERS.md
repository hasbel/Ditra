# Guidelines for developers

Author : Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

### Style

The current implementation mostly follows the pip8 guidelines, except for line 
length which is allowed to go up to 90chars when dividing the line reduces readability.

WARNING: Any non obvious function you add (I.e. most of them) should have a docstring!!

### Functionality

The main Ditra functionality is implemented in the handlers present in handlers.py.

The handlers are coded to handle object of type OFObject. Parsing the raw packet 
data to OFObjects is done through the module messages.py and based on the Loxi library.

### OF Version

To change the OF version used, update the files messages.py to use the needed part
of the Loxi library.

Attention: some message types change across OF version. Some classes might thus 
need to be updated. 