from imerit_ango.models.enums import StorageProvider


class Storage:
    def __init__(self, name: str, provider: StorageProvider, public_key: str = None, private_key: str = None,
                 region: str = 'eu-central-1',
                 credentials: str = None):
        self.name = name
        self.provider = provider
        self.publicKey = public_key
        self.privateKey = private_key
        self.region = region
        self.credentials = credentials

    def to_dict(self):
        return {
            'name': self.name,
            'provider': self.provider.value,
            'publicKey': self.publicKey,
            'privateKey': self.privateKey,
            'region': self.region,
            'credentials': self.credentials
        }
