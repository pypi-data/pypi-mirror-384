"""
认证相关命令
"""
from mando import command, arg
from ketacli.sdk.base.client import do_login, do_logout
from ketacli.sdk.base.config import list_clusters


@command
def login(name="keta", endpoint="http://localhost:9000", token=""):
    """Login to ketadb, cache authentication info to ~/.keta/config.yaml

    :param repository: Repository to push to.
    :param -n, --name: The login account name. Defaults to "keta".
    :param -e, --endpoint: The ketadb endpoint. Defaults to "http://localhost:9000".
    :param -t, --token: Your keta api token, create from ketadb webui. Defaults to "".
    """
    do_login(name=name, endpoint=endpoint, token=token)


@command
@arg("name", type=str,
     completer=lambda prefix, **kwd: [x['name'] for x in list_clusters() if x['name'].startswith(prefix)])
def logout(name=None):
    """Logout from ketadb, clear authentication info

    :param -n, --name: logout from which account
    """
    do_logout(name)