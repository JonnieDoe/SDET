#!/usr/bin/python -tt
# -*- coding: utf-8 -*-


r"""
Program:
    sdet.exe

Usage:
    sdet.exe   (--product_name=<X>)
               (--test_suites_dir=<path_to_dir>)
               (--report_type=<1/2/3>)
               [--path_to_output_dir=<path_to_dir>]
               [--debug=<false/true>]
               [--verbose]

    sdet.exe (-h | --help)
    sdet.exe --version

Options:
    --product_name=<X>                         Name of the product.
                                                        (default: None)
                                                        (e.g.: X/Y etc)
    --test_suites_dir=<path_to_dir>            Name of the platform.
                                                        (default: None)
    --report_type=<1/2/3>                      Type of report.
    --path_to_output_dir=<path_to_dir>         Relative path to 'path_to_output_dir' directory.
                                                        (default: .\output)
    --debug=<false/true>                       Debug the code or not.
                                                        (default: False)

    --verbose                                  Get verbose about output.
    --version                                  Print the version.

    -h, --help                                 Show this message.

Example:
    sdt.exe --product_name="X" --test_suites_dir="TS" --verbose

OBS:
    - Relative path: The path to directory relative to program`s current location
                     If program is located in:
                                'C:\\sdt'
                     Then all options must consider their path starting from here.

    - All options are optional, except '--product_name', '--test_suite_dir' and '--report_type'.
      If no options are given then the program tries to use the default values.
"""

__author__ = "DC"
__mail__ = "david.cristian.paraschivescu@gmail.com"
__title__ = __tool__ = "SDT Report Tool"
__version__ = "0.1"
__copyright__ = "2019. All right reserved"


import datetime
import os
import re
import shutil
import sys

from collections import defaultdict, OrderedDict
from glob import glob
from json import dumps, loads
from traceback import format_exc
from typing import Union
# User defined modules
from const import (
    OUTPUT_DIR_NAME, TEMPLATES_DIR_NAME, TEST_SCENARIO_DIR, TEST_SCENARIO_TEMPLATE, SDET_TEMPLATE_NAME, SECTION_CONTENT
)
from helper import Colors
from jinja_utils import PrintOnConsole, RaiseExtension, SilentUndefined

try:
    import htmlmin
    from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound, TemplateSyntaxError
    from jinja2.ext import do, loopcontrols
    from docopt import docopt
except Exception as error:
    print("\n\tError! Could not import some library: {err}".format(err=error))
    print("\nExiting! ...")
    sys.exit(1)


CONFIG = defaultdict(OrderedDict)
LINE_SEP = os.linesep


