import argparse
import csv
import datetime
import difflib
import hashlib
import json
import multiprocessing
import os
import re
import warnings
from collections import defaultdict
from pathlib import Path

from compliance_checker import __version__ as cc_version
from compliance_checker.runner import CheckSuite

from cc_qa._version import version
from cc_qa.con_checks import compatibility_checks as comp  # noqa
from cc_qa.con_checks import consistency_checks as cons  # noqa
from cc_qa.con_checks import continuity_checks as cont  # noqa
from cc_qa.con_checks import dataset_coverage_checks, inter_dataset_consistency_checks

checker_dict = {
    "cc6": "CORDEX-CMIP6",
    "cf": "CF-Conventions",
    "mip": "MIP",
    # "wcrp-cmip5": "CMIP5",
    "wcrp_cmip6": "CMIP6",
    # "wcrp_cmip7": "CMIP7-AFT",
    # "wcrp_cmip7": "CMIP7",
    # "wcrp_cordex": "CORDEX",
    # "wcrp_cordex_cmip6": "CORDEX-CMIP6",
    # "obs4mips": "Obs4MIPs",
    # "input4mips": "Input4MIPs",
}
checker_release_versions = {}
checker_dict_ext = {
    # "pcons": "ParentConsistency"
    "cons": "Consistency",
    "cont": "Continuity",
    "comp": "Compatibility",
    **checker_dict,
}

_timestamp_with_ms = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")
_timestamp_filename = datetime.datetime.strptime(
    _timestamp_with_ms, "%Y%m%d-%H%M%S%f"
).strftime("%Y%m%d-%H%M")
_timestamp_pprint = datetime.datetime.strptime(
    _timestamp_with_ms, "%Y%m%d-%H%M%S%f"
).strftime("%Y-%m-%d %H:%M")


