import json
from pathlib import Path
from shutil import copyfile

from abm.assess.application_model import ApplicationModel
from abm.assess.shims.application_model_to_assess_metadata import application_model_to_assess_metadata


def generate_dist(application_model_path: Path, dist_directory: Path):
    root_dir = Path(__file__).parent

    assess_id = application_model_path.stem

    application_model_file = application_model_path.joinpath("application_model.json")
    application_model = ApplicationModel.from_data(json.loads(application_model_file.read_text())).or_die()

    assess_model = application_model_to_assess_metadata(application_model, assess_id)

    # Create Directories
    Path(dist_directory, assess_id).mkdir(exist_ok=True)
    dist_dir = dist_directory.joinpath(assess_id)

    # Copy model json to dist
    copyfile(application_model_path.joinpath("model.json"), dist_dir.joinpath("model.json"))

    # Write
    dist_dir.joinpath("assess_metadata.json").write_text(json.dumps(assess_model.to_data(), indent=2))

    # Copy report
    dist_dir.joinpath("report_templates").mkdir(exist_ok=True)
    if application_model.assess.report_url is not None:
        file_name = application_model.assess.report_url.removeprefix("file:./")
        copyfile(application_model_path.joinpath(file_name), dist_dir.joinpath("report_templates", file_name))
    else:
        copyfile(
            root_dir.joinpath("shared", "basic_report.html.handlebars"),
            dist_dir.joinpath("report_templates", "basic_report.html.handlebars"),
        )

    # Copy images:
    if application_model.thumbnail_url is not None:
        file_name = application_model.thumbnail_url.removeprefix("file:./")
        copyfile(application_model_path.joinpath(file_name), dist_dir.joinpath(file_name))
    else:
        copyfile(root_dir.joinpath("shared", "thumbnail.png"), dist_dir.joinpath("thumbnail.png"))

    if application_model.drug_diagram_url is not None:
        file_name = application_model.drug_diagram_url.removeprefix("file:./")
        copyfile(application_model_path.joinpath(file_name), dist_dir.joinpath(file_name))
    else:
        copyfile(root_dir.joinpath("shared", "drug_diagram.png"), dist_dir.joinpath("drug_diagram.png"))

    if application_model.pharmacology_diagram_url is not None:
        file_name = application_model.pharmacology_diagram_url.removeprefix("file:./")
        copyfile(application_model_path.joinpath(file_name), dist_dir.joinpath(file_name))
