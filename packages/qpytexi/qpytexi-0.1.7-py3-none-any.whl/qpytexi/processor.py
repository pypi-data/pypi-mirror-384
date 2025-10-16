import os
import sys
import csv
import subprocess
import logging
import random
import re
import numpy as np
from contextlib import redirect_stdout
import io
import json
import matplotlib
import importlib.metadata
import time
import uuid

matplotlib.use("Agg")  # Use a non-interactive backend

# Set a global random seed based on the current time
initial_seed = int(time.time())
random.seed(initial_seed)

def set_random_seed():
    new_seed = int(time.time()+int.from_bytes(os.urandom(2), 'big'))
    random.seed(new_seed)
    np.random.seed(new_seed)

def format_code_for_latex(code):
    """
    Format the code for inclusion in the LaTeX document using the listings package.
    """
    return "\\begin{lstlisting}[language=Python]\n" + code + "\n\\end{lstlisting}\n"


def execute_python_expression(expr, variables=None):
    """
    Execute a Python expression and return the result as a string.
    """
    try:
        output = io.StringIO()
        with redirect_stdout(output):
            logging.debug(f"Executing expression: {expr}")
            if variables:
                exec(f"print({expr})", globals(), variables)
            else:
                exec(f"print({expr})", globals())
        result = output.getvalue().strip()
        return result if result else ""
    except Exception as e:
        error_msg = f"Error executing expression '{expr}': {str(e)}"
        logging.error(error_msg)
        return f"[{error_msg}]"


def process_inline_python(content, variables=None):
    """
    Process and replace inline Python expressions in the content.
    """
    logging.debug("Finding all inline Python expressions in the content")
    inline_expressions = re.findall(r"`python (.*?)`", content)

    if inline_expressions:
        logging.info(
            f"Found {len(inline_expressions)} inline Python expressions to process"
        )
    else:
        logging.debug("No inline Python expressions found")

    for expr in inline_expressions:
        logging.debug(f"Processing expression: {expr}")
        result = execute_python_expression(expr, variables)
        logging.debug(f"Expression result: {result}")
        content = content.replace(f"`python {expr}`", result)

    return content


def execute_python_code(
    code, output_dir, file_prefix, attrs, variables=None, fig_counter=None
):
    """
    Execute Python code and return the appropriate output based on the output type.
    Variables is a dictionary of variable names and values to be passed to the exec environment.
    Fig_counter is a dictionary to track the number of figures per file.
    """
    formatted_code = format_code_for_latex(code) if attrs.get("echo", False) else ""
    chunk_id = attrs.get("id", "unknown")
    
    logging.debug(f"Executing Python code in chunk {chunk_id} of {file_prefix}")
    output_type = attrs.get("output", "hide")
    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    try:
        if output_type == "fig":
            exec(code, globals(), variables)
            fig_counter[file_prefix] = fig_counter.get(file_prefix, 0) + 1
            fig_name = f"{file_prefix}-{chunk_id}-fig-{fig_counter[file_prefix]:02d}.png"

            matplotlib.pyplot.savefig(os.path.join(assets_dir, fig_name))
            matplotlib.pyplot.close()
            logging.info(f"Saved figure: {fig_name}")

            fig_width = attrs.get("figwidth", "0.8")
            includegraphics_command = (
                f"\\begin{{center}}\\fbox{{\\includegraphics[width={fig_width}\\linewidth]{{assets/{fig_name}}}}}\\end{{center}}\n"
            )
            return formatted_code + includegraphics_command

        elif output_type == "asis":
            output = io.StringIO()
            with redirect_stdout(output):
                exec(code, globals(), variables)
            logging.debug(f"Returning 'asis' output for chunk {chunk_id} in {file_prefix}")
            return formatted_code + output.getvalue()

        else:
            exec(code, globals(), variables)
            logging.debug(f"Executing code with output type 'hide' for chunk {chunk_id} in {file_prefix}")
            return formatted_code

    except Exception as e:
        error_msg = f"Error in {file_prefix}, chunk {chunk_id}: {str(e)}"
        logging.error(error_msg)
        return formatted_code + f"\n[{error_msg}]"


def process_attributes(attributes_string):
    """
    Process the attribute string from a code block and return a dictionary of attributes.
    Removes surrounding quotes from attribute values.
    """
    logging.debug(f"Processing attribute string: {attributes_string}")
    components = attributes_string.split(",")

    # The first component should be the chunk ID
    chunk_id = components[0].strip()
    attrs = {"id": chunk_id, "echo": False, "output": "hide", "run": True}

    logging.debug(f"Chunk ID set to: {chunk_id}")

    # Process the rest of the attributes
    for attr in components[1:]:
        if "=" in attr:
            key, value = attr.split("=")
            value = value.strip()
            # Remove surrounding quotes if present
            if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                value = value[1:-1]

            # Set the attribute value
            if value.lower() == "true":
                attrs[key.strip()] = True
            elif value.lower() == "false":
                attrs[key.strip()] = False
            else:
                attrs[key.strip()] = value

            logging.debug(f"Processed attribute: {key.strip()} = {attrs[key.strip()]}")
        else:
            attrs[attr.strip()] = True
            logging.debug(f"Processed attribute: {attr.strip()} set to True")

    return attrs


