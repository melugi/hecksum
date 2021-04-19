"""
Call with the name of a ReferenceFactory to try it out.
$ python try_reference.py test_failure
"""
from pprint import pprint
import sys
from time import time

from hecksum import references

factory_name = sys.argv[1]
print(factory_name)
factory: references.ReferenceFactory = getattr(references, factory_name)
ref = factory.make()
pprint(ref.dict())
start = time()
download_checksum = ref.download_checksum()
print(time()-start)
print(f'{download_checksum = }')
print(f'Valid: {ref.checksum == download_checksum}')
