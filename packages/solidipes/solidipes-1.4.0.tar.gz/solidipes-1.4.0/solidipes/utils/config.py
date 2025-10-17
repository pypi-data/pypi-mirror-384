solidipes_dirname = ".solidipes"
study_metadata_filename = "study_metadata.yaml"
study_description_filename = "DESCRIPTION.md"
readme_filename = "README.md"
description_warning = (
    f"Do not edit this field manually. It will be replaced by the content of {study_description_filename}."
)
study_medatada_mandatory_fields = {
    "title": "Title of your study",
    "upload_type": "dataset",
    "description": "",
    "creators": [
        {"name": "Your Name", "affiliation": "Affiliation", "orcid": "0000-0000-0000-0000"},
        {"name": "Collaborator Name"},
    ],
    "keywords": ["keyword1", "keyword2"],
    "language": "eng",
    "license": "cc-by-4.0",
}
study_medatada_removed_fields_upload = [
    "access_right_category",  # I don't know what this is
    "meeting",  # TODO: implement in scripts/download (linked Conference)
    "relations",  # Redundant with related_identifiers
]
mimes_filename = "mimes.yaml"
zenodo_infos_filename = "zenodo_infos.yaml"
cloud_dir_name = "cloud"
cloud_info_filename = "cloud.yaml"
cloud_connection_timeout = 15
cached_metadata_yaml_filename = "metadata.yaml"  # backward compatibility
cached_metadata_filename = "metadata.fs"
completed_stages_filename = "completed_stages.yaml"
cached_metadata_polling_interval = 0.5  # seconds
cached_metadata_polling_tries = 30
cached_metadata_save_every = 0.5  # seconds
ignore_filename = "ignore.yaml"
default_ignore_patterns = {
    "*~",
    ".*",
    ".git",
    "__pycache__",
    f"{solidipes_dirname}/solidipes.logs",
    f"{solidipes_dirname}/{cached_metadata_yaml_filename}",
    f"{solidipes_dirname}/{cached_metadata_filename}",
    f"{solidipes_dirname}/{cached_metadata_filename}.index",
    f"{solidipes_dirname}/{cached_metadata_filename}.lock",
    f"{solidipes_dirname}/{cached_metadata_filename}.tmp",
    f"{solidipes_dirname}/{study_metadata_filename}",
    f"{solidipes_dirname}/{zenodo_infos_filename}",
}
