import os
import sys
import csv
import argparse
import logging
from importlib import resources
from pathlib import Path
from . import __version__
from .compiler import compile_tex_files_in_directory
from .processor import process_files, install_packages

def compile_command(args):
    """Handle the compile command."""
    input_path = args.input

    # Check if input is a directory or CSV file
    if os.path.isdir(input_path):
        logging.info(f"Compiling .tex files in directory: {input_path}")
        compile_tex_files_in_directory(input_path)
    elif os.path.isfile(input_path) and input_path.endswith(".csv"):
        with open(input_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                directory = os.path.join(args.source, row[args.key].replace(",", "_").replace(" ", "_"))
                logging.info(f"Compiling .tex files in directory: {directory}")
                compile_tex_files_in_directory(directory)
    else:
        logging.error("Error: Invalid input path.")
        sys.exit(1)

    print("\nCompiling tex files complete!")

def render_command(args):
    """Handle the render command."""
    # Get default template path if none specified
    template_path = args.template
    if template_path == "base_qtex_template.tex":
        try:
            # For Python 3.9+
            with resources.files("qpytexi.templates").joinpath("base_qtex_template.tex").open() as f:
                template_path = str(resources.files("qpytexi.templates").joinpath("base_qtex_template.tex"))
        except Exception as e:
            # Fallback for older Python versions
            template_path = str(Path(__file__).parent / "templates" / "base_qtex_template.tex")
            if not Path(template_path).exists():
                raise FileNotFoundError(f"Cannot find template at {template_path}")
    
    # Verify template file exists
    if not os.path.exists(template_path):
        logging.error(f"Error: Template file not found at {template_path}")
        sys.exit(1)
    
    logging.info(f"Using template file: {template_path}")

    # Install packages if a requirements file is provided
    if args.required_packages:
        install_packages(args.required_packages)
    
    process_files(
        args.exam_json,
        args.student_csv,
        template_path,
        args.source,
        args.output,
        args.solution_tags.split(","),
        args.shuffle,
        args.random,
        getattr(logging, args.log_level.upper()),
        args.student_name_tag,
        args.preamble_tag,
        args.content_tag
    )

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="qpytexi - A Python package for generating LaTeX documents with Python integration")
    
    # Add version argument
    parser.add_argument('-v', '--version', action='version',
                       version=f'qpytexi version {__version__}')
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile LaTeX files to pdf using pdlatex")
    compile_parser.add_argument("input", type=str, help="Path to a directory or a CSV file")
    compile_parser.add_argument("--source", "-s", type=str, default=os.getcwd(),
                              help="Root directory (default is current directory)")
    compile_parser.add_argument("--key", "-k", type=str, default="studentname",
                              help="Column name in CSV to build directories (default is 'studentname')")
    compile_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    
    # Render command
    render_parser = subparsers.add_parser("render", help="Render qtex files to a LaTeX template")
    render_parser.add_argument("-exam-json", "-c", type=str, help="Path to the exam JSON file (optional).")
    render_parser.add_argument("-student-csv", "-i", type=str, help="Path to the student CSV file (optional).")
    render_parser.add_argument("--template", "-t", type=str, default="base_qtex_template.tex",
                             help="Name of the LaTeX template file in source.")
    render_parser.add_argument("--source", "-s", type=str, help="Path to source directory of .qtex files.")
    render_parser.add_argument("--output", "-o", type=str, help="Path to output directory.")
    render_parser.add_argument("--solution-tags", type=str, default="\\printanswers",
                             help="Comma-separated solution tags to be inserted in the solution files.")
    render_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    render_parser.add_argument("--student-name-tag", "-n", type=str, default="studentname",
                             help="Specify the student name tag in the CSV file.")
    render_parser.add_argument("--preamble-tag", type=str,
                             default="% Preamble Template Insertion Point %",
                             help="Tag in the LaTeX template for preamble insertion.")
    render_parser.add_argument("--content-tag", type=str,
                             default="% INSERT CONTENT HERE %",
                             help="Tag in the LaTeX template for content insertion.")
    render_parser.add_argument("--shuffle", action="store_true",
                             help="Shuffle qtex files for each student.")
    render_parser.add_argument("--random", "-r", type=int,
                             help="Select up to N random questions from each question block.")
    render_parser.add_argument("--required-packages", "-p", type=str,
                             help="Path to a requirements.txt file for package installation.")
    
    args = parser.parse_args()
    
    if args.command is None and len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Set up logging
    log_level_str = getattr(args, 'log_level', 'INFO').upper()
    if log_level_str not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        print("Invalid log level. Use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        sys.exit(1)
    log_level = getattr(logging, log_level_str)
    
    # Handle commands
    if args.command == "compile":
        compile_command(args)
    elif args.command == "render":
        render_command(args)

if __name__ == "__main__":
    main() 