def process_qtex_file(file_path, output_dir, variables=None):
    """
    Process a .qtex file based on the language, run, echo, and output attributes of code chunks.
    """
    # Ensure the file ends with .qtex
    if not file_path.endswith(".qtex"):
        file_path += ".qtex"

    try:
        with open(file_path, "r") as file:
            content = file.read()
    except Exception as e:
        error_msg = f"Error reading file {file_path}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    file_prefix = os.path.splitext(os.path.basename(file_path))[0]
    fig_counter = {}

    code_chunks = re.findall(r"```{(\w+)\s(.*?)}\n(.*?)\n```", content, re.DOTALL)

    for language, attributes, code in code_chunks:
        try:
            attrs = process_attributes(attributes)
            output = ""
            if attrs["echo"]:
                output += format_code_for_latex(code) + "\n\n"
            if language.lower() == "python" and attrs.get("run", True):
                output += (
                    execute_python_code(
                        code, output_dir, file_prefix, attrs, variables, fig_counter
                    )
                    + "\n\n"
                )
            # Construct the exact string to be replaced
            chunk_to_replace = f"```{{{language} {attributes}}}\n{code}\n```"
            content = content.replace(chunk_to_replace, output)
        except Exception as e:
            error_msg = f"Error processing chunk in {file_path}: {str(e)}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

    try:
        content = process_inline_python(content, variables)
    except Exception as e:
        error_msg = f"Error processing inline Python in {file_path}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    return content


def insert_into_template(template_input, compiled_content, preamble_insertions, preamble_tag="% Preamble Template Insertion Point %", content_tag="% INSERT CONTENT HERE %"):
    """
    Insert the preamble and compiled content into the LaTeX template.
    If `template_input` is a file path, load the file. Otherwise, treat it as raw LaTeX content.
    """
    # Load template content from file if it's a path, otherwise use it as raw content
    if os.path.exists(template_input):
        with open(template_input, "r", encoding="utf-8") as file:
            template_content = file.read()
    else:
        template_content = template_input
    
    # Insert the preamble and content into the template
    final_content = template_content.replace(preamble_tag, preamble_insertions)
    final_content = final_content.replace(content_tag, compiled_content)
    
    return final_content


def create_preamble_insertions(preamble_data, extra_commands, template_path):
    """
    Create LaTeX preamble insertions from a dictionary of data and extra commands.
    Check the LaTeX template to decide between \newcommand and \renewcommand.
    """
    insertions = ""

    # Read the template file to check for existing commands
    with open(template_path, 'r', encoding='utf-8') as file:
        template_content = file.read()

    for key, value in preamble_data.items():
        # Check if the command is already defined in the template
        if f'\\providecommand{{\\{key}}}' in template_content:
            insertions += f"\\renewcommand{{\\{key}}}{{{value}}}\n"
        else:
            insertions += f"\\newcommand{{\\{key}}}{{{value}}}\n"

    # Add extra commands
    if extra_commands:
        insertions += extra_commands + "\n"

    return insertions


def compile_qtex_files(file_list, output_dir):
    """
    Compile .qtex files listed in the input list and return the combined content.
    If a filename does not end with `.qtex`, append it.
    """
    compiled_content = ""
    
    # Process each .qtex file
    for qtex_filename in file_list:
        # Ensure the filename ends with .qtex
        if not qtex_filename.endswith(".qtex"):
            qtex_filename += ".qtex"
        
        # Get the full path to the file
        file_path = os.path.join(output_dir, qtex_filename)
        compiled_content += process_qtex_file(file_path, output_dir) + "\n"
    
    return compiled_content