####################################################################################################
class GenerateHTMLUtils(object):
    """HTML utils class."""

    def __init__(self, product: str = None, output_dir: str = None, template_env=None) -> None:
        """GenerateHTMLUtils class constructor.
        :param template_env: template Environment used by Jinja2
        :param product: Product name [str]
        :param output_dir: Tests data dict [str]
        """

        if not template_env:
            raise ValueError("No Template Environment supplied!")

        self.__product = product
        self.__output_dir = output_dir

        self.__template_environment = template_env
        self.__template_environment.globals.update(zip=zip)
        self.__template_environment.filters['debug'] = PrintOnConsole.debug

    @property
    def output_dir(self) -> str:
        """Get the path to the output dir."""
        return self.__output_dir

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        """Set the output dir path.
        :param value: Value of the path [str]
        """
        self.__output_dir = value

    @property
    def product(self) -> str:
        """Get the product name."""
        return self.__product

    @property
    def template_environment(self):
        """Get the template env."""
        return self.__template_environment

    ################################################################################################
    def render_template(self, template_filename=None, context: dict = None):
        """Render the template.
        :param template_filename: Template file to use in rendering
        :param context: Input for Jinja2 to replace in template file [dict]
        :return: Rendered template
                 False, on errors
                 None, no correct input
        """

        if not self.template_environment or not template_filename or not context:
            return

        try:
            render = self.template_environment.get_template(template_filename).render(context)
        except TemplateNotFound:
            print(
                'Error loading "{0}": not found'.format(
                    self.template_environment.get_or_select_template(template_filename))
            )
            return False
        except TemplateSyntaxError as e:
            print(
                'Error loading "{0}": {1}, line {2}'.format(
                    self.template_environment.get_or_select_template(template_filename), e, e.lineno)
            )
            return False
        except IOError as e:
            print(
                'Error loading "{0}": {1}'.format(self.template_environment.get_or_select_template(template_filename),
                                                  e.strerror)
            )
            return False
        except:
            # Custom error handling
            print(
                "\tUnknown error when trying to render template '{template}'"
                "\n\n{err}\n"
                "\n\tPlease check the context that JINJA2 has to render!"
                "\n\tContext: {context}".format(
                    template=self.template_environment.get_or_select_template(template_filename),
                    err=format_exc(), context=dumps(context, indent=8))
            )
            return False

        return render

    ################################################################################################
    def create_html_report(self,
                           html_template: str = None, html_page_name: str = None, context_to_render: dict = None
                           ) -> Union[None, bool]:
        """Create the HTML page.
        :param html_template: HTML5 template file to be used for rendering [str]
        :param html_page_name: The name of the HTML page [str]
        :param context_to_render: Values to render in order to produce the HTML page [dict]
        :return: True, on success
                 False, on Failure
                 None, wrong input
        """

        if not context_to_render:
            print("No context to render supplied!")
            return

        try:
            rendered_html = self.render_template(template_filename=html_template, context=context_to_render)

            if not rendered_html:
                print("\nError when rendering the template: method returned '{0}'!".format(rendered_html))
                return False

            try:
                rendered_html.encode('utf-8')
            except AttributeError:
                print("\nError when encoding the template with 'utf-8'! Going on without encoding in 'utf-8'")
            except Exception as exc_err:
                print(
                    "\nUnknown error when encoding the template with 'utf-8'!"
                    "\nError: {0}"
                    "\nGoing on without encoding in 'utf-8'".format(exc_err)
                )
        except Exception as except_err:
            print("\nError when rendering the template: '{0}'".format(except_err))
            return False

        html_page = os.path.join(self.output_dir, html_page_name)
        with open(html_page, 'w') as file_handle:
            file_handle.write(str(rendered_html))

        return True

    ################################################################################################
    def generate_html(
            self, html_page_name: str = None, html_template: str = None, input_data_dkt: dict = None, report_type=1,
            debug: bool = False) -> Union[None, bool]:
        """Generate HTML5 file.
        :param html_page_name: HTML5 output page name [str]
        :param html_template: HTML5 template file to be used for rendering [str]
        :param input_data_dkt: Dict to render in HTML context [dict]
        :param report_type: Type of the report (e.g: <1/2/3>) [int/str]
        :param debug: Print Jinja2 debug info [bool]
        :return: True, if could generate HTML5 page
                 False, on error
                 None, wrong input
        """

        if not html_template:
            print("No HTML Template supplied!")
            return

        if not html_page_name:
            print("No HTML page name supplied!")
            return

        if not input_data_dkt:
            print("No input data to render supplied!")
            return

        # Get date
        report_date = datetime.date.today()
        current_year = datetime.datetime.now().year

        page_title = SECTION_CONTENT.get('html_page_title')
        summary_info_table_header_title = SECTION_CONTENT.get('summary_info_table_header_title')

        summary_info_table_header_title = summary_info_table_header_title
        if report_type == 2:
            summary_info_table_header_title = "{0} Summary Test Report".format(input_data_dkt.get('test_name', ""))
        if report_type == 3:
            # TODO: add page name for this report
            pass

        to_render = {
            'page_title': page_title,
            'summary_info_table_header_title': summary_info_table_header_title,
            'report_date': str(report_date),
            'copyright': (
                'Copyright {year} PDC. '
                'Presence of a copyright notice is not an acknowledgement of publication.'.format(year=current_year)
            ),
            'tool': __tool__.upper(),
            'tool_version': __version__
        }

        if report_type == 1:
            to_render.update(
                {
                    'all_platforms_id': ", ".join(input_data_dkt.get('all_platforms_id', [])),
                    'tests': input_data_dkt
                }
            )

        if report_type == 2:
            to_render.update(
                {
                    'test': input_data_dkt.get('platform_status'),
                    'test_name': input_data_dkt.get('test_name'),
                    'platform_id': input_data_dkt.get('platform_id')
                }
            )

        if debug:
            # ------------------------------- START of context validation ------------------------------- #
            print("\n{ch}\nValidate the rendering context before sending to JINJA!".format(ch="%" * 80))

            abort_rendering = False
            for key, value in to_render.items():
                if value is None:
                    print(
                        "\tThe value of '{key}' key in 'to_render' dict is a <NoneType> value! Most likely, there are "
                        "some missing items".format(key=key)
                    )
                    abort_rendering = True

            print(
                "\nValidating the context finished with status: '{state}'!\n{ch}\n".format(
                    state="OK" if not abort_rendering else "FAILED",
                    ch="%" * 80)
            )

            if abort_rendering:
                print("\nAbort the process of rendering the template!\n")
                return False

            print("\nAll good in the hood: Start the rendering process!")
            # ------------------------------- END of context validation -------------------------------- #

        context_to_render = {
            'to_render': to_render
        }

        create_html_page_status = self.create_html_report(html_template=html_template, html_page_name=html_page_name,
                                                          context_to_render=context_to_render)
        if not create_html_page_status:
            return False

        return True


