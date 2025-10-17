#!/usr/bin/env python3

import logging
import time
import datetime
import string

import boto3
from botocore.exceptions import ClientError


class ProcessStack:
    _timeout = 180
    _region = "us-west-2"
    _valid_capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]

    def __init__(self, stack_config, confirm=False,
                 timeout=_timeout, region=_region,
                 **kwargs):

        self.logger = logging.getLogger("ProcessStack")
        self.kwargs = kwargs

        self.stack_name = stack_config["stack"]
        self.stack_cfg = stack_config["stack_cfg"]
        self.stack_config_json = stack_config["stack_config_json"]
        self.region = stack_config.get("region", region)
        self.aws_profile = stack_config.get("profile", "default")
        self.delete = stack_config.get("delete", False)
        if self.aws_profile == "default":
            # To use the default profile set to None
            self.aws_profile = None

        self.confirm = confirm
        self.timeout = timeout

        self.go = True

        self.return_status = dict(stack=self.stack_name,
                                  profile=self.aws_profile,
                                  aws="Unknown", stack_valid="Unknown",
                                  changes="Unknown", action="Nothing", fail=False)

        if self.stack_cfg.get("dynamic_name", False) is not False and isinstance(self.stack_cfg.get("dynamic_name", False), str):

            dynamic_okay = True
            # Expand Stack Name With Parameterized Data

            self.logger.debug("Live Add Things: {}".format(self.kwargs.get("live_add", {})))

            template_objs = {**self.kwargs.get("live_add", {}).get("parameters", {}),
                             **{x["ParameterKey"]: x["ParameterValue"] for x in
                                self.stack_cfg.get("parameters", list())},
                             **{x["Key"]: x["Value"] for x in self.stack_cfg.get("tags", list())}
                             }

            template = string.Template(self.stack_cfg["dynamic_name"])

            try:
                self.stack_name = template.substitute(template_objs)
            except Exception as TemplateError:
                self.logger.error("Error doing Dynamic Name Substitution : {}".format(TemplateError))
                self.logger.info("Template : {}".format(self.stack_cfg["dynamic_name"]))
                self.logger.debug("Available Replacements : {}".format(template_objs))

                self.go = False
                dynamic_okay = False
                self.return_status["stack_valid"] = "Dynamic Name Failure"
                self.return_status["fail"] = True

            else:
                self.logger.info("Dynamic Name Went from : {} to {}".format(self.stack_cfg["dynamic_name"], self.stack_name))
                self.return_status["stack"] = self.stack_name
        else:
            # No Dynamic Name Used
            self.logger.info("No Dynamic Name Used")
            dynamic_okay = True

        region_text = str()
        if self.region != self._region:
            region_text = "[{}]".format(self.region)
        self.lname = "{}/{}{}".format(self.stack_name, self.aws_profile, region_text)

        self.extend_live_add()

        if self.go:
            self.cf_client = self.get_client()

        if self.go:
            self.clean_change_sets()

        if self.go:
            self.validate_stack()

        if self.go:
            self.process_changeset()

        # self.clean_change_sets()

    def extend_live_add(self):

        live_add = self.kwargs.get("live_add", {})

        for key, value in live_add.items():
            if key == "parameters":
                for k, v in value.items():
                    this_param = {"ParameterKey": k,
                                  "ParameterValue": v}

                    if "parameters" not in self.stack_cfg.keys():
                        self.stack_cfg["parameters"] = list()

                    self.logger.debug("{} Added Live Parameter {} to Stack".format(self.lname, k))
                    self.stack_cfg["parameters"].append(this_param)

    def clean_change_sets(self):

        """
        Clean Up Unused Changesets
        :return:
        """

        if self.stack_exists() == "UPDATE":
            self.logger.info("{} Cleaning Up Any Outstanding Changestes before beginning.".format(self.lname))

            changesets = self.cf_client.list_change_sets(StackName=self.stack_name)

            outstanding_changesets = len(changesets["Summaries"])

            if outstanding_changesets > 0:
                for this_changeset in changesets["Summaries"]:
                    self.logger.info(
                        "{} Cleaning Changeset named : {}".format(self.lname, this_changeset["ChangeSetName"]))

                    try:
                        self.cf_client.delete_change_set(ChangeSetName=this_changeset["ChangeSetId"])
                    except Exception as delete_error:
                        self.logger.warning("{} Unable to Delete old Chnageset {}. Hanging Changeset".format(self.lname,
                                                                                                             this_changeset[
                                                                                                                 "ChangeSetName"]))
                        self.logger.debug("Error: {}".format(delete_error))
                        self.logger.warning("{} Continuing with Hanging Changeset, Clean Manually".format(self.lname))
                        self.go = False
                        self.return_status["fail"] = True
                    else:
                        self.logger.info(
                            "{} Successfully Deleted Changeset {}".format(self.lname, this_changeset["ChangeSetName"]))
            else:
                self.logger.info("{} No Oustanding Changests to Clean".format(self.lname))
        else:
            self.logger.info("{} New Stack, no outstanding changesets to remove.".format(self.lname))

    def return_table_row(self):

        """
        Retturns a Row of Results as an array for the table
        :return:
        """

        table_row = [self.return_status["stack"],
                     self.return_status["profile"],
                     self.region,
                     self.return_status["aws"],
                     self.return_status["stack_valid"],
                     self.return_status["changes"],
                     self.return_status["action"],
                     self.return_status["fail"]]

        return table_row

    def get_client(self):

        """
        Get Cloud Formation Client
        :return:
        """

        self.logger.info("{} : Connecting to CloudFormation".format(self.lname))

        # Validate OKAY Region

        try:
            aws_session = boto3.session.Session(profile_name=self.aws_profile, region_name=self.region)
            cf_client = aws_session.client("cloudformation")
        except Exception as error:
            self.logger.error(
                "Unable to Provision a Cloudformation Client in AWS Profile : {}".format(self.aws_profile))
            self.logger.debug("Error on Session: {}".format(error))
            self.return_status["aws"] = "Error"
            self.go = False
            self.return_status["fail"] = True
            cf_client = None
        else:
            self.return_status["aws"] = self.aws_profile

            try:
                regional_sts = aws_session.client("sts")
                regional_sts.get_caller_identity()
            except ClientError as region_error:
                self.logger.warning("Region {} Unavailable At this Time.".format(self.region))
                self.go = False
                self.return_status["aws"] = "Region Unavailable"
                self.return_status["fail"] = False
                self.return_status["action"] = "Region Ignore"

        return cf_client

    def valiedate_capabilities(self):

        """
        Validates that the configurations capabilities make sense
        """

        cap_okay = True

        requested_capabilities = self.stack_cfg.get("capabilities", list())

        invalid = [x for x in requested_capabilities if x not in self._valid_capabilities]

        if len(invalid) > 0:
            self.logger.error("Found {} invalid capabilities.".format(len(invalid)))
            self.logger.debug("Invalid Capabilities : {}".format(", ".join(invalid)))
            cap_okay = False

        return cap_okay

    def validate_stack(self):

        """
        Validate Stack Being Okay
        :return:
        """

        # Validate Stack
        self.logger.info("{} : Validating Stack Template".format(self.lname))

        try:
            self.cf_client.validate_template(TemplateBody=self.stack_config_json)
        except Exception as ValidationError:
            self.logger.error("Unable to Validate Template for {}.".format(self.lname))
            self.logger.debug("Error on Validation: {}".format(ValidationError))
            self.return_status["stack_valid"] = "Invalid"
            self.return_status["fail"] = True
            self.go = False
        else:

            if self.valiedate_capabilities() is False:
                self.return_status["stack_valid"] = "Invalid (Capabilities)"
                self.return_status["fail"] = "yes"
                self.go = False
            else:

                self.return_status["stack_valid"] = "Valid"

    def stack_exists(self):

        """
        See if Stack Is pre-existing
        :return:
        """

        # See if Exists
        self.logger.info("{} : Checking if Stack Exists".format(self.lname))

        try:
            this_stack_info = self.cf_client.describe_stacks(StackName=self.stack_name)
            cstype = "UPDATE"
        except Exception:
            self.logger.info("{} not does not yet exit, requesting create.".format(self.lname))
            if self.delete is True:
                cstype = "DELETED"
            cstype = "CREATE"
        else:
            if this_stack_info["Stacks"][0]["StackStatus"] == "REVIEW_IN_PROGRESS":
                cstype = "CREATE"
        finally:
            if self.delete is True and cstype in ("UPDATE", "CREATE"):
                cstype = "DELETE"

            self.logger.info("{} exists, requesting {}.".format(self.lname, cstype))

        return cstype

    def wait_for_complete(self, csId):

        """
        Wait for Complete
        :return:
        """

        max_time = int(time.time()) + self.timeout
        complete = "timeout"

        self.logger.info("Waiting for ChangeSet: {}".format(csId))

        while int(time.time()) < max_time:

            current_status = self.cf_client.describe_change_set(ChangeSetName=csId)["Status"]

            self.logger.debug("Current Changeset : {}".format(current_status))

            if current_status in ("CREATE_PENDING", "CREATE_IN_PROGRESS"):
                complete = "in_progress"

            elif current_status in ("CREATE_COMPLETE", "FAILED"):
                complete = "yes"
                break

            elif current_status in ("DELETE_COMPLETE"):
                complete = "error"
                break

            else:
                raise TypeError("Unknown Status {}".format(current_status))

            time.sleep(2)

        return complete

    def process_changeset(self):

        """
        Process Changeset

        :return:
        """

        cstype = self.stack_exists()

        # General Args
        general_args = {"StackName": self.stack_name,
                        "TemplateBody": self.stack_config_json,
                        "Parameters": self.stack_cfg.get("parameters", list()),
                        "Capabilities": self.stack_cfg.get("capabilities", list()),
                        "Tags": self.stack_cfg.get("tags", list()),
                        "Description": self.stack_cfg.get("description", "No Description Given")
                        }

        self.logger.debug("{} general_args: {}".format(self.lname, general_args))

        changeset_name = datetime.datetime.today().strftime(
            "{}-{}-%Y-%m-%d-%s".format(self.stack_name, self.aws_profile))

        self.logger.info("{} Creating Changeset {}".format(self.lname, changeset_name))

        if self.delete is False:
            # Make Changeset to Calculate Changes

            changeset_ident = self.cf_client.create_change_set(ChangeSetName=changeset_name,
                                                               ChangeSetType=cstype,
                                                               **general_args)

            # Wait until Available
            cs_complete = self.wait_for_complete(changeset_ident["Id"])
            if cs_complete != "yes":
                self.logger.error("Unable to create a changeset {}".format(cs_complete))
                self.return_status["changes"] = "Error Creating ChangeSet"
                self.return_status["fail"] = True
                self.go = False
                return

            changeset_info = self.cf_client.describe_change_set(ChangeSetName=changeset_ident["Id"])

            pending_change = len(changeset_info["Changes"])
            if cstype == "CREATE":
                pending_change += 1

            self.logger.debug("{} changes are outstanding.".format(pending_change))

            self.return_status["changes"] = "{} Changes".format(pending_change)
        else:
            # Delete Reequested
            pending_change = 1
            self.return_status["changes"] = "1 Delete"
            if cstype == "DELETED":
                pending_change = 0
                self.return_status["changes"] = "None (Del)"

        if self.confirm is True and pending_change > 0 and self.delete is False:
            # Do Change

            cs_complete = self.wait_for_complete(changeset_ident["Id"])
            if cs_complete != "yes":
                self.logger.error("Unable to create a changeset {}".format(cs_complete))
                self.return_status["changes"] = "Error Creating ChangeSet"
                self.return_status["fail"] = True
                self.go = False
                return

            self.logger.info("{} : Executing {} Changes".format(self.lname, pending_change))
            self.cf_client.execute_change_set(ChangeSetName=changeset_ident["Id"])

            max_utime = int(time.time()) + (self.timeout * 2)

            self.return_status["action"] = "Timed Out On Update"

            while int(time.time()) < max_utime:
                changeset_info = self.cf_client.describe_change_set(ChangeSetName=changeset_ident["Id"])

                execution_status = changeset_info["ExecutionStatus"]
                if execution_status == "EXECUTE_COMPLETE":
                    self.logger.info("{} : {} Changes Successfull".format(self.lname, pending_change))
                    self.return_status["action"] = "UPDATE SUCCESS"
                    break

                if execution_status in ("EXECUTE_FAILED", "OBSOLETE", "UNAVAILABLE"):
                    self.logger.error("{} Error when Doing update {}".format(self.lname, execution_status))
                    self.return_status["action"] = "UPDATED FAILED ({})".format(execution_status)
                    self.return_status["fail"] = True
                    break

                time.sleep(5)

        elif pending_change > 0 and self.delete is True:

            if self.confirm is True:
                self.logger.info("{} : Attempting Delete".format(self.lname))

                try:
                    self.cf_client.delete_stack(StackName=general_args["StackName"])
                except Exception as delete_error:
                    self.logger.error("Unable to Delete Stack with Error : {}".format(delete_error))
                    self.return_status["action"] = "Delete Failure"

                else:
                    self.return_status["action"] = "Deleted"

            else:
                self.logger.info("{} : Would have attempted a Delete, but Confirm not On".format(self.lname))
                self.return_status["action"] = "CONFIRM OFF (DEL)"

        elif pending_change > 0 and self.confirm is False:
            self.logger.info("{} : Stack Has {} changes but Confirm not on.".format(self.lname, pending_change))
            self.return_status["action"] = "CONFIRM OFF"

        elif pending_change == 0:
            # No Changes
            self.logger.info("{} : Stack Unchanged.".format(self.lname))
            self.return_status["action"] = "No Pending Changes"

        return
