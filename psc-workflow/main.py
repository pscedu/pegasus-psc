#!/usr/bin/env python3
##!/usr/bin/python3

"""
Sample Pegasus workflow for training a model on the Cerebras resource
at Neocortex.

This workflow validates, compiles and trains the model as part
of a single worklfow setup to run on Neocortex.

https://portal.neocortex.psc.edu/docs/running-jobs.html
"""

import argparse
import datetime
import getpass
import logging
import os
import shutil
import sys

from Pegasus.api import Container, Grid, Scheduler, SupportedJobs
from Pegasus.api import Directory
from Pegasus.api import File
from Pegasus.api import FileServer
from Pegasus.api import Job
from Pegasus.api import Operation
from Pegasus.api import Properties
from Pegasus.api import ReplicaCatalog
from Pegasus.api import Site
from Pegasus.api import SiteCatalog
from Pegasus.api import Transformation
from Pegasus.api import TransformationCatalog
from Pegasus.api import Workflow
from Pegasus.client._client import PegasusClientError

logging.basicConfig(level=logging.DEBUG)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# need to know where Pegasus is installed for notifications
PEGASUS_HOME = shutil.which("pegasus-version")
PEGASUS_HOME = os.path.dirname(os.path.dirname(PEGASUS_HOME))

# generate a new ssh key (without any password) for the workflows
# ssh-keygen -t ed25519 -f ~/.pegasus/wfsshkey -C "key for pegasus workflows"
# add wfsshkey.pub to your authorized keys on bridges2
# WF_SSH_KEY_PATH = os.path.expanduser("~") + "/.pegasus/wfsshkey"
USER = getpass.getuser()

NEOCORTEX_SITE_HANDLE = "neocortex"
BRIDGES2_SITE_HANDLE = "bridges2"

DUMMY="dummy/"  # Set to "" when switching to use the real files.
# from IPython.display import Image; Image(filename='graph.png')


