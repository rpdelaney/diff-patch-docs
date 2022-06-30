"""
This script uses two modules that are not included in the python standard
library:

    * click: https://click.palletsprojects.com/en/8.1.x/
        For defining the command-line interface. Among other features, it
        enables easy command nesting with the `group` decorator.
    * requests: https://docs.python-requests.org/en/latest/
        HTTP library for humans.
"""
import json
import os
from urllib.parse import urljoin

import click
import requests

from .constants import JIRA_BASE_URL, QUALYS_BASE_URL
from .utils import parse_xml


@click.group()
def cli() -> None:
    pass


@cli.command(help="Get a list of all Jira issues in the OHS project.")
def jira() -> None:
    """Send a request to the Jira search API and print the response."""
    API_FRAGMENT = "rest/api/2/search"
    url = urljoin(JIRA_BASE_URL, API_FRAGMENT)

    response = requests.get(
        url,
        auth=requests.auth.HTTPBasicAuth(
            os.environ["JIRA_USERNAME"], os.environ["JIRA_PASSWORD"]
        ),
        headers={"Content-Type": "application/json"},
        timeout=5,
    )

    for line in response.iter_lines():
        print(line.decode())


@cli.group(help="Get information about Qualys scans.")
def scan() -> None:
    """Parent group for Qualys scan sub-commands."""
    pass


@scan.command(help="Get a list of all finished scans.")
def list() -> None:
    """Send a request to the Qualys scan API requesting a list
    of all finished scans, and convert the response from XML to JSON
    before printing."""
    API_FRAGMENT = "api/2.0/fo/scan"
    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)

    response = requests.post(
        url=url,
        auth=(os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]),
        headers={"X-Requested-With": "application/python"},
        data={"action": "list", "state": "Finished"},
        timeout=5,
    )

    response_dict = parse_xml(response.text)
    print(json.dumps(response_dict))


@scan.command(help="Get a detailed report on a specific scan.")
@click.argument("scan_id", type=click.STRING)
def details(scan_id: str) -> None:
    """Send a request to the Qualys scan API requesting a detailed
    report about a particular scan, and print the response.

    If the `scan_ref` field is not sent, the API will return data for all
    scans. Therefore, the scan_id argument is required.
    """
    API_FRAGMENT = "api/2.0/fo/scan"
    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)

    response = requests.post(
        url=url,
        auth=requests.auth.HTTPBasicAuth(
            os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]
        ),
        headers={"X-Requested-With": "application/python"},
        data={
            "action": "fetch",
            "scan_ref": f"scan/{scan_id}",
            "mode": "extended",
            "output_format": "json",
        },
        timeout=(5, None),
    )

    print(json.dumps(response.json()))


@cli.group(help="Get information about Qualys vulnerabilities.")
def vuln() -> None:
    """Parent group for Qualys vulnerability sub-commands."""
    pass


@vuln.command(
    help="Get information about a specific vulnerability by its QID."
)
@click.argument("vuln_id", type=click.STRING)
def info(vuln_id: str) -> None:
    """Send a request to the Qualys vulnerability API requesting information about
    a specific vulnerability, and convert the response from XML to JSON before
    printing."""
    API_FRAGMENT = "api/2.0/fo/knowledge_base/vuln/"
    url = urljoin(QUALYS_BASE_URL, API_FRAGMENT)

    response = requests.post(
        url=url,
        auth=requests.auth.HTTPBasicAuth(
            os.environ["QUALYS_USERNAME"], os.environ["QUALYS_PASSWORD"]
        ),
        headers={"X-Requested-With": "application/python"},
        data={
            "action": "list",
            "ids": vuln_id,
        },
        timeout=(5, 60),
    )

    response_dict = parse_xml(response.text)
    print(json.dumps(response_dict))
