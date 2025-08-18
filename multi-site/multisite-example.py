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
import logging
import os
import shutil
import sys
import getpass

from Pegasus.api import *

logging.basicConfig(level=logging.DEBUG)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# need to know where Pegasus is installed for notifications
PEGASUS_HOME = shutil.which("pegasus-version")
PEGASUS_HOME = os.path.dirname(os.path.dirname(PEGASUS_HOME))
WF_SSH_KEY_PATH = os.path.expanduser("~") + "/.pegasus/wfsshkey"
USER = getpass.getuser()


class MultiSiteExampleWorkflow():

    # --- Init ---------------------------------------------------------------------
    def __init__(self, project=None):
        self.wf = None
        self.sc = None
        self.tc = None
        self.rc = None
        self.props = None
        self.wf_name = "cerebras-model-zoo-pt"
        self.project = project
        # Log
        self.log = logging.getLogger(__name__)

    # --- Write files in directory -------------------------------------------------
    def write(self):
        if not self.sc is None:
            self.sc.write()
        self.props.write()
        self.rc.write()
        self.tc.write()

        try:
            self.wf.write()
        except PegasusClientError as e:
            print(e)

    # --- Plan and Submit the workflow ----------------------------------------------
    def plan_submit(self):
        try:
            self.wf.plan(
                conf="pegasus.properties",
                sites=["neocortex,bridges2"],
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
            self.wf.status(long=True)
        except PegasusClientError as e:
            print(e)

    # --- Wait for the workflow to finish -----------------------------------------------
    def wait(self):
        try:
            self.wf.wait()
        except PegasusClientError as e:
            print(e)

    # --- Get statistics of the workflow -----------------------------------------------
    def statistics(self):
        try:
            self.wf.statistics()
        except PegasusClientError as e:
            print(e)

    # --- Configuration (Pegasus Properties) ---------------------------------------
    def create_pegasus_properties(self):
        self.props = Properties()
        self.props["pegasus.integrity.checking"] = "none"
        self.props[
            "pegasus.catalog.workflow.amqp.url"
        ] = "amqp://friend:donatedata@msgs.pegasus.isi.edu:5672/prod/workflows"
        self.props["pegasus.data.configuration"] = "nonsharedfs"
        self.props["pegasus.mode"] = "development"

        # we dont want any pegasus worker package
        # to be installed inside the container
        self.props["pegasus.transfer.worker.package"] = True
        self.props["pegasus.transfer.worker.package.autodownload"] = False
        # enable symlinking
        # props["pegasus.transfer.links"] = True
        self.props.write()
        return

    # --- Site Catalog -------------------------------------------------------------
    def create_sites_catalog(self):
        self.sc = SiteCatalog()
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
        local.add_pegasus_profile(SSH_PRIVATE_KEY=WF_SSH_KEY_PATH)
        self.sc.add_sites(local)

        # the neocortex site
        shared_scratch_dir = "/{}/workflows/NEOCORTEX/scratch".format("${PROJECT}")
        local_scratch_dir = "/local4/{}".format("${SALLOC_ACCOUNT}")
        neocortex = Site("neocortex").add_directories(
            Directory(
                Directory.SHARED_SCRATCH, shared_scratch_dir, shared_file_system=True
            ).add_file_servers(FileServer("file://" + shared_scratch_dir, Operation.ALL)),
            Directory(Directory.LOCAL_SCRATCH, local_scratch_dir).add_file_servers(
                FileServer("file://" + local_scratch_dir, Operation.ALL)
            ),
        )
        neocortex.add_condor_profile(grid_resource="batch slurm")
        #    neocortex.add_env("PEGASUS_HOME", "/ocean/projects/cis240026p/vahi/software/install/pegasus/default")
        neocortex.add_pegasus_profile(
            style="glite",
            queue="sdf",
            auxillary_local=True,
            runtime=1800,
            project=self.project,
        )
        self.sc.add_sites(neocortex)

        # bridges2 site
        shared_scratch_dir = "/{}/workflows/BRIDGES@/scratch".format("${PROJECT}")
        login_host = "bridges2.psc.edu"
        bridges2 = Site("bridges2").add_directories(
            Directory(
                Directory.SHARED_SCRATCH, shared_scratch_dir, shared_file_system=True
            ).add_file_servers(FileServer("scp://" + USER + "@" + login_host + shared_scratch_dir, Operation.ALL))
        )
        bridges2.add_grids(
            Grid(grid_type=Grid.BATCH, scheduler_type=Scheduler.SLURM, contact=login_host,
                 job_type=SupportedJobs.COMPUTE)
        )
        bridges2.add_env("PEGASUS_HOME", "/ocean/projects/cis240026p/vahi/software/install/pegasus/default")
        bridges2.add_pegasus_profile(
            style="ssh",
            queue="RM-shared",
            auxillary_local=True,
            runtime=1800,
            project=self.project,
        )
        self.sc.add_sites(bridges2)

    # --- Transformation Catalog (Executables and Containers) ----------------------
    def create_transformation_catalog(self):
        self.tc = TransformationCatalog()
        container = Container(
            "cerebras",
            Container.SINGULARITY,
            "file:///ocean/neocortex/cerebras/cbcore_latest.sif",
            image_site="neocortex",
            # mounts=['/${PROJECT}/workflows/NEOCORTEX/scratch:/${PROJECT}/workflows/NEOCORTEX/scratch:rw'],
        )
        self.tc.add_containers(container)

        # THIS IS A DUMMY PYTHON EXECUTABLE . NOT A REAL TRAINING PYTHON SCRIPT
        pretrain = Transformation(
            "pretrain", site="notlocal",
            pfn="https://raw.githubusercontent.com/pegasus-isi/hpc-examples/refs/heads/main/executables/pegasus-keg.py",
            is_stageable=True, container=container
        )
        pretrain.add_profiles(Namespace.PEGASUS, key="cores", value="1")
        pretrain.add_profiles(Namespace.PEGASUS, key="runtime", value="3600")
        pretrain.add_profiles(Namespace.PEGASUS, key="container.launcher", value="srun")
        pretrain.add_profiles(Namespace.PEGASUS, key="container.launcher.arguments", value="--kill-on-bad-exit")
        pretrain.add_profiles(
            Namespace.PEGASUS,
            key="glite.arguments",
            value="--cpus-per-task=14 --gres=cs:cerebras:1 --qos=low"
        )
        self.tc.add_transformations(pretrain)

        regression = Transformation(
            "regression", site="notlocal",
            pfn="https://raw.githubusercontent.com/pegasus-isi/hpc-examples/refs/heads/main/executables/pegasus-keg.py",
            is_stageable=True,
        )
        regression.add_profiles(Namespace.PEGASUS, key="cores", value="1")
        regression.add_profiles(Namespace.PEGASUS, key="runtime", value="3600")
        self.tc.add_transformations(regression)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()
        # most of the replicas are added when creating the workflow

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.wf = Workflow(self.wf_name)

        # --- Workflow -----------------------------------------------------
        # the main input for the workflow is config file and the modelzoo checkout
        pre_training_input = File("pre_training_input.txt")
        self.rc.add_replica(
            "local", pre_training_input.lfn, "{}/input/pre_training_input.txt".format(BASE_DIR)
        )

        # output of the training job. can be multiple files
        pre_training_output = File("pre_training_output.txt")

        # pretraining job
        pretraining_job = Job("pretrain", node_label="pretraining_node")
        pretraining_job.add_args(
            "--input " + pre_training_input.lfn + "--output " + pre_training_output.lfn
        )
        pretraining_job.add_inputs(pre_training_input)
        pretraining_job.add_outputs(pre_training_output, stage_out=True)
        # force the job to only run on neocortex
        pretraining_job.add_selector_profile(execution_site="neocortex")
        self.wf.add_jobs(pretraining_job)

        # regression job
        regression_job = Job("regression", node_label="regression_node")
        regression_output = File("regression_output.txt")
        regression_job.add_args(
            "--input " + pre_training_output.lfn + "--output " + regression_output.lfn
        )
        regression_job.add_inputs(pre_training_output)
        regression_job.add_outputs(regression_output, stage_out=True)
        # force the job to only run on bridges2
        regression_job.add_selector_profile(execution_site="bridges2")
        self.wf.add_jobs(regression_job)

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
    parser = argparse.ArgumentParser(
        description="generate a sample stub multisite workflow that runs a fake pretraining on neocortex and regression on bridges2")
    parser.add_argument('--project', dest='project', default=None, required=True,
                        help='Specifies the project/grantid of your project')
    args = parser.parse_args(sys.argv[1:])
    wf = MultiSiteExampleWorkflow(project=args.project)
    try:
        wf()
    except PegasusClientError as e:
        wf.log.debug("", exc_info=True)
        print(e.output)
        sys.exit(1)
    except Exception:
        wf.log.debug("", exc_info=True)
        sys.exit(1)
