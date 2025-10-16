"""
Module for signal processing related LazyLinOps (work in progress).
"""
import warnings
warnings.simplefilter(action='always')


try:
    from dask.distributed import Client, LocalCluster
except ImportError:
    print("Dask ImportError")


def create_dask_cluster_and_client(nworkers: int=2, memory: str='1GiB'):
    """Create and return cluster and client dask.distributed.

    Args:
        nworkers: int, optional
        Number of workers to use by dask.distributed (2 is default)
        memory: str, optional
        Memory limit per worker ('1GiB' is default)

    Returns:
        tuple
        dask.distributed.client, dask.distributed.cluster

    Example:
        >>> from lazylinop.wip.code_optimization import create_dask_cluster_and_client
        >>> cluster, client = create_dask_cluster_and_client(nworkers=8, memory='2GiB')
    """
    # with LocalCluster(n_workers=nworkers, processes=True, threads_per_worker=1, memory_limit=memory) as cluster:
    #     print(cluster)
    #     with Client(cluster) as client:
    #         print(client)
    #         return cluster, client
    cluster = LocalCluster(n_workers=nworkers, processes=True, threads_per_worker=1, memory_limit=memory)
    print(cluster)
    client = Client(cluster)
    print(client)
    return cluster, client


def close(client=None, cluster=None):
    if client is not None:
        client.close()
    if cluster is not None:
        cluster.close()