def install_packages(directory_path):
    with open(directory_path, "r") as file:
        required_packages = [line.strip() for line in file if line.strip()]

    # Get installed packages and versions
    installed_distributions = {dist.metadata['Name']: dist.version for dist in importlib.metadata.distributions()}

    # Check for missing packages
    missing_packages = []
    for pkg in required_packages:
        if '==' in pkg:
            pkg_name, pkg_version = pkg.split('==')
            if installed_distributions.get(pkg_name) != pkg_version:
                missing_packages.append(pkg)
        else:
            if pkg not in installed_distributions:
                missing_packages.append(pkg)

    if missing_packages:
        logging.debug("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_packages])
    else:
        logging.debug("All packages from requirements are already installed.")

def process_files(exam_json, student_csv, template_file, source_dir, output_dir, solution_tags, shuffle_flag, random_n, log_level, student_name_tag, preamble_tag, content_tag):
    """
    Main logic for processing files with support for optional exam_json, student_csv, dynamic source, and output folders.
    """
    # Set up logging
    logging.basicConfig(
        filename=f".logs/{time.strftime('%Y%m%d-%H%M%S')}.log",
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Check source directory
    if source_dir is None:
        if exam_json:
            source_dir = os.path.dirname(os.path.abspath(exam_json))
        else:
            source_dir = os.getcwd()
    logging.info(f"Using source directory: {source_dir}")

    # Check output directory
    if output_dir is None:
        if exam_json:
            output_dir = os.path.join(source_dir, os.path.splitext(os.path.basename(exam_json))[0])
        else:
            output_dir = os.path.join(source_dir, f"output_{uuid.uuid4().hex}")
    else:
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(source_dir, output_dir)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Using output directory: {output_dir}")

    # Read exam JSON content if provided
    exam_data = {}
    if exam_json:
        logging.info("Reading JSON content from exam_json file")
        with open(exam_json, "r") as json_file:
            exam_data = json.load(json_file)
    
    # Get qtex files from exam_data, or find them in source_dir
    qtex_files = exam_data.pop("qtex_files", None)

    if not qtex_files:
        logging.info("No qtex_files field found in exam_data; locating .qtex files in source_dir")
        qtex_files = [file for file in os.listdir(source_dir) if file.endswith(".qtex")]

    if not qtex_files:
        logging.error("No .qtex files found or supplied. Exiting program.")
        sys.exit(1)

    # Handle CSV processing
    if student_csv:
        logging.info("Reading the student CSV and processing each row")
        with open(student_csv, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stName = row[student_name_tag]
                stDir = stName.replace(",", "_").replace(" ", "_")
                student_output_dir = os.path.join(output_dir, stDir)
                os.makedirs(student_output_dir, exist_ok=True)

                # Extract and merge preamble data
                logging.debug(f"Processing student: {stName}, Output directory: {student_output_dir}")
                preamble_data_dict = {key: row[key] for key in row}
                merged_preamble_data = {**preamble_data_dict, **exam_data}

                # Compile exam and solutions
                create_and_write_latex(student_output_dir, stName, merged_preamble_data, template_file, source_dir, qtex_files, solution_tags, shuffle_flag, random_n, preamble_tag, content_tag)
    else:
        # Handle single exam generation if no student CSV is provided
        single_output_dir = output_dir
        os.makedirs(single_output_dir, exist_ok=True)

        logging.info("No student CSV provided; rendering exam with generic preamble.")
        create_and_write_latex(single_output_dir, "output", exam_data, template_file, source_dir, qtex_files, solution_tags, shuffle_flag, random_n, preamble_tag, content_tag)

    print("\nProcessing qtex files complete!")

def create_and_write_latex(output_dir, filename, preamble_data, template_file, source_dir, qtex_files, solution_tags, shuffle_flag, random_n, preamble_tag, content_tag):
    """
    Create LaTeX documents with preamble data and qtex content.
    """
    # Generate preamble insertions
    standard_preamble_insertions = create_preamble_insertions(preamble_data, "", template_file)
    solution_preamble_insertions = create_preamble_insertions(preamble_data, "\n".join(solution_tags), template_file)

    # Shuffle or randomly select qtex files if necessary
    perm_qtex_files = []
    for qtex_block in qtex_files:
        if isinstance(qtex_block, list):  # If it's a block of questions
            if random_n:  # If --random N is specified, randomly select N questions
                set_random_seed()
                selected_questions = random.sample(qtex_block, min(random_n, len(qtex_block)))
                perm_qtex_files.extend(selected_questions)
            elif shuffle_flag:  # Otherwise, shuffle the questions
                set_random_seed()
                random.shuffle(qtex_block)
                perm_qtex_files.extend(qtex_block)
            else:
                perm_qtex_files.extend(qtex_block)
        else:
            perm_qtex_files.append(qtex_block)  # Non-blocked questions

    # Compile the qtex files into a single string
    flat_qtex_files = [os.path.join(source_dir, file) for file in perm_qtex_files]
    compiled_qtex_content = compile_qtex_files(flat_qtex_files, output_dir)

    # Insert preamble and content into the template using the insert_into_template function
    standard_output = insert_into_template(template_file, compiled_qtex_content, standard_preamble_insertions, preamble_tag, content_tag)
    solution_output = insert_into_template(template_file, compiled_qtex_content, solution_preamble_insertions, preamble_tag, content_tag)

    # Write the standard and solution LaTeX documents
    logging.info(f"Writing the compiled documents for {filename}")
    with open(os.path.join(output_dir, f"{filename}.tex"), "w") as file:
        file.write(standard_output)
    with open(os.path.join(output_dir, f"{filename}-solution.tex"), "w") as file:
        file.write(solution_output)
