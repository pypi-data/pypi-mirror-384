"""
License GPL3

(C) 2024-2025 Created by Maikel Mardjan - https://nocomplexity.com/

Simple Link checker for JupyterBook markdown files. Simplifies maintenance for dead URLs in JupyterBook projects.
"""

import fire  # for working CLI with this PoC-thing (The Google way)
import asyncio

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import os
import sys  # Import the sys module

from linkaudit import html_result
from linkaudit import markdownhelpers
from linkaudit import nocxhelpers
from linkaudit import __version__

	
nocxheaders = {
    "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0" }
nocxtimeout = 4

linkaudit_ascii_art=r"""
-----------------------------------------------
  _     _       _       _             _ _ _   
 | |   (_)_ __ | | __  / \  _   _  __| (_| |_ 
 | |   | | '_ \| |/ / / _ \| | | |/ _` | | __|
 | |___| | | | |   < / ___ | |_| | (_| | | |_ 
 |_____|_|_| |_|_|\_/_/   \_\__,_|\__,_|_|\__|
 ----------------------------------------------
"""

REPORT_NAME = 'linkaudit-report.html'

async def async_checkurl(url):
    """
    The async version
    Checks the status of a given URL and reports HTTP status codes or DNS errors.

    Args:
        url (str): The URL to check.

    Returns:
        tuple: A tuple containing the URL and either the status code or an error message.
    """

    def check_url():
        try:
            request = Request(url, headers=nocxheaders)
            with urlopen(request, timeout=nocxtimeout) as response:
                return url, response.status
        except HTTPError as e:
            return url, f"HTTP Error: {e.code} {e.reason}"
        except URLError as e:
            return url, f"URL Error: {e.reason}"
        except Exception as e:
            return url, f"Unexpected Error: {str(e)}"

    return await asyncio.to_thread(check_url)


