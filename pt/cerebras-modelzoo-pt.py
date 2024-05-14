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


def generate_wf():
    """
    Main function that parses arguments and generates the pegasus
    workflow
    """

    parser = argparse.ArgumentParser(description="generate a sample pegasus workflow")

    args = parser.parse_args(sys.argv[1:])

    wf = Workflow("cerebras-model-zoo-pt")
    tc = TransformationCatalog()
    rc = ReplicaCatalog()

    # --- Properties ----------------------------------------------------------

    # set the concurrency limit for the download jobs, and send some extra usage
    # data to the Pegasus developers
    props = Properties()
    props[
        "pegasus.catalog.workflow.amqp.url"
    ] = "amqp://friend:donatedata@msgs.pegasus.isi.edu:5672/prod/workflows"
    props["pegasus.data.configuration"] = "nonsharedfs"
    props["pegasus.mode"] = "development"
    # data transfers for the jobs should happen
    # on the HOSTOS not inside the container
    props["pegasus.transfer.container.onhost"] = True
    # we dont want any pegasus worker package
    # to be installed inside the container
    props["pegasus.transfer.worker.package"] = True
    props["pegasus.transfer.worker.package.autodownload"] = False
    # enable symlinking
    #props["pegasus.transfer.links"] = True
    props.write()

    # --- Event Hooks ---------------------------------------------------------

    # get emails on all events at the workflow level
    wf.add_shell_hook(
        EventType.ALL, "{}/share/pegasus/notification/email".format(PEGASUS_HOME)
    )

    # --- Transformations -----------------------------------------------------

    #
    container = Container(
        "cerebras",
        Container.SINGULARITY,
        "file:///ocean/neocortex/cerebras/cbcore_latest.sif",
        image_site="neocortex",
        # mounts=['/${PROJECT}/workflows/NEOCORTEX/scratch:/${PROJECT}/workflows/NEOCORTEX/scratch:rw'],
    )
    tc.add_containers(container)

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
    tc.add_transformations(validate)

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
    tc.add_transformations(compile)

    train = Transformation(
        "train", site="local", pfn=BASE_DIR + "/executables/train.sh", is_stageable=True
    )
    train.add_profiles(Namespace.PEGASUS, key="cores", value="1")
    train.add_profiles(Namespace.PEGASUS, key="runtime", value="3600")
    train.add_profiles(
        Namespace.PEGASUS,
        key="glite.arguments",
        value="--cpus-per-task=14 --gres=cs:cerebras:1 --qos=low",
        container=container
    )
    tc.add_transformations(train)

    # --- Site Catalog -------------------------------------------------
    sc = SiteCatalog()

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

    sc.add_sites(local)

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
        project="cis240026p",
    )
    sc.add_sites(neocortex)

    # --- Workflow -----------------------------------------------------
    # the main input for the workflow is config file and the modelzoo checkout
    modelzoo_config_params = File(
        "modelzoo/modelzoo/fc_mnist/pytorch/configs/params.yaml"
    )
    modelzoo_raw = File("modelzoo-raw.tgz")
    rc.add_replica(
        "local", modelzoo_config_params.lfn, "{}/input/params.yaml".format(BASE_DIR)
    )
    rc.add_replica(
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
        rc.add_replica(
            "nonlocal",
            train_file.lfn,
            "http://yann.lecun.com/exdb/mnist/{}".format(file),
        )
        rc.add_replica(
            "nonlocal",
            train_file.lfn,
            "https://ossci-datasets.s3.amazonaws.com/mnist/{}".format(file),
        )
        validate_job.add_inputs(train_file)

    # track some cerebras log files as outputs
    for file in cerebras_logs:
        # scripts do rename of the files after job completes
        validate_job.add_outputs(File("{}_{}".format("validate", file)), stage_out=True)

    wf.add_jobs(validate_job)

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

    wf.add_jobs(compile_job)

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
    wf.add_jobs(training_job)

    try:
        wf.add_transformation_catalog(tc)
        wf.add_site_catalog(sc)
        wf.add_replica_catalog(rc)
        wf.plan(
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
        print(e.output)


if __name__ == "__main__":
    generate_wf()