class CerebrasPyTorchWorkflow:

    # --- Init ---------------------------------------------------------------------
    def __init__(self, project=None):
        self.workflow = None
        self.site_catalog = None
        self.transformation_catalog = None
        self.replica_catalog = None
        self.properties = None
        self.workflow_name = "psc-workflow"
        self.project = project
        # Log
        self.log = logging.getLogger(__name__)

    # --- Write files in directory -------------------------------------------------
    def write(self):
        if not self.site_catalog is None:
            self.site_catalog.write()
        self.properties.write()
        self.replica_catalog.write()
        self.transformation_catalog.write()

        try:
            self.workflow.write()
        except PegasusClientError as e:
            print(e)

    # --- Plan and Submit the workflow ----------------------------------------------
    def plan_submit(self):
        try:
            self.workflow.plan(
                conf="pegasus.properties",
                sites=[NEOCORTEX_SITE_HANDLE, ],  # BRIDGES2_SITE_HANDLE],
                output_site="local",
                dir="submit",
                cleanup="none",
                force=True,
                verbose=5,
                submit=True,
            )
        except PegasusClientError as e:
            print(e)

    # --- Get status of the workflow -----------------------------------------------
    def status(self):
        try:
            self.workflow.status(long=True)
        except PegasusClientError as e:
            print(e)

    # --- Wait for the workflow to finish -----------------------------------------------
    def wait(self):
        try:
            self.workflow.wait()
        except PegasusClientError as e:
            print(e)

    # --- Get statistics of the workflow -----------------------------------------------
    def statistics(self):
        try:
            self.workflow.statistics()
        except PegasusClientError as e:
            print(e)

    # --- Configuration (Pegasus Properties) ---------------------------------------
    def create_pegasus_properties(self):
        self.properties = Properties()
        self.properties["pegasus.integrity.checking"] = "none"
        self.properties[
            "pegasus.catalog.workflow.amqp.url"
        ] = "amqp://friend:donatedata@msgs.pegasus.isi.edu:5672/prod/workflows"
        self.properties["pegasus.data.configuration"] = "nonsharedfs"
        self.properties["pegasus.mode"] = "development"
        # data transfers for the jobs should happen
        # on the HOSTOS not inside the container
        self.properties["pegasus.transfer.container.onhost"] = True
        # we dont want any pegasus worker package
        # to be installed inside the container
        self.properties["pegasus.transfer.worker.package"] = True
        self.properties["pegasus.transfer.worker.package.autodownload"] = False
        # enable symlinking
        # props["pegasus.transfer.links"] = True
        self.properties.write()
        return

    # --- Site Catalog -------------------------------------------------------------
    def create_sites_catalog(self):
        self.site_catalog = SiteCatalog()
        # add a local site with an optional job env file to use for compute jobs
        shared_scratch_dir = "/{}/workflows/LOCAL/scratch".format("${PROJECT}")
        local_storage_dir = "{}/storage".format(BASE_DIR)
        local = Site("local").add_directories(
            Directory(Directory.SHARED_SCRATCH, shared_scratch_dir).add_file_servers(
                FileServer("file://" + shared_scratch_dir, Operation.ALL)
            ),
            Directory(Directory.LOCAL_STORAGE, local_storage_dir).add_file_servers(
                FileServer("file://" + local_storage_dir, Operation.ALL)
            ),
        )
        # TODO review line: local.add_pegasus_profile(SSH_PRIVATE_KEY=WF_SSH_KEY_PATH)
        self.site_catalog.add_sites(local)

        # the neocortex site
        shared_scratch_dir = "/{}/workflows/NEOCORTEX/scratch".format("${PROJECT}")
        local_scratch_dir = "/local4/{}".format("${SALLOC_ACCOUNT}")
        neocortex = Site(NEOCORTEX_SITE_HANDLE).add_directories(
            Directory(
                Directory.SHARED_SCRATCH, shared_scratch_dir, shared_file_system=True
            ).add_file_servers(FileServer("file://" + shared_scratch_dir, Operation.ALL)),
            Directory(Directory.LOCAL_SCRATCH, local_scratch_dir).add_file_servers(
                FileServer("file://" + local_scratch_dir, Operation.ALL)
            ),
        )
        neocortex.add_condor_profile(grid_resource="batch slurm")
        # TODO, review:
        #    neocortex.add_env("PEGASUS_HOME", "/ocean/projects/cis240026p/vahi/software/install/pegasus/default")
        neocortex.add_pegasus_profile(
            style="glite",
            queue="sdf",
            auxillary_local=True,
            runtime=1800,
            project=self.project,
        )
        self.site_catalog.add_sites(neocortex)

        # bridges2 site
        shared_scratch_dir = "/{}/workflows/BRIDGES/scratch".format("${PROJECT}")
        login_host = "bridges2.psc.edu"
        bridges2 = Site(BRIDGES2_SITE_HANDLE).add_directories(
            Directory(
                Directory.SHARED_SCRATCH, shared_scratch_dir, shared_file_system=True
            ).add_file_servers(FileServer("file:///" + shared_scratch_dir, Operation.ALL))
        )
        bridges2.add_grids(
            Grid(grid_type=Grid.BATCH, scheduler_type=Scheduler.SLURM, contact=login_host,
                 job_type=SupportedJobs.COMPUTE)
        )
        # TODO: Update PEGASUS_HOME path.
        bridges2.add_env("PEGASUS_HOME", "/ocean/projects/cis240026p/vahi/software/install/pegasus/default")
        bridges2.add_pegasus_profile(
            style="ssh",
            queue="RM-shared",
            auxillary_local=True,
            runtime=1800,
            project=self.project,
        )
        self.site_catalog.add_sites(bridges2)

    # --- Transformation Catalog (Executables and Containers) ----------------------
    def create_transformation_catalog(self):
        self.transformation_catalog = TransformationCatalog()
        container = Container(
            name="cerebras",
            container_type=Container.SINGULARITY,
            image="file:///ocean/neocortex/cerebras/cbcore_latest.sif",
            image_site=NEOCORTEX_SITE_HANDLE,
        )
        self.transformation_catalog.add_containers(container)

        step1_pretrain = Transformation(
            name="step1_pretrain",
            site="local",
            # TODO review differences between local and notlocal: site="notlocal",
            pfn=BASE_DIR + f"/step1/{DUMMY}run_pretrain.sh",
            is_stageable=True,
            container=container,
        )
        step1_pretrain.add_pegasus_profiles(cores=1, runtime="300",
                                            container_launcher="srun",
                                            container_launcher_arguments="--kill-on-bad-exit",
                                            glite_arguments="--cpus-per-task=14")
        self.transformation_catalog.add_transformations(step1_pretrain)

        step2_regression = Transformation(
            name="step2_regression",
            site="local",
            pfn=BASE_DIR + f"/step2/{DUMMY}run_regression.sh",
            is_stageable=True,
            container=container,
        )
        step2_regression.add_pegasus_profiles(cores=1, runtime="300",
                                              container_launcher="srun",
                                              container_launcher_arguments="--kill-on-bad-exit",
                                              glite_arguments="--cpus-per-task=14")
        self.transformation_catalog.add_transformations(step2_regression)

        step3_inference = Transformation(
            name="train",
            site="local",
            pfn=BASE_DIR + f"/step3/{DUMMY}run_inference",
            is_stageable=True,
            container=container,
        )
        step3_inference.add_pegasus_profiles(cores=1, runtime="300",
                                             container_launcher="srun",
                                             container_launcher_arguments="--kill-on-bad-exit",
                                             glite_arguments="--cpus-per-task=14")
        self.transformation_catalog.add_transformations(step3_inference)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        self.replica_catalog = ReplicaCatalog()
        # most of the replicas are added when creating the workflow

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.workflow = Workflow(self.workflow_name)

        # --- Workflow -----------------------------------------------------
        # the input files required for the workflow are tracked in the Replica Catalog.
        # TODO: Switch file name
        modelzoo_config_params = File(
            "modelzoo/modelzoo/fc_mnist/pytorch/configs/params.yaml"
        )
        # TODO: Switch file name
        modelzoo_raw = File("modelzoo-raw.tgz")

        # TODO: Update path
        self.replica_catalog.add_replica(
            "local", modelzoo_config_params.lfn, "{}/input/params.yaml".format(BASE_DIR)
        )

        # TODO: Update path
        self.replica_catalog.add_replica(
            "local", modelzoo_raw.lfn, "{}/input/modelzoo-raw.tgz".format(BASE_DIR)
        )

        # some output of modelzoo checkout at each stage
        modelzoo_validated = File("modelzoo-validated.tgz")
        modelzoo_compiled = File("modelzoo-compiled.tgz")
        modelzoo_trained = File("modelzoo-trained.tgz")
        modelzoo_trained_checkpoints = File("model-checkpoints.tgz")

        # some logs that we always stageout
        cerebras_logs = ["fabric.json", "run_summary.json", "params.yaml"]

        # validate job
        validate_job = Job("validate", node_label="validate_model")
        validate_job.add_args(
            "--mode train --validate_only --params configs/params.yaml  --model_dir model"
        )
        validate_job.add_inputs(modelzoo_raw)
        validate_job.add_inputs(modelzoo_config_params)
        validate_job.add_outputs(modelzoo_validated, stage_out=True)
        # add files against which we will train as inputs
        # instead of letting the code download automatically
        prefix = "modelzoo/modelzoo/fc_mnist/pytorch/data/mnist/train/MNIST/raw"
        for file in [
            "train-images-idx3-ubyte.gz",
            "train-labels-idx1-ubyte.gz",
            "t10k-images-idx3-ubyte.gz",
            "t10k-labels-idx1-ubyte.gz",
        ]:
            train_file = File("{}/{}".format(prefix, file))
            self.replica_catalog.add_replica(
                "nonlocal",
                train_file.lfn,
                "http://yann.lecun.com/exdb/mnist/{}".format(file),
            )
            self.replica_catalog.add_replica(
                "nonlocal",
                train_file.lfn,
                "https://ossci-datasets.s3.amazonaws.com/mnist/{}".format(file),
            )
            validate_job.add_inputs(train_file)

        # track some cerebras log files as outputs
        for file in cerebras_logs:
            # scripts do rename of the files after job completes
            validate_job.add_outputs(File("{}_{}".format("validate", file)), stage_out=True)

        self.workflow.add_jobs(validate_job)

        # compile job
        compile_job = Job("compile", node_label="compile_model")
        compile_job.add_args(
            "--mode train --compile_only --params configs/params.yaml --model_dir model"
        )
        compile_job.add_inputs(modelzoo_validated)
        compile_job.add_outputs(modelzoo_compiled, stage_out=True)

        # track some cerebras log files as outputs
        for file in cerebras_logs:
            # scripts do rename of the files after job completes
            compile_job.add_outputs(File("{}_{}".format("compile", file)), stage_out=True)

        self.workflow.add_jobs(compile_job)

        # training job
        now = datetime.datetime.now().strftime("%s")
        training_job = Job("train", node_label="train_model")
        training_job.add_args(
            "--mode train --params configs/params.yaml --model_dir model --cs_ip $CS_IP_ADDR"
        )
        training_job.add_inputs(modelzoo_compiled)
        training_job.add_outputs(modelzoo_trained, stage_out=True)
        training_job.set_stdout("train-{}.out".format(now))
        training_job.set_stderr("train-{}.err".format(now))

        # track some cerebras log files as outputs
        for file in cerebras_logs:
            # scripts do rename of the files after job completes
            if file == "fabric.json":
                # we dont copy fabric.json
                continue
            training_job.add_outputs(File("{}_{}".format("train", file)), stage_out=True)

        training_job.add_outputs(File("train_performance.json"), stage_out=True)
        self.workflow.add_jobs(training_job)

    def __call__(self):
        self.log.info("Creating workflow properties...")
        self.create_pegasus_properties()

        self.log.info("Creating execution sites...")
        self.create_sites_catalog()

        self.log.info("Creating transformation catalog...")
        self.create_transformation_catalog()

        self.log.info("Creating replica catalog...")
        self.create_replica_catalog()

        self.log.info("Creating workflow ...")
        self.create_workflow()

        self.write()
        self.log.info("Workflow has been created. Will be planned and submitted ...")

        self.plan_submit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Generate a sample multi-cluster Pegasus workflow at PSC")
    parser.add_argument('--project', dest='project', default=None, required=True,
                        help='Specifies the project/grantid of your project')
    args = parser.parse_args(sys.argv[1:])
    wf = CerebrasPyTorchWorkflow(project=args.project)
    try:
        wf()
    except PegasusClientError as e:
        wf.log.debug("", exc_info=True)
        print(e.output)
        sys.exit(1)
    except Exception:
        wf.log.debug("", exc_info=True)
        sys.exit(1)
