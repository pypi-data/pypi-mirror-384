import os
import glob
from pathlib import Path
from typing import Optional
import pandas
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.fl_context import FLContext
from apheris_preprocessing import FederatedDataFrame
from apheris_preprocessing.exceptions import TransformationsException
from apheris_utils.data import download_dataset, download_all


def get_processed_remote_dataset(
    dataset_id: Optional[str] = None,
    download_folder: Optional[str] = None,
    fl_ctx: Optional[FLContext] = None,
) -> pandas.DataFrame:
    """
    Returns a processed remote dataset as a pandas DataFrame. This function can only be
    called from the gateway executor. Locally it will raise an exception.
    Args:
        dataset_id: id of the dataset to create the FederatedDataFrame from.
        read_format: format of data source
    """
    try:
        if dataset_id:
            # this will download the dataset via the DAL if called from the gateway executor
            # or return the local path if called from the local executor in simulator mode
            fpaths = download_dataset(dataset_id=dataset_id, folder=download_folder)
        else:
            fpaths = download_all(download_folder)
    except KeyError as e:
        raise TransformationsException(
            message=f"Dataset with id {dataset_id} not found in the data access layer."
            " This function can only be called from the gateway executor or in a "
            "local simulator run."
        ) from e
    fdf = load_from_job_config(fl_ctx)
    return fdf._run(fpaths)


def load_from_job_config(fl_ctx: FLContext) -> FederatedDataFrame:
    engine = fl_ctx.get_engine()
    job_id = fl_ctx.get_prop(FLContextKey.CURRENT_RUN)
    run_dir = engine.get_workspace().get_run_dir(job_id)
    if os.environ.get("APH_LOCAL_RUN", "0") == "1":
        graph_path = (
            Path(engine.get_workspace().get_client_app_config_file_path(job_id)).parent
            / "fdf.json"
        )
    else:
        path_list = glob.glob(run_dir + "/*/config/fdf.json")
        if len(path_list) != 1:
            raise TransformationsException(
                message=(
                    "There should be exactly one fdf.json file in the run directory. "
                    f"Found {len(path_list)} files."
                )
            )
        graph_path = Path(path_list[0])
    s = graph_path.read_text()
    fdf = FederatedDataFrame(graph_json=s)

    return fdf