class QAResultAggregator:
    def __init__(self, checker_dict):
        """
        Initialize the aggregator with an empty summary.
        """
        self.summary = {
            "error": defaultdict(
                lambda: defaultdict(lambda: defaultdict(list))
            ),  # No weight, just function -> error msg
            "fail": defaultdict(
                lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
            ),  # weight -> test -> msg -> dsid -> filenames
        }
        self.checker_dict = checker_dict

    def update(self, result_dict, dsid, file_name):
        """
        Update the summary with a single result of a cc-run.
        """
        for checker in result_dict:
            for test in result_dict[checker]:
                if test == "errors":
                    for function_name, error_msg in result_dict[checker][
                        "errors"
                    ].items():
                        self.summary["error"][
                            f"[{checker_dict[checker]}] " + function_name
                        ][error_msg][dsid].append(file_name)
                else:
                    score, max_score = result_dict[checker][test]["value"]
                    weight = result_dict[checker][test].get("weight", 3)
                    msgs = result_dict[checker][test].get("msgs", [])
                    if score < max_score:  # test outcome: fail
                        for msg in msgs:
                            self.summary["fail"][weight][
                                f"[{checker_dict[checker]}] " + test
                            ][msg][dsid].append(file_name)

    def update_ds(self, result_dict, dsid):
        """
        Update the summary with a single result of a cc-qa run.
        """
        for checker in result_dict:
            for test in result_dict[checker]:
                if test == "errors":
                    for function_name, errdict in result_dict[checker][
                        "errors"
                    ].items():
                        for file_name in errdict["files"]:
                            self.summary["error"][
                                f"[{checker_dict_ext[checker]}] " + function_name
                            ][errdict["msg"]][dsid].append(file_name)
                else:
                    weight = result_dict[checker][test].get("weight", 3)
                    fails = result_dict[checker][test].get("msgs", {})
                    for msg, file_names in fails.items():
                        for file_name in file_names:
                            self.summary["fail"][weight][
                                f"[{checker_dict_ext[checker]}] " + test
                            ][msg][dsid].append(file_name)

    def sort(self):
        """
        Sort the summary.
        """
        self.summary["fail"] = dict(sorted(self.summary["fail"].items(), reverse=True))
        for key in self.summary["fail"]:
            self.summary["fail"][key] = dict(sorted(self.summary["fail"][key].items()))

        # Sort errors by function name
        for checker in self.summary["error"]:
            self.summary["error"][checker] = dict(
                sorted(self.summary["error"][checker].items())
            )

    @staticmethod
    def cluster_messages(messages, threshold):
        clusters = []
        while messages:
            base = messages.pop(0)
            cluster = [base]
            to_remove = []
            for msg in messages:
                ratio = difflib.SequenceMatcher(None, base, msg).ratio()
                if ratio >= threshold:
                    cluster.append(msg)
                    to_remove.append(msg)
            for msg in to_remove:
                messages.remove(msg)
            clusters.append(cluster)
        return clusters

    @staticmethod
    def generalize_message_group(messages):
        if len(messages) == 1:
            return messages[0], {}

        # Split messages into tokens
        split_messages = [re.findall(r"\w+|\W", m) for m in messages]
        transposed = list(zip(*split_messages))
        template = []
        placeholders = {}
        var_index = 0

        for i, tokens in enumerate(transposed):
            unique_tokens = set(tokens)
            if len(unique_tokens) == 1:
                template.append(tokens[0])
            else:
                var_name = chr(ord("A") + var_index)
                template.append(f"{{{var_name}}}")
                placeholders[var_name] = tokens[0]
                var_index += 1

        # Merge placeholders if possible
        template, placeholders = QAResultAggregator.merge_placeholders(
            template, placeholders
        )

        # Return the generalized message and the placeholders
        generalized = "".join(template)
        return generalized, placeholders

    @staticmethod
    def merge_placeholders(list_of_strings, dictionary, skip=0):
        def find_next_two_placeholders(list_of_strings, skip):
            placeholders = [
                s for s in list_of_strings if s.startswith("{") and s.endswith("}")
            ]
            if len(placeholders) < 2:
                return None, None
            return placeholders[skip] if len(placeholders) >= skip + 1 else None, (
                placeholders[skip + 1] if len(placeholders) >= skip + 2 else None
            )

        def extract_text_between_placeholders(
            list_of_strings, placeholder1, placeholder2
        ):
            idx1 = list_of_strings.index(placeholder1)
            idx2 = list_of_strings.index(placeholder2)
            return "".join(list_of_strings[idx1 + 1 : idx2])

        def merge_two_placeholders(
            placeholder1, placeholder2, text_between, dictionary
        ):
            new_value = (
                dictionary[placeholder1.lstrip("{").rstrip("}")]
                + text_between
                + dictionary[placeholder2.lstrip("{").rstrip("}")]
            )
            dictionary[placeholder1.lstrip("{").rstrip("}")] = new_value
            del dictionary[placeholder2.lstrip("{").rstrip("}")]
            return dictionary

        def update_placeholder_names(list_of_strings, dictionary):
            old_placeholders = sorted(list(dictionary.keys()))
            new_placeholders = [
                chr(ord("A") + i) for i in range(0, len(old_placeholders))
            ]
            new_dictionary = dict(
                zip(new_placeholders, [dictionary[val] for val in old_placeholders])
            )
            for old, new in zip(old_placeholders, new_placeholders):
                list_of_strings = [
                    s.replace("{" + old + "}", "{" + new + "}") for s in list_of_strings
                ]
            return list_of_strings, new_dictionary

        def replace_placeholders_with_new_one(
            list_of_strings, placeholder1, placeholder2
        ):
            idx1 = list_of_strings.index(placeholder1)
            idx2 = list_of_strings.index(placeholder2)
            list_of_strings_new = list_of_strings[:idx1] + [placeholder1]
            if idx2 < len(list_of_strings) + 1:
                list_of_strings_new += list_of_strings[idx2 + 1 :]
            return list_of_strings_new

        if not any(s.startswith("{") and s.endswith("}") for s in list_of_strings):
            return list_of_strings, dictionary

        placeholder1, placeholder2 = find_next_two_placeholders(list_of_strings, skip)
        if placeholder1 is None or placeholder2 is None:
            return list_of_strings, dictionary

        text_between = extract_text_between_placeholders(
            list_of_strings, placeholder1, placeholder2
        )
        if len(text_between) < 5:
            dictionary = merge_two_placeholders(
                placeholder1, placeholder2, text_between, dictionary
            )
            list_of_strings = replace_placeholders_with_new_one(
                list_of_strings, placeholder1, placeholder2
            )
            list_of_strings, dictionary = update_placeholder_names(
                list_of_strings, dictionary
            )
            return QAResultAggregator.merge_placeholders(
                list_of_strings, dictionary, skip
            )
        else:
            return QAResultAggregator.merge_placeholders(
                list_of_strings, dictionary, skip + 1
            )

    def cluster_summary(self, threshold=0.75):
        self.clustered_summary = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        )
        for status in self.summary:
            if status == "error":
                for test_id in self.summary[status]:
                    messages = list(self.summary[status][test_id].keys())
                    # Pass a copy of messages to cluster_messages to generate clusters
                    clusters = QAResultAggregator.cluster_messages(
                        messages[:], threshold
                    )

                    for cluster in clusters:
                        generalized, placeholders = (
                            QAResultAggregator.generalize_message_group(cluster)
                        )
                        example_parts = ", ".join(
                            [
                                (
                                    f"{k}='{v[0]}'"
                                    if isinstance(v, list)
                                    else f"{k}='{v}'"
                                )
                                for k, v in placeholders.items()
                            ]
                        )
                        if example_parts:
                            msg_summary = f"{generalized} ({len(cluster)} occurrences, e.g. {example_parts})"
                        else:
                            msg_summary = f"{generalized}{' (' + str(len(cluster)) + ' occurrences)' if len(cluster) > 1 else ''}"

                        # Gather all ds_ids and filenames across the cluster
                        combined = defaultdict(set)
                        for message in cluster:
                            for ds_id, files in self.summary[status][test_id][
                                message
                            ].items():
                                combined[ds_id].update(files)

                        # Shorten file lists to one example
                        formatted = {
                            ds_id
                            + " ("
                            + str(len(files))
                            + f" file{'s' if len(files) > 1 else ''} affected)": (
                                [f"e.g. '{next(iter(files))}'"]
                                if len(files) > 1
                                else [f"'{next(iter(files))}'"]
                            )
                            for ds_id, files in combined.items()
                        }

                        self.clustered_summary[status][test_id][msg_summary] = formatted
            elif status == "fail":
                for weight in self.summary[status]:
                    for test_id in self.summary[status][weight]:
                        messages = list(self.summary[status][weight][test_id].keys())
                        # Pass a copy of messages to cluster_messages to generate clusters
                        clusters = QAResultAggregator.cluster_messages(
                            messages[:], threshold
                        )

                        for cluster in clusters:
                            generalized, placeholders = (
                                QAResultAggregator.generalize_message_group(cluster)
                            )
                            example_parts = ", ".join(
                                [
                                    (
                                        f"{k}='{v[0]}'"
                                        if isinstance(v, list)
                                        else f"{k}='{v}'"
                                    )
                                    for k, v in placeholders.items()
                                ]
                            )
                            if example_parts:
                                msg_summary = f"{generalized} ({len(cluster)} occurrences, e.g. {example_parts})"
                            else:
                                msg_summary = f"{generalized}{' (' + str(len(cluster)) + ' occurrences)' if len(cluster) > 1 else ''}"

                            # Gather all ds_ids and filenames across the cluster
                            combined = defaultdict(set)
                            for message in cluster:
                                for ds_id, files in self.summary[status][weight][
                                    test_id
                                ][message].items():
                                    combined[ds_id].update(files)

                            # Shorten file lists to one example
                            formatted = {
                                ds_id
                                + " ("
                                + str(len(files))
                                + f" file{'s' if len(files) > 1 else ''} affected)": (
                                    [f"e.g. '{next(iter(files))}'"]
                                    if len(files) > 1
                                    else [f"'{next(iter(files))}'"]
                                )
                                for ds_id, files in combined.items()
                            }

                            self.clustered_summary[status][weight][test_id][
                                msg_summary
                            ] = formatted


