import os
import subprocess
import logging

def compile_tex_files_in_directory(directory):
    """Compile all TEX files in the specified directory."""
    tex_files = [file for file in os.listdir(directory) if file.endswith(".tex")]
    
    if not tex_files:
        logging.warning(f"No .tex files found in directory: {directory}")
        return

    for file in tex_files:
        # Run pdflatex three times
        for _ in range(3):
            try:
                subprocess.run(
                    [
                        "pdflatex",
                        file,
                        "-shell-escape",
                        "-interaction=nonstopmode",
                    ],
                    cwd=directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
            except subprocess.SubprocessError as e:
                logging.error(f"An error occurred while processing {file}: {e}")

        # Clean up intermediate files
        for ext in [".aux", ".out"]:
            try:
                os.remove(os.path.join(directory, os.path.splitext(file)[0] + ext))
            except OSError:
                pass  # Ignore if file doesn't exist 