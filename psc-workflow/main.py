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
        self.site_catalog = SiteCatalog()
        self.transformation_catalog = TransformationCatalog()
        self.replica_catalog = ReplicaCatalog()
        self.properties = None
        self.workflow_name = "psc-workflow"
        self.workflow = Workflow(name=self.workflow_name)
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

        # # bridges2 site
        # shared_scratch_dir = "/{}/workflows/BRIDGES/scratch".format("${PROJECT}")
        # login_host = "bridges2.psc.edu"
        # bridges2 = Site(BRIDGES2_SITE_HANDLE).add_directories(
        #     Directory(
        #         Directory.SHARED_SCRATCH, shared_scratch_dir, shared_file_system=True
        #     ).add_file_servers(FileServer("file:///" + shared_scratch_dir, Operation.ALL))
        # )
        # bridges2.add_grids(
        #     Grid(grid_type=Grid.BATCH, scheduler_type=Scheduler.SLURM, contact=login_host,
        #          job_type=SupportedJobs.COMPUTE)
        # )
        # # TODO: Update PEGASUS_HOME path.
        # bridges2.add_env("PEGASUS_HOME", "/ocean/projects/cis240026p/vahi/software/install/pegasus/default")
        # bridges2.add_pegasus_profile(
        #     style="ssh",
        #     queue="RM-shared",
        #     auxillary_local=True,
        #     runtime=1800,
        #     project=self.project,
        # )
        # self.site_catalog.add_sites(bridges2)

        # TODO: Is this line needed?
        # self.workflow.add_site_catalog(sc=self.site_catalog)

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
            name="step3_inference",
            site="local",
            pfn=BASE_DIR + f"/step3/{DUMMY}run_inference.sh",
            is_stageable=True,
            container=container,
        )
        step3_inference.add_pegasus_profiles(cores=1, runtime="300",
                                             container_launcher="srun",
                                             container_launcher_arguments="--kill-on-bad-exit",
                                             glite_arguments="--cpus-per-task=14")
        self.transformation_catalog.add_transformations(step3_inference)

        # TODO: Is this line needed?
        # self.workflow.add_transformation_catalog(tc=self.transformation_catalog)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        pass
        # most of the replicas are added when creating the workflow

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.workflow = Workflow(self.workflow_name)

        # --- Workflow -----------------------------------------------------
        # the input files required for the workflow are tracked in the Replica Catalog.

        ### Step 1: Pre-training
        step1_pretrain_job = Job("step1_pretrain", node_label="step1_pretrain_label")
        self.workflow.add_jobs(step1_pretrain_job)
        ###

        ### Step 2: Regression
        step2_regression_job = Job("step2_regression", node_label="step2_regression_label")
        self.workflow.add_jobs(step2_regression_job)
        ###

        ### Step 3: Inference
        step3_inference_job = Job("step3_inference", node_label="step3_inference_label")
        self.workflow.add_jobs(step3_inference_job)
        ###

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
