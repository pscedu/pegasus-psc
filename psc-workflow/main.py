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
import getpass
import logging
import os
import shutil
import sys

from Pegasus.api import *
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

# from IPython.display import Image; Image(filename='graph.png')

ENTRY_LOCATION = "/ocean/projects/sys890003p/spagaria/project1/dana"


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
                sites=[NEOCORTEX_SITE_HANDLE, BRIDGES2_SITE_HANDLE],
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

        # prepare_tokenization_split
        prepare_tokenization_split_transformation = Transformation(
            name="prepare_tokenization_split_transformation",
            site="local",
            pfn=f"{BASE_DIR}/executables/step1/prepare_tokenization_split.sh",
            is_stageable=True,
        )
        prepare_tokenization_split_transformation.add_pegasus_profiles(cores=1, runtime="300",
                                                                       container_launcher="srun",
                                                                       container_launcher_arguments="--kill-on-bad-exit",
                                                                       glite_arguments="--cpus-per-task=28")
        self.transformation_catalog.add_transformations(prepare_tokenization_split_transformation)

        # create_csv_mlm_only.py train, val, test
        for mode in "train", "val", "test":
            create_csv_mlm_only_transformation = Transformation(
                name=f"create_csv_mlm_only_{mode}_transformation",
                site="local",
                pfn=f"{BASE_DIR}/executables/step1/create_csv_mlm_only_{mode}.sh",
                is_stageable=True,
            )
            create_csv_mlm_only_transformation.add_pegasus_profiles(cores=1, runtime="300",
                                                                    container_launcher="srun",
                                                                    container_launcher_arguments="--kill-on-bad-exit",
                                                                    glite_arguments="--cpus-per-task=28")
            self.transformation_catalog.add_transformations(create_csv_mlm_only_transformation)

        # [Neocortex] run_roberta.py
        run_roberta_transformation = Transformation(
            name="run_roberta_transformation",
            site="local",
            pfn=f"{BASE_DIR}/executables/step1/run_roberta.sh",
            is_stageable=True,
            container=container,
        )
        run_roberta_transformation.add_pegasus_profiles(cores=1, runtime="300",
                                                        container_launcher="srun",
                                                        container_launcher_arguments="--kill-on-bad-exit",
                                                        glite_arguments="--cpus-per-task=28")  # --gres=cs:cerebras:1
        self.transformation_catalog.add_transformations(run_roberta_transformation)

        # create_regression_csv.py
        create_regression_csv_transformation = Transformation(
            name="create_regression_csv_transformation",
            site="local",
            pfn=f"{BASE_DIR}/executables/step2/create_regression_csv.sh",
            is_stageable=True,
        )
        create_regression_csv_transformation.add_pegasus_profiles(cores=1, runtime=str(60 * 60 * 5),
                                                                  container_launcher="srun",
                                                                  container_launcher_arguments="--kill-on-bad-exit",
                                                                  glite_arguments="--cpus-per-task=28")
        self.transformation_catalog.add_transformations(create_regression_csv_transformation)

        # run_regression.py
        run_regression_transformation = Transformation(
            name="run_regression_transformation",
            site="local",
            pfn=f"{BASE_DIR}/executables/step2/run_regression.sh",
            is_stageable=True,
        )
        run_regression_transformation.add_pegasus_profiles(cores=1, runtime="300",
                                                           queue="GPU-shared", gpus=1,
                                                           container_launcher="srun",
                                                           container_launcher_arguments="--kill-on-bad-exit",
                                                           glite_arguments="--cpus-per-task=28")
        self.transformation_catalog.add_transformations(run_regression_transformation)

        # run_inference.py
        run_inference_transformation = Transformation(
            name="run_inference_transformation",
            site="local",
            pfn=f"{BASE_DIR}/executables/step3/run_inference.sh",
            is_stageable=True,
        )
        run_inference_transformation.add_pegasus_profiles(cores=1, runtime="300",
                                                          queue="GPU-shared", gpus=1,
                                                          container_launcher="srun",
                                                          container_launcher_arguments="--kill-on-bad-exit",
                                                          glite_arguments="--cpus-per-task=28")
        self.transformation_catalog.add_transformations(run_inference_transformation)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        pass
        # most of the replicas are added when creating the workflow

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.workflow = Workflow(self.workflow_name)

        # --- Workflow -----------------------------------------------------
        # the input files required for the workflow are tracked in the Replica Catalog.

        ## Main Workflow Steps
        # prepare_tokenization_split.py
        # create_csv_mlm_only.py train
        # create_csv_mlm_only.py val
        # create_csv_mlm_only.py test
        # [Neocortex] run_roberta.py  }
        # create_regression_csv.py    } => run_regression.py => run_inference.py => End

        ### prepare_tokenization_split.py
        #### Files definition
        create_csv_mlm_only_py_file = File("create_csv_mlm_only_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=create_csv_mlm_only_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step1/create_csv_mlm_only.py"
        )
        prepare_tokenization_split_py_file = File("prepare_tokenization_split_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=prepare_tokenization_split_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step1/prepare_tokenization_split.py"
        )
        run_roberta_py_file = File("run_roberta_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=run_roberta_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step1/run_roberta.py"
        )
        create_regression_csv_py_file = File("create_regression_csv_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=create_regression_csv_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step2/create_regression_csv.py"
        )
        run_regression_py_file = File("run_regression_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=run_regression_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step2/run_regression.py"
        )
        run_inference_py_file = File("run_inference_py_file")
        self.replica_catalog.add_replica(
            site="local", lfn=run_inference_py_file.lfn,
            pfn=f"{BASE_DIR}/executables/step3/run_inference.py"
        )

        materials_string_input_file = File("materials_string_input_file")
        self.replica_catalog.add_replica(
            site="local", lfn=materials_string_input_file.lfn,
            pfn=f"{ENTRY_LOCATION}/encoding/crystal_materials_string_OCELOT.txt"
        )
        pretraining_output_tar = File("pretrain_OCELOT__pretrain_MS_0_0001__pretraining.tgz")
        model_pretrain_tar = File("pretrain_OCELOT__pretrain_MS_0_0001__model_pretrain.tgz")
        #### Job definition
        prepare_tokenization_split_job = Job(transformation="prepare_tokenization_split_transformation",
                                             node_label="prepare_tokenization_split_label")
        self.workflow.add_jobs(prepare_tokenization_split_job)

        prepare_tokenization_split_job.add_inputs(materials_string_input_file,
                                                  prepare_tokenization_split_py_file)
        prepare_tokenization_split_job.add_outputs(pretraining_output_tar)

        ### create_csv_mlm_only.py
        #### Files definition
        tokenizer_vobac_input_file = File("tokenizer_vobac_input_file")
        self.replica_catalog.add_replica(
            site="local", lfn=tokenizer_vobac_input_file.lfn,
            pfn=f"{ENTRY_LOCATION}/tokenizer/materials_string_OCELOT.txt"
        )
        csv_train_tar = File("csv_train.tgz")
        csv_val_tar = File("csv_val.tgz")
        csv_test_tar = File("csv_test.tgz")

        roberta_params_yaml_input_file = File("roberta_params_yaml_input_file")
        self.replica_catalog.add_replica(
            site="local", lfn=roberta_params_yaml_input_file.lfn,
            pfn=f"{BASE_DIR}/inputs/step1/roberta_params_OCELOT_MS.yaml"
        )

        #### create_csv_mlm_only.py train
        create_csv_mlm_only_train_job = Job(transformation="create_csv_mlm_only_train_transformation",
                                            node_label="create_csv_mlm_only_train_label")
        self.workflow.add_jobs(create_csv_mlm_only_train_job)

        create_csv_mlm_only_train_job.add_inputs(pretraining_output_tar, tokenizer_vobac_input_file,
                                                 create_csv_mlm_only_py_file)
        create_csv_mlm_only_train_job.add_outputs(csv_train_tar)

        #### create_csv_mlm_only.py val
        create_csv_mlm_only_val_job = Job(transformation="create_csv_mlm_only_val_transformation",
                                          node_label="create_csv_mlm_only_val_label")
        self.workflow.add_jobs(create_csv_mlm_only_val_job)

        create_csv_mlm_only_val_job.add_inputs(pretraining_output_tar, tokenizer_vobac_input_file,
                                               create_csv_mlm_only_py_file)
        create_csv_mlm_only_val_job.add_outputs(csv_val_tar)

        #### create_csv_mlm_only.py test
        create_csv_mlm_only_test_job = Job(transformation="create_csv_mlm_only_test_transformation",
                                           node_label="create_csv_mlm_only_test_label")
        self.workflow.add_jobs(create_csv_mlm_only_test_job)

        create_csv_mlm_only_test_job.add_inputs(pretraining_output_tar, tokenizer_vobac_input_file,
                                                create_csv_mlm_only_py_file)
        create_csv_mlm_only_test_job.add_outputs(csv_test_tar)

        ### python-pt run_roberta.py
        run_roberta_job = Job(transformation="run_roberta_transformation", node_label="run_roberta_label")
        run_roberta_job.add_selector_profile(execution_site=NEOCORTEX_SITE_HANDLE)
        self.workflow.add_jobs(run_roberta_job)

        run_roberta_job.add_inputs(roberta_params_yaml_input_file, run_roberta_py_file,
                                   csv_train_tar, csv_val_tar, csv_test_tar)
        run_roberta_job.add_outputs(model_pretrain_tar)

        ### Files
        # TODO: Connect by untarring before accessing the file from model_pretrain_output_tar in .sh file
        # f"{ENTRY_LOCATION}/pretrain_OCELOT/pretrain_MS_0.0001/model_pretrain/checkpoint_3000.mdl"
        regression_params_yaml_input_file = File("regression_params_yaml_input_file")
        self.replica_catalog.add_replica(
            site="local", lfn=regression_params_yaml_input_file.lfn,
            pfn=f"{BASE_DIR}/inputs/step2/regression_params.yaml"
        )
        # TODO: Compress in .sh file. 85MB total, split across 9579 files. {ENTRY_LOCATION}/Merged_Dataset/OCELOT
        merged_dataset_ocelot_input_tar_file = File("merged_dataset_ocelot.tgz")
        self.replica_catalog.add_replica(
            site="local", lfn=merged_dataset_ocelot_input_tar_file.lfn,
            pfn=f"{BASE_DIR}/inputs/step2/merged_dataset_ocelot.tgz"
        )
        regression_OCELOT__ms_OCELOT_output_tar = File("regression_OCELOT__ms_OCELOT.tgz")
        inference_MS_OCELOT_json_output_file = File("inference_MS_OCELOT.json")
        # TODO: Currently using model_pretrain.tgz instead. Is it better to make the change?
        # checkpoint_3000_input_file = File("checkpoint_3000_input_file")
        # self.replica_catalog.add_replica(
        #     site="local", lfn=checkpoint_3000_input_file.lfn,
        #     pfn=f"{ENTRY_LOCATION}/regression_OCELOT/ms_OCELOT/checkpoint_3000.mdl"
        # )
        checkpoint_2100_file = File("checkpoint_2100_file")
        self.replica_catalog.add_replica(
            site="local", lfn=checkpoint_2100_file.lfn,
            pfn=f"{ENTRY_LOCATION}/regression_OCELOT/ms_OCELOT/checkpoint_2100.mdl"
        )

        ### create_regression_csv.py
        create_regression_csv_job = Job(transformation="create_regression_csv_transformation",
                                        node_label="create_regression_csv_label")
        self.workflow.add_jobs(create_regression_csv_job)
        create_regression_csv_job.add_inputs(merged_dataset_ocelot_input_tar_file, create_regression_csv_py_file)
        create_regression_csv_job.add_outputs(regression_OCELOT__ms_OCELOT_output_tar)

        ### run_regression.py
        run_regression_job = Job(transformation="run_regression_transformation", node_label="run_regression_label")
        self.workflow.add_jobs(run_regression_job)

        # TODO: is the whole folder needed from the previous step for regression_OCELOT__ms_OCELOT_output_tar? Maybe just a csv file is needed.
        run_regression_job.add_inputs(model_pretrain_tar, regression_params_yaml_input_file,
                                      regression_OCELOT__ms_OCELOT_output_tar,
                                      run_regression_py_file)
        run_regression_job.add_outputs(checkpoint_2100_file)

        ### run_inference_job.py
        run_inference_job = Job(transformation="run_inference_transformation", node_label="run_inference_label")
        self.workflow.add_jobs(run_inference_job)

        run_inference_job.add_inputs(checkpoint_2100_file, run_inference_py_file)
        run_inference_job.add_outputs(inference_MS_OCELOT_json_output_file)

        ## Job Dependencies
        self.workflow.add_dependency(job=prepare_tokenization_split_job,
                                     children=[create_csv_mlm_only_train_job,
                                               create_csv_mlm_only_val_job,
                                               create_csv_mlm_only_test_job, ])
        self.workflow.add_dependency(job=run_regression_job, parents=[create_regression_csv_job, run_roberta_job])
        self.workflow.add_dependency(job=run_inference_job, parents=[run_regression_job, ])

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