def get_default_result_dir():
    global _timestamp
    global _timestamp_with_ms
    hash_object = hashlib.md5(_timestamp_with_ms.encode())
    return (
        os.path.abspath(".")
        + f"/cc-qa-results_{_timestamp_filename}_{hash_object.hexdigest()}"
    )


def get_dsid(files_to_check_dict, dataset_files_map_ext, file_path, project_id):
    dir_id = files_to_check_dict[file_path]["id_dir"].split("/")
    fn_id = files_to_check_dict[file_path]["id_fn"].split("_")
    if project_id in dir_id:
        dsid = ".".join(dir_id[dir_id.index(project_id) :])
    else:
        dsid = ".".join(dir_id)
    if len(dataset_files_map_ext[files_to_check_dict[file_path]["id_dir"]].keys()) > 1:
        dsid += "." + ".".join(fn_id)
    return dsid


def get_checker_release_versions(checkers, checker_options={}):
    global checker_release_versions
    global checker_dict
    global checker_dict_ext
    check_suite = CheckSuite(options=checker_options)
    check_suite.load_all_available_checkers()
    for checker in checkers:
        if checker.split(":")[0] not in checker_release_versions:
            if checker.split(":")[0] in checker_dict:
                checker_release_versions[checker.split(":")[0]] = (
                    check_suite.checkers.get(
                        checker, "unknown version"
                    )._cc_spec_version
                )
            elif checker.split(":")[0] in checker_dict_ext:
                checker_release_versions[checker.split(":")[0]] = version


def run_compliance_checker(file_path, checkers, checker_options={}):
    """
    Run the compliance checker on a file with the specified checkers and options.

    Parameters:
        file_path (str): Path to the file to be checked.
        checkers (list): List of checkers to run.
        checker_options (dict): Dictionary of options for each checker.
                                Example format: {"cf": {"check_dimension_order": True}}
    """
    check_suite = CheckSuite(options=checker_options)
    check_suite.load_all_available_checkers()
    ds = check_suite.load_dataset(file_path)
    include_checks = None
    # Run only time checks if time_checks_only option is set
    if checker_options.get("cc6", {}).get(
        "time_checks_only", False
    ) or checker_options.get("mip", {}).get("time_checks_only", False):
        include_checks = [
            "check_time_continuity",
            "check_time_bounds",
            "check_time_range",
        ]
    else:
        include_checks = None
    if include_checks:
        results = {}
        for checker in checkers:
            if include_checks and "cc6:latest" in checker or "mip:latest" in checker:
                results.update(
                    check_suite.run_all(ds, [checker], include_checks, skip_checks=[])
                )
            else:
                results.update(
                    check_suite.run_all(
                        ds, [checker], include_checks=None, skip_checks=[]
                    )
                )
        return results
    return check_suite.run_all(ds, checkers, include_checks=None, skip_checks=[])


def track_checked_datasets(checked_datasets_file, checked_datasets):
    with open(checked_datasets_file, "a") as file:
        writer = csv.writer(file)
        for dataset_id in checked_datasets:
            writer.writerow([dataset_id])


