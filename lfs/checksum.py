# checksum.py - verify checksums

import sys
import hashlib
            
#-------------------------------------------------------------------------------
# Checksum - 
#-------------------------------------------------------------------------------

class Checksum():
    def __init__(self, type, value=None, pkgid=None):
        self.type = type
        self.pkgid = pkgid
        self.value = value
   
    #---------------------------------------------------------------------------
    # JSON encode/decode
    #---------------------------------------------------------------------------

    def to_json_encodable(self):
        """Create a json-encodable object representing this object."""
        # print('  Checksum: to_json_encodable')
        d = {}
        for k, v in self.__dict__.items():
            if not (v is None or v == '' or v == [] or v == {}):
                d[k] = v
        return d

    @classmethod
    def from_json_decoded(cls, obj):
        """Return a Checksum object from a json-decoded object."""
        d = {}
        # We iterate on the members actually present, ignoring absent ones.
        for k, v in obj.items():
            d[k] = v            
        return cls(**d)

    def __str__(self):
        return (f'checksum: type={self.type}, pkgid={self.pkgid}'
                    + f', value={self.value}\n')

    def to_csv(self):
        return f'{self.type}\t{self.pkgid}\t{self.value}'

    @classmethod
    def csv_header(cls):
        return f'type\tpkgid\tvalue'

    def check(self, filepath):
        sh = hashlib.__dict__[self.type]()
        with open(filepath, 'rb') as f:
            for data in iter(lambda: f.read(4096), b''):
                sh.update(data)
        # print(f'Checksum: expected={self.value}')
        # print(f'Checksum:   actual={sh.hexdigest()}')

        return self.value == sh.hexdigest()

    def get_hash(self, filepath):
        sh = hashlib.__dict__[self.type]()
        with open(filepath, 'rb') as f:
            for data in iter(lambda: f.read(4096), b''):
                sh.update(data)
        self.value = sh.hexdigest()
        return self.value

#===============================================================================
# main - 
#===============================================================================

if __name__ == '__main__':
    # print("""This module is not meant to run directly.""")

    # if len(sys.argv) != 4:
    #     print(f'Usage: {sys.argv[0]} <type> <filepath> <checksum-value>')
    #     print('Supported types include md5, sha1, sha256, sha512. See python hashlib doc')
    #     print('for the complete list of supported types.')
    #     exit(-1)
    # type = sys.argv[1]
    # filepath = sys.argv[2]
    # value = sys.argv[3]

    # c = Checksum(type, value)
    # print(f'checksum: {"ok" if c.check(filepath) else "NOK"}')

    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <type> <filepath>')
        print('Supported types include md5, sha1, sha256, sha512. See python hashlib doc')
        print('for the complete list of supported types.')
        exit(-1)
    type = sys.argv[1]
    filepath = sys.argv[2]

    c = Checksum(type)
    print(f'checksum: {c.get_hash(filepath)}')

