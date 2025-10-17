"""This module must be lazy loaded due to pandas import."""

import os
from typing import Any, Dict

import pandas as pd
from iso639 import Lang

################################################################
# data_licenses

dir_name = os.path.dirname(__file__)
licenses = pd.read_csv(os.path.join(dir_name, "licenses.csv"))
licences_data_or_software = licenses[licenses["domain_data"] | licenses["domain_software"]]
licenses = licenses[["id", "title"]]
licenses = [(d[1]["id"].lower(), d[1]["title"]) for d in licenses.iterrows()]
licences_data_or_software = licences_data_or_software[["id", "title"]]
licences_data_or_software = [(d[1]["id"].lower(), d[1]["title"]) for d in licences_data_or_software.iterrows()]

################################################################
# languages

dir_name = os.path.dirname(__file__)
lang = pd.read_csv(os.path.join(dir_name, "languages-iso-639-2.csv"))
lang["ISO 639-1 Code"] = lang["ISO 639-1 Code"].apply(lambda x: x.strip())
lang = lang[lang["ISO 639-1 Code"] != ""]
lang = lang[["ISO 639-2 Code", "English name of Language", "ISO 639-1 Code"]]
lang = [(d[1]["ISO 639-2 Code"].lower(), d[1]["English name of Language"]) for d in lang.iterrows()]

################################################################
# metadata mappings


