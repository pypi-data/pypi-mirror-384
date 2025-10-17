from datetime import timedelta
from typing import Union

from couchbase.auth import PasswordAuthenticator
from couchbase.bucket import Bucket
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions


class Couchbase:
    def __init__(self, password: str, username="Administrator", domain='localhost', tls=True):
        dialect = 'couchbases' if tls else 'couchbase'
        self.connection_string = f"{dialect}://{domain}"
        self.options = ClusterOptions(PasswordAuthenticator(
            username,
            password,
        ))
        self.connection: Union[Cluster, None] = None
        self.bucket: Union[Bucket, None]  = None

    def connect(self, bucket=None):
        self.connection = Cluster(self.connection_string, self.options)
        self.connection.wait_until_ready(timedelta(seconds=5))
        if bucket is not None:
            self.bucket = self.connection.bucket(bucket)