####################################################################################################
def banner() -> None:
    """Banner to print."""

    title = __title__
    version = __version__
    contact = __mail__

    print("-" * 120)
    print("{title}{line_sep}".format(title=title.center(120), line_sep=os.linesep))
    print(("version: {version}".format(version=version)).center(120))
    print(("contact: {contact}".format(contact=contact)).center(120))
    print("-" * 120)


####################################################################################################
def check_path(path: str = None) -> Union[None, bool]:
    """Check if the tool can chdir to script base directory.
    :param path: Full path to script base directory [str]
    :return: True, on success
             False, on failure
             None, if wrong input
    """

    if not path:
        return

    try:
        os.chdir(path)
    except Exception as err:
        print("Error when changing dir to: '{dir}'{line_sep}{err}".format(dir=path, line_sep=LINE_SEP, err=err))
        return False

    return True


####################################################################################################
def set_input_variables(product_name: str = None, test_suites_dir: str = None, report_type: str = None,
                        path_to_output_dir: str = None, verbose: dict = None) -> None:
    """Parse user input and overwrite defaults.
    :param product_name: Name of the product [str]
    :param test_suites_dir: Path to the TS dir [str]
    :param report_type: Type of the report [str]
    :param path_to_output_dir: Relative path to 'output' directory [str]
    :param verbose: Print verbose [dict]
    :return: None
    """

    verbose_ok = False

    # Print verbose
    if verbose.get('mode'):
        verbose_ok = True

        print(
            "{line_sep}{ch_format}{line_sep}Options as provided by the user{line_sep}".format(line_sep=LINE_SEP,
                                                                                              ch_format=("*" * 80))
        )
        print(dumps(verbose.get('args'), indent=4))
        print("{line_sep}{ch_format}{line_sep}".format(line_sep=LINE_SEP, ch_format=("*" * 80)))

    if not product_name or not bool(product_name.strip()):
        print("{line_sep}No product name supplied or arg is empty{line_sep}".format(line_sep=LINE_SEP))
        sys.exit(1)

    global CONFIG
    CONFIG['product_name'] = product_name

    # Current directory with absolute full PATH to current script
    path = os.path.dirname(os.path.realpath(__file__))

    # Assure that current directory is where the script is located
    if check_path(path=path) is not True:
        print("Exiting! ...")
        sys.exit(1)

    CONFIG['path'] = path

    # Get output directory name
    CONFIG['output_dir'] = os.path.normpath(os.path.join(path, OUTPUT_DIR_NAME))

    # Get output directory full PATH
    if path_to_output_dir:
        try:
            os.chdir(os.path.join(path, path_to_output_dir))
        except Exception as err:
            print(
                "Error when trying to change directory to: '{path_to_output_dir}'{line_sep}{err}{line_sep}".format(
                    path_to_output_dir=path_to_output_dir, line_sep=LINE_SEP, err=err)
            )
            print("Exiting! ...")
            sys.exit(1)

        CONFIG['output_dir'] = os.getcwd()

    # Get TS directory full PATH
    if not test_suites_dir:
        print("No TS dir supplied!{line_sep}Exiting! ...".format(line_sep=LINE_SEP))
        sys.exit(1)

    try:
        os.chdir(os.path.join(path, test_suites_dir))
    except Exception as err:
        print(
            "Error when trying to change directory to: '{test_suites_dir}'{line_sep}{err}{line_sep}".format(
                test_suites_dir=test_suites_dir, line_sep=LINE_SEP, err=err)
        )
        print("Exiting! ...")
        sys.exit(1)

    CONFIG['test_suites_dir'] = os.getcwd()

    if not report_type:
        print("No report type supplied!{line_sep}Exiting! ...".format(line_sep=LINE_SEP))
        sys.exit(1)

    CONFIG['report_type'] = report_type

    if verbose_ok:
        print(
            "{line_sep}{ch_format}{line_sep}Options after parsing{line_sep}".format(line_sep=LINE_SEP,
                                                                                    ch_format=("*" * 80))
        )
        print("\tProduct Name\n\t\t{0}".format(CONFIG['product_name']))
        print("\tReport Type\n\t\t{0}".format(CONFIG['report_type']))
        print("\tTest_Suites_dir\n\t\t{0}".format(CONFIG['test_suites_dir']))
        print("\tOutput_dir\n\t\t{0}".format(CONFIG['output_dir']))
        print("{line_sep}{ch_format}{line_sep}".format(line_sep=LINE_SEP, ch_format=("*" * 80)))