def process_file(
    file_path,
    checkers,
    checker_options,
    files_to_check_dict,
    processed_files,
    progress_file,
):
    # Read result from disk if check was run previously
    result_file = files_to_check_dict[file_path]["result_file"]
    consistency_file = files_to_check_dict[file_path]["consistency_file"]
    if (
        file_path in processed_files
        and os.path.isfile(result_file)
        and (
            os.path.isfile(consistency_file)
            or not any(cn.startswith("cc6") or cn.startswith("mip") for cn in checkers)
        )
    ):
        with open(result_file) as file:
            print(f"Read result from disk for '{file_path}'.")
            result = json.load(file)
        # If no runtime errors were registered last time, return results, otherwise rerun checks
        # Potentially add more conditions to rerun checks:
        #  eg. rerun checks if runtime errors occured
        #      rerun checks if lvl 1 checks failed
        #      rerun checks if lvl 1 and 2 checks failed
        #      rerun checks if any checks failed
        #      rerun checks if forced by user
        if all(result[checker.split(":")[0]]["errors"] == {} for checker in checkers):
            return file_path, result
        else:
            print(f"Rerunning previously erroneous checks for '{file_path}'.")
    else:
        print(f"Running checks for '{file_path}'.")

    # Else run check
    result = run_compliance_checker(file_path, checkers, checker_options)

    # Check result
    check_results = dict()
    # Note: the key in the errors dict is not the same as the check name!
    #       The key is the checker function name, while the check.name
    #       is the description.
    for checkerv in checkers:
        checker = checkerv.split(":")[0]
        check_results[checker] = dict()
        check_results[checker]["errors"] = {}
        # print()
        # print("name",result[checker][0][0].name)
        # print("weight", result[checker][0][0].weight)
        # print("value", result[checker][0][0].value)
        # print("msgs", result[checker][0][0].msgs)
        # print("method", result[checker][0][0].check_method)
        # print("children", result[checker][0][0].children)
        # quit()
        for check in result[checkerv][0]:
            check_results[checker][check.name] = {}
            check_results[checker][check.name]["weight"] = check.weight
            check_results[checker][check.name]["value"] = check.value
            check_results[checker][check.name]["msgs"] = check.msgs
            check_results[checker][check.name]["method"] = check.check_method
            check_results[checker][check.name]["children"] = check.children
        for check_method in result[checkerv][1]:
            a = result[checkerv][1][check_method][1]
            while True:
                if a.tb_frame.f_code.co_name == check_method:
                    break
                else:
                    a = a.tb_next
            check_results[checker]["errors"][
                check_method
            ] = f"Exception: {result[checkerv][1][check_method][0]} at {a.tb_frame.f_code.co_filename}:{a.tb_frame.f_lineno} in function/method '{a.tb_frame.f_code.co_name}'."
            vars = [
                j
                for i, j in a.tb_frame.f_locals.items()
                if "var" in i and isinstance(j, str)
            ]
            if vars:
                check_results[checker]["errors"][
                    check_method
                ] += f" Potentially affected variables: {', '.join(vars)}."

    # Write result to disk
    with open(result_file, "w") as f:
        json.dump(check_results, f, ensure_ascii=False, indent=4)

    # Register file in progress file
    with open(progress_file, "a") as file:
        file.write(file_path + "\n")

    return file_path, check_results


