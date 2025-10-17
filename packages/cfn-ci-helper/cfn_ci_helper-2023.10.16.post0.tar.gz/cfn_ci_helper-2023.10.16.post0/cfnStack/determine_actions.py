#!/usr/bin/env python3

import logging
import os.path
import importlib.resources

import yaml
import jinja2
import boto3

import cfnStack

class ActionParser:

    _default_region = "us-east-1"

    def __init__(self,
                 only_profiles: list[str] = [],
                 stackname: list[str] = [],
                 confirm: bool = False,
                 category: str|None=None,
                 config: str|None=None,
                 stack: str|None=None,
                 description: str = "No Description Given",
                 regions: list[str] = [],
                 capabilities: list[str] = [],
                 dynamic_tags: list[str|dict] = [],
                 parameters: list[str|dict] = [],
                 profiles: list[str] = [],
                 delete: bool = False,
                 **kwargs):

        self.logger = logging.getLogger(__name__)

        self.stackname = stackname

        self.kwargs = kwargs
        self.errors = dict()
        self.delete = delete
        self.description = description
        self.capabilities = capabilities
        self.regions = regions
        self.parameters = parameters
        self.only_profiles = only_profiles
        self.profiles = profiles
        self.dynamic_tags = dynamic_tags
        self.live_add = self.parse_params()
        self.category_dir = category
        self.all_category_configs = self.determine_category_configs(category, config, stack)

        self.wanted_stacks = self.filter_wanted_stacks()

        self.action_stacks = self.filter_actions()


    def parse_params(self):

        live_add = dict(parameters={})

        for param in self.parameters:
            if isinstance(param, str):
                param_key, param_val = param.split(":", 1)
                live_add["parameters"][param_key] = param_val
            elif isinstance(param, dict):
                live_add["parameters"][param["Key"]] = param["Value"]

        return live_add



    def determine_category_configs(self, category, config, stack) -> dict:

        category_configs: dict = dict()

        if category is not None:
            if os.path.isdir(category) is False:
                self.logger.error("Unable to Find Cateogry Directory : {}".format(category))
                self.errors["category"] = "Unable to Find Cateogry Directory : {}".format(category)
            else:
                self.logger.debug("Working in Category: {}".format(category))
                config_file = os.path.join(category, "config.yaml")

            with open(config_file) as config_fobj:
                category_configs = yaml.safe_load(config_fobj)

        elif config is not None:
            if os.path.isfile(config) is False:
                self.logger.error("Unable to Find Configuration File : {}".format(config))
                self.errors["config"] = "Unable to Find Configuration File : {}".format(config)
            else:
                self.logger.debug("Categories not in Use in a direct yaml config : {}.".format(config))
                config_file = config
            with open(config_file) as config_fobj:
                category_configs = yaml.safe_load(config_fobj)

        elif stack is not None:
            if os.path.isfile(stack) is False:
                self.logger.error("Cannot Find Direct Stack Configuration : {}".format(stack))
                self.errors["stack"] = "Cannot Find Direct Stack Configuration : {}".format(stack)
            else:
                self.logger.debug("Using default configuration for direct stack.")

                render_data = dict(filename=stack,
                                   description=self.description,
                                   capabilities=self.capabilities,
                                   parameters=
                                    ["{}:{}".format(k, v) for k, v in self.live_add["parameters"].items()],
                                   tags=self.dynamic_tags)

                if len(self.profiles) == 0:
                    render_data["profiles"] = ["default"]
                else:
                    render_data["profiles"] = self.profiles

                if len(self.regions) == 0:
                    render_data["regions"] = [self._default_region]
                else:
                    render_data["regions"] = self.regions

                with importlib.resources.path(cfnStack, "default_stack.yaml.jinja") as stack_template_path:
                    with open(stack_template_path, "r") as stack_template_fobj:
                        stack_template_str = stack_template_fobj.read()

                        config_template = jinja2.Environment(loader=jinja2.BaseLoader,
                                                             autoescape=jinja2.select_autoescape(
                                                                 enabled_extensions=('html', 'xml'),
                                                                 default_for_string=False
                                                             )).from_string(stack_template_str)

                        config_rendered = config_template.render(**render_data)

                        self.logger.debug(render_data)
                        self.logger.debug("Live Rendered: {}".format(config_rendered))

                        category_configs = yaml.safe_load(config_rendered)

                        self.logger.debug("configs: {}".format(category_configs))

        return category_configs

    def filter_wanted_stacks(self):

        if len(self.stackname) == 0:
            # All Stacks
            wanted_stacks = list(self.all_category_configs.keys())
        else:

            wanted_stacks = [stack for stack in self.stackname if stack in self.all_category_configs.keys()]

            missing_stacks = [mstack for mstack in self.stackname if mstack not in self.category_configs.keys()]

            if len(missing_stacks) > 0:
                self.logger.error(
                    "Requested Stack(s) {} not requested configured in category {}".format(",".join(missing_stacks),
                                                                                           self.category))

                self.errors["stacks"] = "Missing Stack(s): {}".format(" , ".join(missing_stacks))

        return wanted_stacks


    def filter_actions(self) -> list[dict]:

        action_tuples = list()

        for wstack in self.wanted_stacks:

            this_config = self.all_category_configs[wstack]

            if self.category_dir is not None:
                # Front with Path
                this_config_file = os.path.join(self.category_dir, this_config["file"])
            else:
                # Assume Path to File Given
                this_config_file = os.path.join(this_config["file"])

            with open(this_config_file, "r") as stack_config_file_obj:
                stack_config_json = stack_config_file_obj.read()

            if len(self.only_profiles) == 0:

                wprofiles = self.all_category_configs[wstack]["profiles"]
            else:

                wprofiles = [prof for prof in self.only_profiles if prof in self.all_category_configs[wstack]["profiles"]]

                mprofiles = [prof for prof in self.only_profiles if prof not in self.all_category_configs[wstack]["profiles"]]

                if len(mprofiles) > 0:
                    self.logger.error("{} missing requested profiles {}.".format(wstack, ",".join(mprofiles)))
                    self.errors["mprofile"] = "{} missing requested profiles {}.".format(wstack, ",".join(mprofiles))

            wregions = this_config.get("regions", [self._default_region])

            if isinstance(wregions, str) and wregions.startswith("all"):
                wregions = [wregions]

            for wprofile in wprofiles:

                self.logger.info("Profiles {}".format(wprofiles))
                self.logger.info("This Profiles {}".format(wprofile))

                this_wregions = wregions

                if len(wregions) == 1 and wregions[0].startswith("all"):
                    # Get and Wrap All Regions
                    fast_service_name="cloudformation"

                    if ":" in wregions[0]:
                        fast_service_name = wregions[0].split(":")[1]

                    self.logger.warning("Deployment requested to all regions for service: {}".format(fast_service_name))
                    fast_session_args = dict()

                    if wprofile != "default":
                        fast_session_args["profile_name"] = wprofile

                    fast_session = boto3.session.Session(**fast_session_args)
                    this_wregions = fast_session.get_available_regions(service_name=fast_service_name)
                    self.logger.info("Expanding to {} regions for profile {}".format(len(this_wregions), wprofile))
                    self.logger.debug("Wanted Regions for Profile {}, {}".format(wprofile, ", ".join(this_wregions)))

                for wregion in this_wregions:

                    action_tuples.append({
                        "stack": wstack,
                        "stack_cfg": this_config,
                        "region": wregion,
                        "profile": wprofile,
                        "stack_config_json": stack_config_json,
                        "delete": self.delete
                    })

        return action_tuples