def dc_to_solidipes(dc_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Dublin Core Qualified metadata to solidipes-compliant, solidipes-adjacent metadata.

    Args:
        dc_metadata (dict): Input metadata in Dublin Core Qualified format

    Returns:
        dict: Transformed metadata in solidipes format
    """
    solidipes_metadata = {}

    # In Dspace5, the fields are strings and such.
    # In Dspace7, they are dicts with the actual value stored in a field.
    test_field = dc_metadata["dc.title"][0]
    if isinstance(test_field, dict):
        empty_default = [{"value": ""}]
    else:
        empty_default = [""]

    """
    print("\n")
    for x in sorted(dc_metadata.keys()):
        print(x)
    """
    print([dc_metadata.get("dc.title", "")])

    def get_single_element(x):
        if isinstance(x, str):
            return x
        elif isinstance(x, list):
            return get_single_element(x[0])
        else:
            return x["value"]

    def get_all_elements(y):
        return [get_single_element(x) for x in y]

    solidipes_metadata["zz_orig_metadata"] = dc_metadata

    doi_element = dc_metadata.get("dc.identifier.doi", empty_default)
    solidipes_metadata["doi"] = get_single_element(doi_element)

    # Transform creators
    creator_elements = dc_metadata.get("dc.contributor.author", empty_default)
    if isinstance(creator_elements, dict) or isinstance(creator_elements, str):
        creator_elements = [creator_elements]
    solidipes_metadata["creators"] = [{"name": creator} for creator in get_all_elements(creator_elements)]

    # Transform titles
    # titles = dc_metadata.get("dc:title", [])
    # if isinstance(titles, str):
    #    titles = [titles]
    # solidipes_metadata["titles"] = [{"title": title} for title in titles]
    title_elements = dc_metadata.get("dc.title", empty_default)
    solidipes_metadata["title"] = get_single_element(title_elements)

    # Publisher
    publisher_elements = dc_metadata.get("dc.publisher", empty_default)
    solidipes_metadata["publisher"] = get_single_element(publisher_elements)

    # Publication Year (extract from date)
    date_element = dc_metadata.get("dc.date.issued", empty_default)
    if date_element:
        solidipes_metadata["publication_date"] = get_single_element(date_element)

    # Subjects (Keywords)
    subjects = dc_metadata.get("dc.subject", [])
    subjects += dc_metadata.get("dc.subject.ddc", [])
    if isinstance(subjects, str):
        subjects = [subjects]
    solidipes_metadata["keywords"] = get_all_elements(subjects)

    # Contributors
    contributors = dc_metadata.get("dc.contributor", [])
    if isinstance(contributors, str):
        contributors = [contributors]
    solidipes_metadata["contributors"] = [
        {"contributorType": "Other", "name": contributor} for contributor in get_all_elements(contributors)
    ]

    # Language
    language_elements = dc_metadata.get("dc.language.iso", empty_default)
    if language_elements == empty_default:
        solidipes_metadata["language"] = "eng"
    else:
        lang_iso693_1 = Lang(get_single_element(language_elements))
        solidipes_metadata["language"] = lang_iso693_1.pt2b

    # Resource Type
    upload_type_element = dc_metadata.get("dc.type", empty_default)
    # Dublin Core will often contain non-standard values
    standard_dc_types = {
        "text": "text",
        "image": "image",
        "sound": "sound",
        "dataset": "dataset",
        "software": "software",
        "interactive": "dataset",
        "event": "event",
        "physical object": "physicalobject",
    }
    if upload_type_element == empty_default:
        solidipes_metadata["upload_type"] = "dataset"
    elif get_single_element(upload_type_element).lower() not in standard_dc_types:
        # Map non-standard types to a safe value
        solidipes_metadata["upload_type"] = "dataset"
    else:
        solidipes_metadata["upload_type"] = standard_dc_types[get_single_element(upload_type_element).lower()]

    version_elements = dc_metadata.get("dc.description.version", empty_default)
    solidipes_metadata["version"] = get_single_element(version_elements)

    return solidipes_metadata


def solidipes_to_dspace7(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform solidipes-compliant/solidipes-adjacent metadata to DSpace7 patch-ready metadata,
    i.e. a list of field insertion operations.

    Args:
        metadata (dict): solidipes metadata

    Returns:
        dict: Transformed metadata in DSpace7 patch-ready Dublin Core format
    """

    solidipes_dc_types_map = {
        "text": "text",
        "image": "image",
        "sound": "sound",
        "dataset": "dataset",
        "software": "software",
        "event": "event",
        "physicalobject": "physical object",
    }

    d7_metadata = []
    empty_default = [""]

    def map_single_field(solidipes_field, dc_field, mymap=None):
        solidipes_elements = metadata.get(solidipes_field, empty_default)
        if isinstance(solidipes_elements, str):
            solidipes_elements = [solidipes_elements]
        for idx, x in enumerate(solidipes_elements):
            if mymap is None:
                value = x
            else:
                try:
                    value = mymap[x]
                except KeyError:
                    value = x
            return {
                "op": "add",
                "path": f"/metadata/{dc_field}/{idx}",
                "value": [{"value": value}],
            }

    d7_metadata.append(map_single_field("title", "dc.title"))
    d7_metadata.append(map_single_field("description", "dc.description.abstract"))
    d7_metadata.append(map_single_field("doi", "dc.identifier.doi"))
    d7_metadata.append(map_single_field("language", "dc.language.iso"))
    d7_metadata.append(map_single_field("publication_date", "dc.date.issued"))
    d7_metadata.append(map_single_field("publisher", "dc.publisher"))
    d7_metadata.append(map_single_field("keywords", "dc.subject"))
    d7_metadata.append(map_single_field("type", "dc.type", solidipes_dc_types_map))

    # Transform creators
    creator_elements = metadata.get("creators", empty_default)
    for idx, x in enumerate(creator_elements):
        operation = {
            "op": "add",
            "path": f"/metadata/dc.contributor.author/{idx}",
            "value": [{"value": x["name"]}],
        }
        d7_metadata.append(operation)
        # FIXME? Either wrong DC property, or not supported at all
        """
        if "affiliation" in x:
            d7_metadata.append(
                {
                    "op": "add",
                    "path": f"/metadata/dc.contributor.affiliation/{idx}",
                    "value": [{"value": x["affiliation"]}],
                }
            )
        """

    return d7_metadata
