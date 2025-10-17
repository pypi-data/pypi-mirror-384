#!python

"""
Script to Deploy the Specified configuration to the correct places (or specified places)
"""

import logging
import argparse
import sys
import os.path
import importlib.resources
import json

import boto3
import yaml
import texttable
import jinja2


import cfnStack

_region = "us-west-2"
_timeout = 180

def get_argparse() -> argparse.ArgumentParser:
    """
    Allows the use of Documentation Tools for Argparse

    :return: args
    :rtype: argparse.Namespace
    """

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--only_profiles", help="Only deploy to these profiles even if more are configured.", default=[], action="append")
    parser.add_argument("-s", "--stackname", help="Stack Name to Deploy (Default Depoloy all in Category", default=[],
                        action="append")
    parser.add_argument("-C", "--confirm", help="Make Changes", default=False, action="store_true")
    parser.add_argument("-v", "--verbose", action="append_const", help="Verbosity Controls",
                        const=1, default=[])

    # "Live" Deployment Options
    parser.add_argument("--description", help="If using -S what description should go with the stack.",
                        default="No Description Given")
    parser.add_argument("--capabilities", help="If using -S what capabilities should go with the stack", default=[],
                        action="append")
    parser.add_argument("--regions", help="If using -S what regions should this deploy too", default=[],
                        action="append")
    parser.add_argument("--tags", help="If using -S what tags specified as tag:value to use", default=[],
                        action="append")
    parser.add_argument("--parameters", help="Parameters specified as param:value to use.", default=[],
                        action="append")
    parser.add_argument("--profiles", help="If using -S what profiles this should be deployed to.", default=[],
                        action="append")

    parser.add_argument("-D", "--stackdelete", help="Delete the Specified (Stacks)", default=False, action="store_true")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--category", help="Which Cateogry to Choose from (directory)", default=None)
    group.add_argument("-c", "--config", help="Specify a Configuration File to Deploy", default=None)
    group.add_argument("-S", "--stack", help="Specify a single Stack file deploy", default=None)

    args = parser.parse_args()

    return args

if __name__ == "__main__":

    args = get_argparse()

    VERBOSE = len(args.verbose)

    EXTRA_MODULES = ["boto3", "urllib3", "botocore",
                     "botocore.hooks", "botocore.retryhandler"]

    extra_level = logging.ERROR

    if VERBOSE == 0:
        logging.basicConfig(level=logging.ERROR)
    elif VERBOSE == 1:
        logging.basicConfig(level=logging.WARNING)
        extra_level = logging.ERROR
    elif VERBOSE == 2:
        logging.basicConfig(level=logging.INFO)
        extra_level = logging.WARNING
    elif VERBOSE == 3:
        logging.basicConfig(level=logging.DEBUG)
        extra_level = logging.INFO
    elif VERBOSE == 4:
        logging.basicConfig(level=logging.DEBUG)
        extra_level = logging.DEBUG

    for mod in EXTRA_MODULES:
        logging.getLogger(mod).setLevel(extra_level)

    logger = logging.getLogger("deploy_cf")

    action_obj = cfnStack.ActionParser(
        only_profiles = args.only_profiles,
        stackname = args.stackname,
        category = args.category,
        config = args.config,
        stack = args.stack,
        description = args.description,
        regions = args.regions,
        capabilities = args.capabilities,
        dynamic_tags = args.tags,
        parameters = args.parameters,
        profiles = args.profiles,
        delete = args.stackdelete
    )

    logger.debug("Requested Stack/Profile with New Object. \n{}".format(json.dumps(action_obj.action_stacks, indent=2)))


    result_table = texttable.Texttable(max_width=160)
    result_table.add_row(["stack", "profile", "region", "aws", "stack_valid", "changes", "action", "f_triggered"])

    should_break = False

    if len(action_obj.errors.keys()) > 0:
        logger.error("Parsing Error() on Action Obj.")
        logger.debug("Errors: {}".format(json.dumps(action_obj.errors, indent=2)))

        sys.exit(1)

    for action_tuple in action_obj.action_stacks:
        this_result = cfnStack.ProcessStack(action_tuple,
                                            confirm=args.confirm,
                                            live_add=action_obj.live_add)

        if this_result.return_status["fail"] is True:
            should_break = True

        result_table.add_row(this_result.return_table_row())

    print(result_table.draw())

    if should_break is True:
        logger.error("One or more stacks had an abnormal response.")
        sys.exit(1)
