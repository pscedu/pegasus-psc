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

from Pegasus.api import *

logging.basicConfig(level=logging.DEBUG)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# need to know where Pegasus is installed for notifications
PEGASUS_HOME = shutil.which("pegasus-version")
PEGASUS_HOME = os.path.dirname(os.path.dirname(PEGASUS_HOME))


class CerebrasPyTorchWorkflow():

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
                sites=["neocortex"],
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
        # data transfers for the jobs should happen
        # on the HOSTOS not inside the container
        self.props["pegasus.transfer.container.onhost"] = True
        # we dont want any pegasus worker package
        # to be installed inside the container
        self.props["pegasus.transfer.worker.package"] = True
        self.props["pegasus.transfer.worker.package.autodownload"] = False
        # enable symlinking
        # props["pegasus.transfer.links"] = True
        self.props.write()
        return

    # --- Site Catalog -------------------------------------------------------------
    def create_sites_catalog(self, exec_site_name="condorpool"):
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

        self.sc.add_sites(local)

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

    # --- Transformation Catalog (Executables and Containers) ----------------------
    def create_transformation_catalog(self, exec_site_name="condorpool"):
        self.tc = TransformationCatalog()
        container = Container(
            "cerebras",
            Container.SINGULARITY,
            "file:///ocean/neocortex/cerebras/cbcore_latest.sif",
            image_site="neocortex",
            # mounts=['/${PROJECT}/workflows/NEOCORTEX/scratch:/${PROJECT}/workflows/NEOCORTEX/scratch:rw'],
        )
        self.tc.add_containers(container)

        validate = Transformation(
            "validate",
            site="local",
            pfn=BASE_DIR + "/executables/validate.sh",
            is_stageable=True,
            container=container,
        )
        validate.add_profiles(Namespace.PEGASUS, key="cores", value="1")
        validate.add_profiles(Namespace.PEGASUS, key="runtime", value="900")
        validate.add_profiles(
            Namespace.PEGASUS,
            key="glite.arguments",
            value="--cpus-per-task=14 --gres=cs:cerebras:1 --qos=low",
        )
        self.tc.add_transformations(validate)

        compile = Transformation(
            "compile",
            site="local",
            pfn=BASE_DIR + "/executables/compile.sh",
            is_stageable=True,
            container=container,
        )
        compile.add_profiles(Namespace.PEGASUS, key="cores", value="1")
        compile.add_profiles(Namespace.PEGASUS, key="runtime", value="900")
        compile.add_profiles(
            Namespace.PEGASUS,
            key="glite.arguments",
            value="--cpus-per-task=14 --gres=cs:cerebras:1 --qos=low",
        )
        self.tc.add_transformations(compile)

        train = Transformation(
            "train", site="local", pfn=BASE_DIR + "/executables/train.sh", is_stageable=True, container=container
        )
        train.add_profiles(Namespace.PEGASUS, key="cores", value="1")
        train.add_profiles(Namespace.PEGASUS, key="runtime", value="3600")
        train.add_profiles(Namespace.PEGASUS, key="container.launcher", value="srun")
        train.add_profiles(Namespace.PEGASUS, key="container.launcher.arguments", value="--kill-on-bad-exit")
        train.add_profiles(
            Namespace.PEGASUS,
            key="glite.arguments",
            value="--cpus-per-task=14 --gres=cs:cerebras:1 --qos=low"
        )
        self.tc.add_transformations(train)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()
        # most of the replicas are added when creating the workflow

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.wf = Workflow(self.wf_name)

        # --- Workflow -----------------------------------------------------
        # the main input for the workflow is config file and the modelzoo checkout
        modelzoo_config_params = File(
            "modelzoo/modelzoo/fc_mnist/pytorch/configs/params.yaml"
        )
        modelzoo_raw = File("modelzoo-raw.tgz")
        self.rc.add_replica(
            "local", modelzoo_config_params.lfn, "{}/input/params.yaml".format(BASE_DIR)
        )
        self.rc.add_replica(
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
            self.rc.add_replica(
                "nonlocal",
                train_file.lfn,
                "http://yann.lecun.com/exdb/mnist/{}".format(file),
            )
            self.rc.add_replica(
                "nonlocal",
                train_file.lfn,
                "https://ossci-datasets.s3.amazonaws.com/mnist/{}".format(file),
            )
            validate_job.add_inputs(train_file)

        # track some cerebras log files as outputs
        for file in cerebras_logs:
            # scripts do rename of the files after job completes
            validate_job.add_outputs(File("{}_{}".format("validate", file)), stage_out=True)

        self.wf.add_jobs(validate_job)

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

        self.wf.add_jobs(compile_job)

        # training job
        now = datetime.datetime.now().strftime("%s")
        training_job = Job("train", node_label="train_model")
        training_job.add_args(
            "--mode train --params configs/params.yaml --model_dir model --cs_ip $CS_IP_ADDR"
        )
        training_job.add_inputs(modelzoo_compiled)
        training_job.add_outputs(modelzoo_trained, stage_out=True)
        # training_job.add_outputs(modelzoo_trained_checkpoints, stage_out=True)
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
        self.wf.add_jobs(training_job)

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
    parser = argparse.ArgumentParser(description="generate a sample cerebras PyTorch pegasus workflow")
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
