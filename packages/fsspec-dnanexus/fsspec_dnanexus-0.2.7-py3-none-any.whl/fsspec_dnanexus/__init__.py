import os
import dxpy

from .core import DXFileSystem, \
                DXFileSystemException, \
                DXPathExtractor, \
                DXBufferedFileOnRay, \
                DXBufferedFile, \
                logger

from .factories import dxfactory

__version__ = "0.2.7"

def init_for_modin_on_ray(n_partitions: int = None):
    def init_ray_cluster() -> None:
        import ray._private.services as services
        
        dx_job_id = os.environ.get('DX_JOB_ID')
        try:
            # check if ray can connect any running Ray instance
            services.get_ray_address_from_environment("auto", None)

            if ray.is_initialized():
                return

            ray.init(address="auto",
                _node_ip_address=dxpy.describe(dx_job_id)['host'] if dx_job_id else services.get_node_ip_address(),
                runtime_env={'env_vars': {'__MODIN_AUTOIMPORT_PANDAS__': '1'}},
            )
        except ConnectionError as e:
            import re
            
            msg = str(e)
            if re.match(r".*(Could not read '.*' from GCS. Did GCS start successfully).*", msg):
                logger.warn(f"Ray failed to start. {str(e)}. To check if Ray is running, please run the command line `ray status`.")
                logger.warn("If you run `ray start --head` in the cell of Jupyter notebook, please run it in terminal instead!")
            else:
                logger.debug(msg)
    
    try:
        import ray
        
        init_ray_cluster()

        # set NPartitions
        if n_partitions is not None:
            import modin.config as cfg
            cfg.NPartitions.put(n_partitions)
        
        logger.info("Provision Pandas on Ray")
        dxfactory.provision_dx_on_ray()

    except ModuleNotFoundError as e:
        if "ray" in str(e):
            logger.info("Provision Pandas on Python")
            dxfactory.provision_dx_on_python()
        else:
            raise e

