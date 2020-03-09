from frame.app import create_app
from frame.tasks.database import api_init


def test_api_init():
    app = create_app()
    api_init(app, [])