async def process_multiple_urlchecks(urls):
    """Process multiple URLs asynchronously."""
    tasks = [async_checkurl(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results


def check_links_in_markdown_file(file_path):
    """Checks all URLs in a markdown file"""
    urls_to_check = []  # List to store URLs to be checked
    line_url_mapping = []  # List to store tuples of (line_number, url)
    with open(file_path, "r") as file:
        lines = file.readlines()
        # Loop through each line and search for URLs
        for line_number, line in enumerate(lines, start=1):
            urls = markdownhelpers.extract_urls_from_markdown(line)
            for url in urls:
                urls_to_check.append(url)
                line_url_mapping.append((line_number, url))
    # Check the URLs using the new process_multiple_urlchecks function
    url_statuses = asyncio.run(process_multiple_urlchecks(urls_to_check))
    # Create a dictionary for easy lookup of status codes by URL
    url_status_dict = dict(url_statuses)
    # Combine the lists into a list of dictionaries
    combined = []
    for line_number, url in line_url_mapping:
        status = url_status_dict.get(
            url, "N/A"
        )  # Default to "N/A" if status is not found
        combined.append({"line_number": line_number, "url": url, "status": status})
    return combined


def show_all_links(bookdirectory, filename=REPORT_NAME):
    """Shows all URLs from MyST Markdown files in a directory and generates an HTML report.

    Args:
        bookdirectory (str): The path to the directory containing Markdown files to analyze.

    Returns:
        None: Outputs an HTML file named "REPORT_NAME" with the report.

    """
    files_tocheck = markdownhelpers.collect_markdown_files(bookdirectory)
    htmloutput = (
        "<h1> Overview of URLs  - Link Audit for markdown files (URL checker) </h1><br>"
    )
    l = len(files_tocheck)
    nocxhelpers.printProgressBar(0, l, prefix="Progress:", suffix="Complete", length=50)
    total_urls = 0
    for index, md_file in enumerate(files_tocheck):
        # result = markdownhelpers.extract_urls_from_markdown(md_file)
        result = markdownhelpers.get_links_in_markdown_file(md_file)
        nocxhelpers.printProgressBar(
            index + 1, l, prefix="Progress:", suffix="Complete", length=50
        )
        if result:  # only save files with links
            htmloutput += f"<h3>Result: {md_file}</h3><br>"
            htmloutput += html_result.generate_html_table(result)
            htmloutput += "<br><br>"
            total_urls += len(result)
    htmloutput += "<h2> Summary </h2><br>"
    htmloutput += f"<p>Total number of found URLs: {total_urls} </p>"
    print(f"Total number of found URLs: {total_urls}")
    html_result.create_output_htmlfile(htmloutput, filename)


def check_md_files(bookdirectory, result_output="H"):
    """Print txt tables of URLs checks of JB Book
    Args:
        bookdirectory (str): The path to the directory containing Markdown files to analyze.
        result_output (str, optional): Output format, "H" for HTML (default) or "T" for TXT.
            Overridden by user input during execution.

    Returns:
        None: Outputs either "REPORT_NAME" or "linkaudit_result.md" based on user choice.    
    """
    files_tocheck = markdownhelpers.collect_markdown_files(bookdirectory)
    result_output = input("HTML output [H] (=Default) or TXT output [T]? )")
    txtoutput = "# Result of Link Audit for markdown files (URL checker) \n\n"
    htmloutput = "<h1> Result of Link Audit for markdown files (URL checker) </h1><br>"
    htmloutput += "<p><i> Note: </i> Only URLs with issues are reported! Broken links are reported per file. </p><br>"
    l = len(files_tocheck)
    nocxhelpers.printProgressBar(0, l, prefix="Progress:", suffix="Complete", length=50)
    total_urls = 0
    for index, md_file in enumerate(files_tocheck):
        result = check_links_in_markdown_file(md_file)
        total_urls += len(result)
        # Filter out entries with status 200 - So only report files with broken links.
        filtered_result = [entry for entry in result if entry["status"] != 200]
        if filtered_result:
            if result_output == "T":
                nocxhelpers.printProgressBar(
                    index + 1, l, prefix="Progress:", suffix="Complete", length=50
                )
                table = markdownhelpers.create_markdown_table(filtered_result)
                txtoutput += f"## Result: {md_file} \n\n"
                txtoutput += table
                txtoutput += "\n\n"
            else:
                nocxhelpers.printProgressBar(
                    index + 1, l, prefix="Progress:", suffix="Complete", length=50
                )
                htmloutput += f"<h3>Result: {md_file}</h3><br>"
                htmloutput += html_result.generate_html_table(filtered_result)
                htmloutput += "<br><br>"
    if result_output == "T":
        txtoutput += "## Summary \n\n"
        txtoutput += f"Total number of found URLs: {total_urls} \n\n"
        with open("linkaudit_result.md", "w", encoding="utf-8") as file:
            file.write(txtoutput)
        current_directory = os.getcwd()  # gets the current directory
        result_location = current_directory + "/" + "linkaudit_report.md"
        print(f"Markdown result file written! Check file : file://{result_location}")
    else:
        htmloutput += "<h2> Summary </h2><br>"
        htmloutput += f"<p>Total number URLs detected: {total_urls} </p>"
        html_result.create_output_htmlfile(htmloutput, REPORT_NAME)


def display_version():
    """Prints the module version. Use [-v] [--v] [-version] or [--version]."""
    print(f"version: {__version__}")


def display_help():
    """Prints linkaudit help text"""
    print(linkaudit_ascii_art)
    print('LinkAudit - Superfast, simple, and deadly accurate to find broken links in markdown.\n')
    print('Usage: linkaudit COMMAND [PATH]\n')
    print('Commands:')
    commands = ["showlinks", "checklinks", "version"]  # commands on CLI
    functions = [
        show_all_links,
        check_md_files,
        display_version,
    ]  # Related functions relevant for help
    for command, function in zip(commands, functions):
        docstring = function.__doc__
        summary = docstring.split("\n", 1)[0]        
        print(f"  {command:<20} {summary}")   
    print("Use linkaudit [COMMAND] --help for detailed help per command.")
    print("\nUse the Linkaudit documentation to learn more!\nCheck: https://nocomplexity.com/documents/linkaudit/intro.html\n")



def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-v", "--v", "--version", "-version"):
        display_version()
    elif len(sys.argv) > 1 and sys.argv[1] in ("-help", "-?", "--help", "-h"):
        display_help()
    elif len(sys.argv) == 1:
        display_help()
    else:
        fire.Fire(
            {
                "checklinks": check_md_files,
                "showlinks": show_all_links,
                "version": display_version,
                "--version": display_version,
                "-help": display_help,
            }
        )


if __name__ == "__main__":
    main()