####################################################################################################
def json_to_dict(json_file: str = None) -> Union[None, bool, dict]:
    """Transform a JSON file into a dictionary.
    :param json_file: Full path to the JSON file [string]
    :return: None, no input file
             False, on error/ JSON file is empty
             Dict, if could load the JSON file content
    """

    if not json_file:
        return

    if not os.path.isfile(json_file):
        return False

    try:
        with open(json_file) as fd_in:
            json_data = loads(fd_in.read())
    except ValueError as exc_error:  # includes JSONDecodeError
        print(
            "Error whe trying to load JSON file: '{file}'{line_sep}{err}".format(file=json_file, line_sep=LINE_SEP,
                                                                                 err=exc_error)
        )
        return False
    except Exception as except_err:
        print(
            "Base exception error whe trying to load JSON file: '{file}'{line_sep}{err}".format(file=json_file,
                                                                                                line_sep=LINE_SEP,
                                                                                                err=except_err)
        )
        return False

    if not json_data:
        print("{line_sep}JSON file is empty: '{file}'{line_sep}".format(file=json_file, line_sep=LINE_SEP))
        return False

    return json_data


####################################################################################################
def aggregate_all_data(main_dkt: dict = None, tests_dkt: dict = None) -> Union[None, dict]:
    """Compound the main dictionary holding all data from all JSONs.
    :param main_dkt: Main dictionary to be updated [dict]
    :param tests_dkt: All platform tests [dict]
    :return: None, no valid input
             Modified dict, on success
    """

    if not tests_dkt:
        return

    for test in tests_dkt:
        test_name = os.path.basename(test.get('sr_test_name', ""))
        platform_id = test.get("sr_ts_id")
        status = 'OK' if test.get("sr_tests_failed", 0) == 0 else "FAILED"

        test.update({'status': status})

        if test_name in main_dkt:
            if status == "FAILED" and main_dkt[test_name]['status'] != "FAILED":
                main_dkt[test_name]['status'] = "FAILED"

            main_dkt[test_name]['platforms_id'].update(
                {
                    platform_id: test
                }
            )
        else:
            main_dkt[test_name] = {
                'name': test_name,
                'status': status,
                'platforms_id': {
                    platform_id: test
                }
            }

    return main_dkt


