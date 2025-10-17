import os

os.environ['DATABASE_HOST'] = 'edh01.ornl.gov'
os.environ['DATABASE_PORT'] = '5435'
os.environ['DATABASE_USER'] = 'service_account'
os.environ['DATABASE_PW'] = 'EDH01c_her!!202503'
os.environ['DATABASE_DB'] = 'c_her_dev'

from pygarden.database import Database
from pygarden.mixins.postgres import PostgresMixin

class TestingFeature(PostgresMixin, Database):
    pass

if __name__ == '__main__':
    with TestingFeature() as db:
        x = db.query('SELECT 1')
        print(x)
