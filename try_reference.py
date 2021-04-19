"""
Call with the name of a ReferenceFactory to try it out.
"""
from pprint import pprint
import sys

from hecksum import references

factory_name = sys.argv[1]
print(factory_name)
factory: references.ReferenceFactory = getattr(references, factory_name)
ref = factory.make()
pprint(ref.dict())
download_checksum = ref.download_checksum()
print(f'{download_checksum = }')
print(f'Valid: {ref.checksum == download_checksum}')