####################################################################################################
def requirement_1(platforms_dkt_data: dict = None, tests_status_dkt: dict = None) -> None:
    """Requirement 1.
    :param platforms_dkt_data: All formatted data read from JSON files [dict]
    :param tests_status_dkt: All tests status dict [dict]
    """

    if not platforms_dkt_data:
        return

    for test_name, test_values in platforms_dkt_data.items():
        platform_info = defaultdict(OrderedDict)
        for platform_id, platform_data in test_values.get('platforms_id').items():
            platform_info['status'].update({platform_id: platform_data.get('status')})

        test_info = {
            'status': test_values.get('status'),
            'platforms_id': platform_info
        }

        if test_values.get('status') == "FAILED":
            if not tests_status_dkt['failed'].get(test_name):
                tests_status_dkt['failed'].update({test_name: test_info})
            else:
                tests_status_dkt['failed'][test_name] = test_info
        else:
            if not tests_status_dkt['successful'].get(test_name):
                tests_status_dkt['successful'].update({test_name: test_info})
            else:
                tests_status_dkt['successful'][test_name] = test_info


####################################################################################################
def requirement_2(platforms_dkt_data: dict = None, tests_detailed_info_dkt: dict = None) -> Union[None, bool]:
    """Requirement 2.
    :param platforms_dkt_data: All formatted data read from JSON files [dict]
    :param tests_detailed_info_dkt: All tests status dict [dict]
    :return:
    """

    if not platforms_dkt_data:
        return

    for test_status in tests_detailed_info_dkt:
        if test_status not in ['failed', 'successful']:
            continue

        for test_name, test_values in tests_detailed_info_dkt.get(test_status, {}).items():
            platforms_ids = test_values.get('platforms_id', {}).get('status')

            for platform_id in platforms_ids:
                sr_tap = \
                    platforms_dkt_data.get(test_name, {}).get('platforms_id', {}).get(platform_id, {}).get('sr_tap')

                total_tests = int(
                    platforms_dkt_data.get(
                        test_name, {}).get('platforms_id', {}).get(platform_id, {}).get('sr_test_cases', 0)
                )
                failed_tests = int(
                    platforms_dkt_data.get(
                        test_name, {}).get('platforms_id', {}).get(platform_id, {}).get('sr_tests_failed', 0)
                )
                passed_tests = total_tests - failed_tests

                # Split by new-line
                all_scenarios = defaultdict(list)
                for test_scenario in sr_tap.split('\n'):
                    # Check for OK tests
                    if re.search(r'ok [0-9]+ -\s', test_scenario):
                        all_scenarios['ok'].append(test_scenario)

                    # Check for NOT OK tests
                    if re.search(r'not ok [0-9]+ -\s', test_scenario):
                        all_scenarios['not_ok'].append(test_scenario)

                    # Check for NOT OK tests
                    if re.search(r'# SKIP\s', test_scenario):
                        all_scenarios['skipped'].append(test_scenario)

                if 'platforms_run_status' not in tests_detailed_info_dkt[test_status][test_name]:
                    tests_detailed_info_dkt[test_status][test_name].update(
                        {
                            'platforms_run_status': {
                                platform_id: {
                                    'scenarios': all_scenarios,
                                    'total_tests': total_tests,
                                    'passed_tests': passed_tests,
                                    'failed_tests': failed_tests
                                }
                            }
                        }
                    )
                else:
                    tests_detailed_info_dkt[test_status][test_name]['platforms_run_status'].update(
                        {
                            platform_id: {
                                'scenarios': all_scenarios,
                                'total_tests': total_tests,
                                'passed_tests': passed_tests,
                                'failed_tests': failed_tests
                            }
                        }
                    )

    return True


