import os
import kfp

from typing import Optional
from kfp.client.token_credentials_base import TokenCredentialsBase
from ._utils import _load_context
from .login import login


KUBERNETES_TOKEN_FILENAME = "/var/run/secrets/kubernetes.io/serviceaccount/token"


def generate_client(
    host: Optional[str] = None,
    client_id: Optional[str] = None,
    namespace: str = "kubeflow",
    other_client_id: Optional[str] = None,
    other_client_secret: Optional[str] = None,
    existing_token: Optional[str] = None,
    cookies: Optional[str] = None,
    proxy: Optional[str] = None,
    ssl_ca_cert: Optional[str] = None,
    kube_context: Optional[str] = None,
    credentials: Optional[TokenCredentialsBase] = None,
    ui_host: Optional[str] = None,
    verify_ssl: Optional[bool] = None,
) -> kfp.Client:
    in_cluster = os.path.isfile(KUBERNETES_TOKEN_FILENAME)
    if not in_cluster:
        try:
            login(allow_existing_token=True)
        except Exception as e:
            error_msg = f"""
            Pipeline appears to be submitted from outside the cluster, attempted to login to Kubeflow, but failed to acquire an auth token with the error: {e}
            """
            raise Exception(e)

        host = host or os.environ.get("KF_PIPELINES_ENDPOINT_ENV", "")
        if not host:
            context, _ = _load_context()
            host = context.get("host", "")
        if not host:
            error_msg = """
            Pipeline appears to be submitted from outside the cluster, supply the pipelines host, either as an argument e.g generate_client(host=...), or by the KF_PIPELINES_ENDPOINT_ENV environment variable, or by the config json
            """
            raise Exception(error_msg)

        namespace = namespace or os.environ.get("KF_PIPELINES_NAMESPACE", "")
        if not namespace:
            context, _ = _load_context()
            namespace = context.get("namespace", "")
        if not namespace:
            error_msg = """
            Pipeline appears to be submitted from outside the cluster, supply the pipelines namespace, either as an argument e.g generate_client(namespace=...), or by the KF_PIPELINES_NAMESPACE environment variable, or by the config json
            """
            raise Exception(error_msg)

    kfp_client = kfp.Client(
        host,
        client_id,
        namespace,
        other_client_id,
        other_client_secret,
        existing_token,
        cookies,
        proxy,
        ssl_ca_cert,
        kube_context,
        credentials,
        ui_host,
        verify_ssl,
    )

    return kfp_client
