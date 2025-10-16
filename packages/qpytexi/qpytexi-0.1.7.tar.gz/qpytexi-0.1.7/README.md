# Quick Python Tex/Latex Integrator (qpytexi)

A Python package for generating LaTeX documents with Python integration, particularly useful for creating exams and homework assignments.

## Installation

Install directly from PyPI:

```bash
pip install qpytexi
```

## Commands

### Render Command

Process qtex files into LaTeX documents with support for Python code execution, figure generation, and student-specific customization.

```bash
# Basic usage with exam JSON
qtex render -exam-json exam.json

# Process with student CSV
qtex render -exam-json exam.json -student-csv students.csv

# Shuffle questions
qtex render --source ./source --output ./output --shuffle

# Select random questions
qtex render -exam-json exam.json --random 3
```

Options:
- `-exam-json, -c`: Path to the exam JSON file (optional)
- `-student-csv, -i`: Path to the student CSV file (optional)
- `--template, -t`: Name of the LaTeX template file (default: base_qtex_template.tex)
- `--source, -s`: Path to source directory of .qtex files
- `--output, -o`: Path to output directory
- `--solution-tags`: Comma-separated solution tags (default: \printanswers)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--student-name-tag, -n`: Student name tag in CSV file (default: studentname)
- `--shuffle`: Shuffle qtex files for each student
- `--random, -r`: Select N random questions from each question block
- `--required-packages, -p`: Path to requirements.txt for package installation

### Compile Command

Compile LaTeX files in a directory or process a CSV file containing student information.

```bash
# Compile all .tex files in a directory
qtex compile /path/to/directory

# Compile files using a CSV file
qtex compile students.csv --source /path/to/source --key studentname
```

Options:
- `input`: Path to a directory or CSV file
- `--source, -s`: Root directory (default is current directory)
- `--key, -k`: Column name in CSV to build directories (default is 'studentname')
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## File Formats

### QTEX Files
QTEX files are Markdown-like files that can contain Python code chunks and inline Python expressions.

Example qtex file:
```markdown
\section{Example Question}

Here's a question with a Python-generated value: `python 2 + 2`

    ```{python chunk1, echo=True, output="asis"}
    print("This will be shown in the LaTeX output")
    ```

    ```{python chunk2, output="fig"}
    import matplotlib.pyplot as plt
    plt.plot([1, 2, 3], [1, 2, 3])
    plt.title("Example Plot")
    ```
```

Code chunk options:
- `echo`: Show the code in the output (default: False)
- `output`: Output type ("hide", "asis", "fig")
- `figwidth`: Width of figures as fraction of linewidth (default: 0.8)
- `run`: Execute the code (default: True)

### Exam JSON
The exam JSON file specifies the qtex files to process and can include additional preamble data.

Example exam.json:
```json
{
    "qtex_files": [
        "question1.qtex",
        ["question2a.qtex", "question2b.qtex"],
        "question3.qtex"
    ],
    "examTitle": "Midterm Exam",
    "courseCode": "MATH101"
}
```

Arrays within `qtex_files` define question blocks for random selection or shuffling.

### Student CSV
The student CSV file contains student-specific information used to customize the exams.

Example students.csv:
```csv
studentname,id,section
John Doe,12345,A
Jane Smith,12346,B
```

CSV columns become LaTeX commands in the template (e.g., \studentname, \id, \section).

## Template System

QuizTeX uses a template system for LaTeX document generation. The default template includes:
- Preamble insertion point: `% Preamble Template Insertion Point %`
- Content insertion point: `% INSERT CONTENT HERE %`

Custom templates can be specified with the `--template` option.

## Requirements

- Python 3.11 or higher
- LaTeX installation (for compilation)
    - Currently pdflatex is used for compiling built latex files.
- Required Python packages:
  - numpy >= 2.0.0
  - matplotlib >= 3.8.0

## License

MIT License - See LICENSE file for details.