####################################################################################################
def main(docopt_args=None) -> None:
    """The main function.
    :param docopt_args: Arguments from 'docopt'
    """

    global CONFIG

    # Show banner()
    banner()

    # Parse user input
    product_name = None
    test_suites_dir = None
    report_type = None
    path_to_output_dir = None
    debug = False
    verbose = {'mode': None}

    if '--product_name' in docopt_args and docopt_args['--product_name']:
        product_name = docopt_args['--product_name']

    if '--test_suites_dir' in docopt_args and docopt_args['--test_suites_dir']:
        test_suites_dir = docopt_args['--test_suites_dir']

    if '--report_type' in docopt_args and docopt_args['--report_type']:
        report_type = int(docopt_args['--report_type'])

    if '--path_to_output_dir' in docopt_args and docopt_args['--path_to_output_dir']:
        path_to_output_dir = docopt_args['--path_to_output_dir']

    if '--debug' in docopt_args and docopt_args['--debug']:
        debug = docopt_args['--debug']

    if '--verbose' in docopt_args and docopt_args['--verbose']:
        verbose = {
            'mode': True,
            'args': arguments
        }

    # Overwrite default values with user input
    set_input_variables(product_name=product_name,
                        test_suites_dir=test_suites_dir,
                        report_type=report_type,
                        path_to_output_dir=path_to_output_dir,
                        verbose=verbose)

    # Get path to JSON files
    json_files_path = os.path.join(CONFIG['test_suites_dir'], "*.json")
    # Get all JSON files
    json_files = glob(json_files_path)
    if len(json_files) == 0:
        print("No JSON files to parse in directory: '{dir}'".format(dir=CONFIG['test_suites_dir']))
        sys.exit(1)

    all_platforms_id = list()
    platforms_dkt_data = OrderedDict()

    # Parse all JSON files
    for json_file in json_files:
        path_base_name = os.path.basename(json_file)

        # Remove extension from file name
        platform_id, _ = os.path.splitext(path_base_name)

        # Get all parsed platform IDs
        all_platforms_id.append(platform_id)

        # Get data from JSON file
        platform_tests_data = json_to_dict(json_file=json_file)
        if not platform_tests_data:
            print("Could not transform JSON file to dict!")
            sys.exit(1)

        # Aggregate read data into main dictionary
        form_main_dkt = aggregate_all_data(tests_dkt=platform_tests_data.get('data', []), main_dkt=platforms_dkt_data)
        if not form_main_dkt:
            print(
                "{line_sep}Could not format main dictionary.{line_sep}Exiting! ...".format(
                    line_sep=LINE_SEP)
            )
            sys.exit(1)

    # ------------------------------------------- Task 1 ------------------------------------------------------------- #
    tests_status_dkt = defaultdict(dict)

    requirement_1(platforms_dkt_data=platforms_dkt_data, tests_status_dkt=tests_status_dkt)
    if not tests_status_dkt:
        print("{line_sep}Could not get status data.{line_sep}Exiting! ...".format(line_sep=LINE_SEP))
        sys.exit(1)

    # Using OrderedDict() + sorted() sort dictionary by key
    # Alphabetically sort 'failed' tests
    tmp_dict = OrderedDict()
    for key in sorted(tests_status_dkt.get('failed', {})):
        tmp_dict.update(
            {key: tests_status_dkt.get('failed', {}).get(key)}
        )
    tests_status_dkt['failed'] = tmp_dict

    # Alphabetically sort 'successful' tests
    tmp_dict = OrderedDict()
    for key in sorted(tests_status_dkt.get('successful', {})):
        tmp_dict.update(
            {key: tests_status_dkt.get('successful', {}).get(key)}
        )
    tests_status_dkt['successful'] = tmp_dict

    tests_status_dkt['all_platforms_id'] = all_platforms_id

    generate_html = GenerateHTMLUtils(
        template_env=Environment(autoescape=select_autoescape(['html']),
                                 loader=FileSystemLoader(os.path.join(CONFIG['path'], TEMPLATES_DIR_NAME)),
                                 extensions=[do, loopcontrols, RaiseExtension],
                                 undefined=SilentUndefined,
                                 trim_blocks=False),
        product=product_name,
        output_dir=CONFIG['output_dir']
    )

    # - Generate HTML5 page
    status = generate_html.generate_html(html_page_name="SDET_SummaryTestReport.html",
                                         html_template=SDET_TEMPLATE_NAME,
                                         input_data_dkt=tests_status_dkt,
                                         report_type=1,
                                         debug=True)
    if status:
        print(
            Colors.BOLD + Colors.OKBLUE + "\tSuccessfully generated HTML file!" + Colors.ENDC +
            Colors.WARNING + "\n\t\tPlease check output directory: '{dir}'".format(dir=CONFIG['output_dir']) +
            Colors.ENDC
        )
    else:
        print(Colors.BOLD + Colors.FAIL + "\tNo HTML file generated!" + Colors.ENDC)
        print("\nExiting! ...")
        sys.exit(1)

    # ------------------------------------------- Task 2 ------------------------------------------------------------- #
    if report_type in [2, 3]:
        req_2 = requirement_2(platforms_dkt_data=platforms_dkt_data, tests_detailed_info_dkt=tests_status_dkt)
        if not req_2:
            print(
                "{line_sep}Could not get detailed status data about tests.{line_sep}Exiting! ...".format(
                    line_sep=LINE_SEP)
            )
            sys.exit(1)

        # Create the directory if it does not exist
        tests_scenario_data_dir = os.path.join(CONFIG['output_dir'], TEST_SCENARIO_DIR)
        if not os.path.isdir(tests_scenario_data_dir):
            os.makedirs(tests_scenario_data_dir)

        # Delete dir content data (from previous runs). Do not delete root dir
        for path in os.listdir(tests_scenario_data_dir):
            path = os.path.join(tests_scenario_data_dir, path)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except Exception as exc:
                print(exc)

        # Set new output path
        generate_html.output_dir = tests_scenario_data_dir

        for test_status in tests_status_dkt:
            if test_status not in ['failed', 'successful']:
                continue

            for test_name, test_values in tests_status_dkt.get(test_status, {}).items():
                platforms_status_data = test_values.get('platforms_run_status', {})

                for platform_id, platform_status_data in platforms_status_data.items():
                    # - Generate HTML5 page
                    status = generate_html.generate_html(
                        html_page_name="{f_name}_{platform_id}.html".format(f_name=test_name.lower(),
                                                                            platform_id=platform_id),
                        html_template=TEST_SCENARIO_TEMPLATE,
                        input_data_dkt={
                            'test_name': test_name,
                            'platform_id': platform_id,
                            'platform_status': platform_status_data
                        },
                        report_type=2
                    )
                    if not status:
                        print(
                            Colors.BOLD + Colors.FAIL +
                            "\tNo HTML file generated for test '{t_n}'!".format(t_n=test_name) + Colors.ENDC
                        )

    # ------------------------------------------- Task 3 ------------------------------------------------------------- #
    # TODO: Implement Task 3
    # Set new output path
    if report_type == 3:
        generate_html.output_dir = CONFIG['output_dir']

    # ------------------------------------------- DEBUG -------------------------------------------------------------- #
    if debug:
        # JIRA_UPDATER-75
        # 3336531
        # jira_savapi-433.py_42628.html
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(platforms_dkt_data)
        pp.pprint(tests_status_dkt)


####################################################################################################
# Standard boilerplate to call the main() function to begin the program.
# This only runs if the module was *not* imported.
if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)

    main(arguments)
