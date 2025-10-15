import tempfile
import os, os.path
import uuid

# Debug flag
IS_DEBUG = True


class GatewayServerImplementation:
    """
    Implementation that should be moved within the server component, so instead of:
    client -> GatewayProjectBackend -> GatewayServerImpl -> execution
    it should be
    client -> GatewayProjectBackend -> REST -> GatewayServerImpl -> execution
    """

    def __init__(self):
        # TODO: The spool directory should be read but not write accessible from service user on the compute nodes
        #       this is to prevent userA modifying with userB's inputs (on purpose or not). It's probably better to make
        #       it so the slurm script has a shared secret or something that lets it curl the tarball from the server
        self.spool_path = tempfile.mkdtemp()
        self.tarball_path = os.path.join(self.spool_path, "input_spool")
        os.mkdir(self.tarball_path)

    def __del__(self):
        """
        Sloppy, I know, but only needed for local testing
        """
        if not IS_DEBUG:
            if hasattr(self, "spool_path") and os.exists(self.spool_path):
                os.rmdir(self.spool_path)

    # Expose externally
    def enqueue_run(
        self,
        tarball_path,
        entry_point,
        params,
        backend_config,
        tracking_uri,
        experiment_id,
        user_subj="",
    ):
        """
        Takes the user request, then submits to a job backend on their behalf (either local or SLURM)

        :param tarball_path: Path to the users' sandbox
        :param entry_point: Entry point to execute (from MLProject config)
        :param params: Paramaters to pass to task (from MLProject config)
        :param backend_config: MLTF backend config, hardware requests, etc.. (from MLProject config)
        :param tracking_uri: What URI to use to send MLFlow logging (from client env if provided, default set otherwise)
        :param experiment_id: What experiment to group this run under (from client if provided)
        :param user_subj: Subject of the user submitting task (string) (from REST layer)
        :return: A SubmittedRun describing the asynchronously-running task
        """
        # First, parse the backend_config to figure out what SLURM parameters we want to use
        # FIXME: Fill stub out more, need to set MLFLOW magic variables, etc..
        slurm_params = {"job_name": "mltf_sub", "time": 120}

        # Next, store the tarball somewhere securely. This must *not* be writable by the service users for the reason
        # explained in __init__
        target_name = str(uuid.uuid4())
        target_path = os.path.join(self.tarball_path, target_name)
        os.chmod(tarball_path, 644)
        os.rename(tarball_path, target_path)

        pass

    def generate_wrapper(self):
        ret = """#!/bin/sh
# FIXME: A lot of this can be done once per-cluster and not per-job, but trying to simplify things
mkdir -p mltf-runtime
cd mltf-runtime
(
    # Download
    flock -s 200   
    current_time=$(date +%s)
    git_dir="pyenv"

    if [ -d "$git_dir" ]; then
        git_mod_time=$(stat -c %Y "$git_dir")
    else
        echo "Git directory not found. Cloning instead."
        git clone https://github.com/pyenv/pyenv pyenv
        git_mod_time=${current_time}
    fi

    time_diff=$((current_time - git_mod_time))

    if [ $time_diff -gt 86400 ]; then
        echo "Performing git pull..."
        git pull
    else
        echo "Last pull was within the last 24 hours. Skipping."
    fi

) 200>mltf-lockfile

SCRATCH="$(mkdtemp -d)"
# FIXME: Don't delete temp dirs while still testing
# trap 'rm -rf "$SCRATCH" EXIT
cd $SCRATCH

# Install an environment for the wrapper (so we don't have to use bash for all this)
python3 -m venv wrapper-venv
source wrapper-venv/bin/activate
pip install mlflow-skinny

mkdir sandbox
cd sandbox
tar xf %s{tarball_path} .
mlflow run . - %s{entry_point}
"""


# Global implementation variable, used so __del__ works
server_impl = GatewayServerImplementation()
