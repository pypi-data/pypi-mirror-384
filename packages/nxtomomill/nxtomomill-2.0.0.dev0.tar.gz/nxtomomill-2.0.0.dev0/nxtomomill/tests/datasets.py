import os
from tomoscan.tests.datasets import GitlabProject


GitlabDataset = GitlabProject(
    branch_name="nxtomomill",
    host="https://gitlab.esrf.fr",
    cache_dir=os.path.join(
        os.path.dirname(__file__),
        "__archive__",
    ),
    token=None,
    project_id=4299,  # https://gitlab.esrf.fr/tomotools/ci_datasets
)