def process_dataset(
    ds,
    ds_map,
    checkers,
    checker_options,
    files_to_check_dict,
    processed_datasets,
    progress_file,
):
    # Read result from disk if check was run previously
    result_file = files_to_check_dict[ds_map[ds][0]]["result_file_ds"]
    if ds in processed_datasets and os.path.isfile(result_file):
        with open(result_file) as file:
            print(f"Read result from disk for '{ds}'.")
            result = json.load(file)
        # If no runtime errors were registered last time, return results, otherwise rerun checks
        # Potentially add more conditions to rerun checks:
        #  eg. rerun checks if runtime errors occured
        #      rerun checks if lvl 1 checks failed
        #      rerun checks if lvl 1 and 2 checks failed
        #      rerun checks if any checks failed
        #      rerun checks if forced by user
        if all(
            result[checker.split(":")[0]]["errors"] == {}
            for checker in checkers
            if checker.split(":")[0] in result
            and "errors" in result[checker.split(":")[0]]
        ):
            return ds, result
        else:
            print(f"Rerunning previously erroneous checks for '{ds}'.")
    else:
        print(f"Running checks for '{ds}'.")

    # Else run check
    result = dict()
    for checkerv in checkers:
        checker = checkerv.split(":")[0]
        if checker in globals():
            checker_fct = globals()[checker]
            result[checker] = checker_fct(
                ds, ds_map, files_to_check_dict, checker_options[checker]
            )
        else:
            result[checker] = {
                "errors": {
                    checker: {
                        "msg": f"Checker '{checker}' not found.",
                        "files": ds_map[ds],
                    },
                },
            }

    # Write result to disk
    with open(result_file, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    # Register file in progress file
    with open(progress_file, "a") as file:
        file.write(ds + "\n")

    return ds, result


def call_process_file(args):
    return process_file(*args)


def call_process_dataset(args):
    return process_dataset(*args)


def parse_options(opts):
    """
    Helper function to parse possible options. Splits option into key/value
    pairs and optionally a value for the checker option. The separator
    is a colon. Adapted from
    https://github.com/ioos/compliance-checker/blob/cbb40ed1981c169b74c954f0775d5bd23005ed23/cchecker.py#L23

    Parameters:
        opts: Iterable of strings with options

    Returns:
        Dictionary with keys as checker type (i.e. "mip").
        Each value is a dictionary where keys are checker options and values
        are checker option values or None if not provided.
    """
    options_dict = defaultdict(dict)
    for opt_str in opts:
        try:
            checker_type, checker_opt, *checker_val = opt_str.split(":", 2)
            checker_val = checker_val[0] if checker_val else None
        except ValueError:
            raise ValueError(
                f"Could not split option '{opt_str}', seems illegally formatted. The required format is: '<checker>:<option_name>[:<option_value>]', eg. 'mip:tables:/path/to/Tables'."
            )
        if checker_type != "mip":
            raise ValueError(
                f"Currently, only options for 'mip' checker are supported, got '{checker_type}'."
            )
        options_dict[checker_type][checker_opt] = checker_val
    return options_dict


def main():
    # CLI
    parser = argparse.ArgumentParser(description="Run QA checks")
    parser.add_argument(
        "parent_dir",
        type=str,
        help="Parent directory to scan for files",
        nargs="?",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default=get_default_result_dir(),
        help="Directory to store QA results. Needs to be non-existing or empty or from previous QA run.",
    )
    parser.add_argument(
        "-O",
        "--option",
        default=[],
        action="append",
        help="Additional options to be passed to the checkers. Format: '<checker>:<option_name>[:<option_value>]'. Multiple invocations possible.",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="append",
        help="The test to run ('cc6:latest' or 'cf:<version>', can be specified multiple times, eg.: '-t cc6:latest -t cf:1.8') - default: running 'cc6:latest' and 'cf:1.11'.",
    )
    parser.add_argument(
        "-i",
        "--info",
        type=str,
        help="Informtaion to be included in the QA results identifying the current run, eg. the experiment_id.",
    )
    parser.add_argument(
        "-r",
        "--resume",
        action="store_true",
        help="Specify to continue a previous QC run. Requires the <output_dir> argument to be set.",
    )
    parser.add_argument(
        "-C",
        "--include_consistency_checks",
        action="store_true",
        help="Include basic consistency and continuity checks. Default: False.",
    )
    args = parser.parse_args()

    result_dir = os.path.abspath(args.output_dir)
    parent_dir = os.path.abspath(args.parent_dir) if args.parent_dir else None
    tests = sorted(args.test) if args.test else []
    info = args.info if args.info else ""
    resume = args.resume
    include_consistency_checks = (
        args.include_consistency_checks if args.include_consistency_checks else False
    )
    cl_checker_options = parse_options(args.option)

    # Progress file to track already checked files
    progress_file = Path(result_dir, "progress.txt")
    # Progress file to track already checked datasets
    dataset_file = Path(result_dir, "progress_datasets.txt")

    # Resume information stored in a json file
    resume_info_file = Path(result_dir, ".resume_info")

    # Deal with result_dir
    if not os.path.exists(result_dir):
        if resume:
            resume = False
            warnings.warn(
                "Resume is set but specified output_directory does not exist. Starting a new QA run..."
            )
        os.mkdir(result_dir)
    elif os.listdir(result_dir) != []:
        if resume:
            required_files = [progress_file, resume_info_file]
            required_paths = [os.path.join(result_dir, p) for p in ["tables"]]
            if not all(os.path.isfile(rfile) for rfile in required_files) or not all(
                os.path.isdir(rpath) for rpath in required_paths
            ):
                raise Exception(
                    "Resume is set but specified output_directory cannot be identified as output_directory of a previous QA run."
                )
        else:
            if "progress.txt" in os.listdir(
                result_dir
            ) and ".resume_info" in os.listdir(result_dir):
                raise Exception(
                    "Specified output_directory is not empty but can be identified as output_directory of a previous QA run. Use'-r' or '--resume' (together with '-o' or '--output_dir') to continue the previous QA run or choose a different output_directory instead."
                )
            else:
                raise Exception("Specified output_directory is not empty.")
    else:
        if resume:
            resume = False
            warnings.warn(
                "Resume is set but specified output_directory is empty. Starting a new QA run..."
            )
    if resume:
        print(f"Resuming previous QA run in '{result_dir}'")
        with open(os.path.join(result_dir, ".resume_info")) as f:
            try:
                resume_info = json.load(f)
                required_keys = ["parent_dir", "info", "tests"]
                if not all(key in resume_info for key in required_keys):
                    raise Exception(
                        "Invalid .resume_info file. It should contain the keys 'parent_dir', 'info', and 'tests'."
                    )
                if not (
                    isinstance(resume_info["parent_dir"], str)
                    and isinstance(resume_info["info"], str)
                    and isinstance(resume_info["tests"], list)
                    and all(isinstance(test, str) for test in resume_info["tests"])
                ):
                    raise Exception(
                        "Invalid .resume_info file. 'parent_dir' and 'info' should be strings, and 'tests' should be a list of strings."
                    )
            except json.JSONDecodeError:
                raise Exception(
                    "Invalid .resume_info file. It should be a valid JSON file."
                )
            if tests and sorted(tests) != resume_info["tests"]:
                raise Exception("Cannot resume a previous QA run with different tests.")
            else:
                tests = resume_info["tests"]
            if info and info != resume_info["info"]:
                warnings.warn(
                    f"<info> argument differs from the originally specified <info> argument ('{resume_info['info']}'). Using the new specification."
                )
            if parent_dir is None:
                parent_dir = resume_info["parent_dir"]
            if parent_dir and Path(parent_dir) != Path(resume_info["parent_dir"]):
                raise Exception(
                    "Cannot resume a previous QA run with different <parent_dir>."
                )
            if cl_checker_options and cl_checker_options != resume_info.get(
                "checker_options", {}
            ):
                raise Exception(
                    "Cannot resume a previous QA run with different <option> arguments."
                )
            else:
                parent_dir = Path(resume_info["parent_dir"])
            if "include_consistency_checks" in resume_info:
                include_consistency_checks = resume_info["include_consistency_checks"]
    else:
        print(f"Storing check results in '{result_dir}'")

    # Deal with tests
    if not tests:
        checkers = ["cc6", "cf"]
        checkers_versions = {"cc6": "latest", "cf": "1.11"}
        checker_options = defaultdict(dict)
    else:
        test_regex = re.compile(r"^[a-z0-9_]+:(latest|[0-9]+(\.[0-9]+)*)$")
        if not all([test_regex.match(test) for test in tests]):
            raise Exception(
                f"Invalid test(s) specified. Please specify tests in the format 'checker_name:version'. Currently supported are: {', '.join(list(checker_dict.keys()))}, eerie."
            )
        checkers = [test.split(":")[0] for test in tests]
        if sorted(checkers) != sorted(list(set(checkers))):
            raise Exception("Cannot specify multiple instances of the same checker.")
        checkers_versions = {
            test.split(":")[0]: (
                test.split(":")[1]
                if len(test.split(":")) == 2 and test.split(":")[1] != ""
                else "latest"
            )
            for test in tests
        }
        checker_options = defaultdict(dict)
        if "cc6" in checkers_versions and checkers_versions["cc6"] != "latest":
            checkers_versions["cc6"] = "latest"
            warnings.warn("Version of checker 'cc6' must be 'latest'. Using 'latest'.")
        if "mip" in checkers_versions and checkers_versions["mip"] != "latest":
            checkers_versions["mip"] = "latest"
            warnings.warn("Version of checker 'mip' must be 'latest'. Using 'latest'.")
            if "tables" not in cl_checker_options["mip"]:
                raise Exception(
                    "Option 'tables' with path to CMOR tables as value must be specified for checker 'mip'."
                )
        # EERIE support - hard code
        if "eerie" in checkers_versions:
            checkers_versions["mip"] = "latest"
            del checkers_versions["eerie"]
            if "tables" in cl_checker_options["eerie"]:
                cl_checker_options["mip"]["tables"] = cl_checker_options["eerie"][
                    "tables"
                ]
            elif "tables" not in cl_checker_options["mip"]:
                cl_checker_options["mip"][
                    "tables"
                ] = "/work/bm0021/cmor_tables/eerie_cmor_tables/Tables"
        if sum(1 for ci in checkers_versions if ci in ["mip", "cc6"]) > 1:
            raise Exception(
                "ERROR: Cannot run both 'cc6' and 'mip' checkers at the same time."
            )
        if any(test not in checker_dict.keys() for test in checkers_versions):
            raise Exception(
                f"Invalid test(s) specified. Supported are: {', '.join(checker_dict.keys())}"
            )

    # Combine checkers and versions
    #  (checker_options are hardcoded)
    checkers = sorted([f"{c}:{v}" for c, v in checkers_versions.items()])

    # Does parent_dir exist?
    if parent_dir is None:
        parser.error("Missing required argument <parent_dir>.")
    elif not os.path.exists(parent_dir):
        raise Exception(f"The specified <parent_dir> '{parent_dir}' does not exist.")

    # Write resume file
    resume_info = {
        "parent_dir": str(parent_dir),
        "info": info,
        "tests": checkers,
    }
    if include_consistency_checks:
        resume_info["include_consistency_checks"] = True
    if cl_checker_options:
        resume_info["checker_options"] = cl_checker_options
    with open(os.path.join(result_dir, ".resume_info"), "w") as f:
        json.dump(resume_info, f)

    # If only cf checker is selected, run cc6 time checks only
    if (
        not any(cn.startswith("cc6") or cn.startswith("mip") for cn in checkers)
        and include_consistency_checks
    ):
        time_checks_only = True
        checkers.append("mip:latest")
        checkers.sort()
    else:
        time_checks_only = False

    # Ensure progress files exist
    os.makedirs(result_dir + "/tables", exist_ok=True)
    progress_file.touch()
    dataset_file.touch()

    # Check if progress files exist and read already processed files/datasets
    processed_files = set()
    with open(progress_file) as file:
        for line in file:
            processed_files.add(line.strip())
    processed_datasets = set()
    with open(dataset_file) as file:
        for line in file:
            processed_datasets.add(line.strip())

    # todo: allow black-/whitelisting (parts of) paths for checks
    path_whitelist = []
    path_blacklist = []

    #########################################################
    # Find all files to check and group them in datasets
    #########################################################
    files_to_check = []  # List of files to check
    files_to_check_dict = {}
    dataset_files_map = {}  # Map to store files grouped by their dataset_ids
    dataset_files_map_ext = (
        {}
    )  # allowing files of multiple datasets in a single directory
    for root, _, files in os.walk(parent_dir):
        for file in files:
            if file.endswith(".nc"):
                file_path = os.path.normpath(os.path.join(root, file))
                dataset_id_dir = os.path.dirname(file_path)
                dataset_id_fn = "_".join(
                    filter(
                        re.compile(r"^(?!\d{1,}-{0,1}\d{0,}$)").match,
                        os.path.splitext(os.path.basename(file_path))[0].split("_"),
                    )
                )
                dataset_timestamp = "_".join(
                    filter(
                        re.compile(r"^\d{1,}-?\d*$").match,
                        os.path.splitext(os.path.basename(file_path))[0].split("_"),
                    )
                )
                os.makedirs(result_dir + dataset_id_dir + "/result", exist_ok=True)
                os.makedirs(
                    result_dir + dataset_id_dir + "/consistency-output", exist_ok=True
                )
                result_file = (
                    result_dir
                    + dataset_id_dir
                    + "/"
                    + "result"
                    + "/"
                    + dataset_id_fn
                    + "__"
                    + dataset_timestamp
                    + ".json"
                )
                consistency_file = (
                    result_dir
                    + dataset_id_dir
                    + "/"
                    + "consistency-output"
                    + "/"
                    + dataset_id_fn
                    + "__"
                    + dataset_timestamp
                    + ".json"
                )
                if "_" in dataset_timestamp:
                    raise Exception(
                        f"Filename contains multiple time stamps: '{file_path}'"
                    )
                if any(file_path.startswith(skip_path) for skip_path in path_blacklist):
                    continue
                if path_whitelist != [] and not any(
                    file_path.startswith(use_path) for use_path in path_whitelist
                ):
                    continue
                files_to_check.append(file_path)
                files_to_check_dict[file_path] = {
                    "id_dir": dataset_id_dir,
                    "id_fn": dataset_id_fn,
                    "ts": dataset_timestamp,
                    "result_file": result_file,
                    "consistency_file": consistency_file,
                }
                if dataset_id_dir in dataset_files_map_ext:
                    if dataset_id_fn in dataset_files_map_ext[dataset_id_dir]:
                        dataset_files_map_ext[dataset_id_dir][dataset_id_fn].append(
                            file_path
                        )
                    else:
                        dataset_files_map_ext[dataset_id_dir][dataset_id_fn] = [
                            file_path
                        ]
                else:
                    dataset_files_map_ext[dataset_id_dir] = {dataset_id_fn: [file_path]}
    files_to_check = sorted(files_to_check)
    for file_path in files_to_check:
        files_to_check_dict[file_path]["id"] = get_dsid(
            files_to_check_dict, dataset_files_map_ext, file_path, "CORDEX-CMIP6"
        )
        files_to_check_dict[file_path]["result_file_ds"] = (
            result_dir
            + "/"
            + files_to_check_dict[file_path]["id_dir"]
            + "/"
            + hashlib.md5(files_to_check_dict[file_path]["id"].encode()).hexdigest()
            + ".json"
        )
        if files_to_check_dict[file_path]["id"] in dataset_files_map:
            dataset_files_map[files_to_check_dict[file_path]["id"]].append(file_path)
        else:
            dataset_files_map[files_to_check_dict[file_path]["id"]] = [file_path]
        checker_options[file_path] = {
            "mip": {
                **cl_checker_options["mip"],
                "consistency_output": files_to_check_dict[file_path][
                    "consistency_file"
                ],
                "time_checks_only": time_checks_only,
            },
            "cc6": {
                **cl_checker_options["cc6"],
                "consistency_output": files_to_check_dict[file_path][
                    "consistency_file"
                ],
                "tables_dir": result_dir + "/tables",
                "force_table_download": file_path == files_to_check[0]
                and (
                    not resume or (resume and os.listdir(result_dir + "/tables") == [])
                ),
                "time_checks_only": time_checks_only,
            },
            "cf:": {
                **cl_checker_options["cf"],
                "enable_appendix_a_checks": True,
            },
        }
        checker_options[file_path].update(
            {
                k: v
                for k, v in cl_checker_options.items()
                if k not in ["cc6", "cf", "mip"]
            }
        )

    if len(files_to_check) == 0:
        raise Exception("No files found to check.")
    else:
        print(
            f"Found {len(files_to_check)} files (organized in {len(dataset_files_map)} datasets) to check."
        )

    print()
    print("Files to check:")
    print(json.dumps(files_to_check, indent=4))
    print()
    print("Dataset - Files mapping (extended):")
    print(json.dumps(dataset_files_map_ext, indent=4))
    print()
    print("Dataset - Files mapping:")
    print(json.dumps(dataset_files_map, indent=4))
    print()
    print("Files to check dict:")
    print(json.dumps(files_to_check_dict, indent=4))
    print()

    #########################################################
    # QA Part 1 - Run all compliance-checker checks
    #########################################################

    print()
    print("#" * 50)
    print("# QA Part 1 - Run all compliance-checker checks")
    print("#" * 50)
    print()

    # Initialize the summary
    summary = QAResultAggregator(checker_dict=checker_dict_ext)

    # Calculate the number of processes
    num_processes = max(multiprocessing.cpu_count() - 4, 1)
    print(f"Using {num_processes} parallel processes for cc checks.")
    print()

    # Run the first process:
    if len(files_to_check) > 0:
        processed_file, result_first = process_file(
            files_to_check[0],
            checkers,
            checker_options[files_to_check[0]],
            files_to_check_dict,
            processed_files,
            progress_file,
        )
        summary.update(
            result_first, files_to_check_dict[processed_file]["id"], processed_file
        )
        del result_first

    # Run the rest of the processes
    if len(files_to_check) > 1:
        # Prepare the argument tuples
        args = [
            (
                x,
                checkers,
                checker_options[x],
                files_to_check_dict,
                processed_files,
                progress_file,
            )
            for x in files_to_check[1:]
        ]

        # Use a pool of workers to run jobs in parallel
        with multiprocessing.Pool(processes=num_processes, maxtasksperchild=10) as pool:
            # results = [result_first] + pool.starmap(
            #    process_file, args
            # )  # This collects all results in a list
            for processed_file, result in pool.imap_unordered(call_process_file, args):
                summary.update(
                    result, files_to_check_dict[processed_file]["id"], processed_file
                )
                del result

    # Skip continuity and consistency checks if no cc6/mip checks were run
    #   (and thus no consistency output file was created)
    if "cc6:latest" in checkers or "mip:latest" in checkers:

        #########################################################
        # QA Part 2 - Run all consistency & continuity checks
        #########################################################

        print()
        print("#" * 50)
        print("# QA Part 2 - Run consistency & continuity checks")
        print("#" * 50)
        print()

        ###########################
        # Consistency across files
        print(
            "# QA Part 2.1 - Continuity & Consistency across files of a single dataset"
        )
        print(
            "#   (Reference for consistency checks is the first file of each respective dataset timeseries)"
        )
        print()

        # Calculate the number of processes
        num_processes = max(multiprocessing.cpu_count() - 4, 1)
        # Limit the number of processes for consistency checks since a lot
        #   of files will be opened at the same time
        num_processes = min(num_processes, 10)
        print(f"Using {num_processes} parallel processes for dataset checks.")
        print()

        datasets = sorted(list(dataset_files_map.keys()))
        args = [
            (
                x,
                dataset_files_map,
                ["cons", "cont", "comp"],
                {"cons": {}, "cont": {}, "comp": {}},
                files_to_check_dict,
                processed_datasets,
                dataset_file,
            )
            for x in datasets
            if len(dataset_files_map[x]) > 1
        ]
        if len(args) > 0:
            # Use a pool of workers to run jobs in parallel
            with multiprocessing.Pool(
                processes=num_processes, maxtasksperchild=10
            ) as pool:
                for processed_ds, result in pool.imap_unordered(
                    call_process_dataset, args
                ):
                    summary.update_ds(result, processed_ds)
                    del result

        ##############################
        # Consistency across datasets
        print()
        print("# QA Part 2.2 - Continuity & Consistency across all datasets")
        print()

        # Attributes and Coordinates
        results_extra = inter_dataset_consistency_checks(
            dataset_files_map, files_to_check_dict, checker_options={}
        )
        for ds in results_extra.keys():
            summary.update_ds({"cons": results_extra[ds]}, ds)

        # Time coverage
        results_extra = dataset_coverage_checks(
            dataset_files_map, files_to_check_dict, checker_options={}
        )
        for ds in results_extra.keys():
            summary.update_ds({"cons": results_extra[ds]}, ds)
    else:
        print()
        warnings.warn(
            "Continuity & Consistency checks skipped since no cc6 checks were run."
        )

    #########################################################
    # Summarize and save results
    #########################################################

    print()
    print("#" * 50)
    print(
        f"# QA Part {'3' if 'cc6:latest' in checkers or 'mip:latest' in checkers else '2'} - Summarizing and clustering the results"
    )
    print("#" * 50)
    print()

    # todo: always the latest checker version is used atm, but the
    #       specified version should be used ("tests")
    summary.sort()
    qc_summary = summary.summary
    get_checker_release_versions(checkers)
    summary_info = {
        "id": "",
        "date": _timestamp_pprint,
        "files": str(len(files_to_check)),
        "datasets": str(len(dataset_files_map)),
        "cc_version": cc_version,
        "checkers": ", ".join(
            [
                f"{checker_dict.get(checker.split(':')[0], '')} {checker.split(':')[0]}:{checker_release_versions[checker.split(':')[0]]}"
                for checker in checkers
            ]
        ),
        "parent_dir": str(parent_dir),
    }
    dsid_common_prefix = os.path.commonprefix(list(dataset_files_map.keys()))
    if dsid_common_prefix != list(dataset_files_map.keys())[0]:
        dsid_common_prefix = dsid_common_prefix + "*"
    if info:
        summary_info["id"] = f"{info} ({dsid_common_prefix})"
    else:
        summary_info["id"] = f"{dsid_common_prefix}"
    qc_summary["info"] = summary_info

    # Save JSON file
    timestamp = _timestamp_filename
    fileid = hashlib.md5(_timestamp_with_ms.encode()).hexdigest()
    infostr = re.sub("[^a-z0-9]", "", info.lower())[:10] if info else ""
    filename = f"qa_result_{infostr}{'_' if infostr else ''}{timestamp}_{fileid}.json"
    with open(os.path.join(result_dir, filename), "w") as f:
        json.dump(qc_summary, f, indent=4, ensure_ascii=False, sort_keys=False)
    print(f"Saved QC result: {result_dir}/{filename}")

    # Save cluster
    summary.cluster_summary()
    qc_summary_clustered = summary.clustered_summary
    # print(json.dumps(qc_summary_clustered, indent=4))
    qc_summary_clustered["info"] = summary_info
    filename = (
        f"qa_result_{infostr}{'_' if infostr else ''}{timestamp}_{fileid}.cluster.json"
    )
    with open(os.path.join(result_dir, filename), "w") as f:
        json.dump(
            qc_summary_clustered, f, indent=4, ensure_ascii=False, sort_keys=False
        )
    print(f"Saved QC cluster summary: {result_dir}/{filename}")


if __name__ == "__main__":
    main()
