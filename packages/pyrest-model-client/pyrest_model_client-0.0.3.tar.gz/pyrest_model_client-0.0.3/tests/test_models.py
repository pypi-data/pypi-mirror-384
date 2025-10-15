from example_usage.models.environment import Environment
from example_usage.models.user import User
from pyrest_model_client.base import BaseAPIModel


def test_user_model_inheritance():
    user = User(name="a", email="a@b.com")
    assert isinstance(user, BaseAPIModel)
    assert user._resource_path == "user"  # pylint: disable=W0212


def test_environment_model_inheritance():
    env = Environment(name="dev")
    assert isinstance(env, BaseAPIModel)
    assert env._resource_path == "environment"  # pylint: disable=W0212
