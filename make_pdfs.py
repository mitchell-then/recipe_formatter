#!/usr/bin/env python3

# Author: Mitchell Then

import os
import re
import shutil
import subprocess
import sys
import tempfile
import yaml


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: {} <src dir> <dest dir>\n".format(
            os.path.basename(__file__)))
        exit(1)

    src_dir = os.path.abspath(sys.argv[1])
    dest_dir = os.path.abspath(sys.argv[2])

    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)

    for (dirpath, dirnames, filenames) in os.walk(src_dir):
        # skip special "images" directory
        if "images" in dirpath:
            continue

        for filename in filenames:
            # skip hidden files
            if filename[0] == '.':
                continue
            if os.path.splitext(filename)[1] != '.yml':
                print("Skipping: {}".format(os.path.join(dirpath, filename)))
                continue

            recipe = None
            try:
                with open(os.path.join(dirpath, filename), 'r') as f:
                    recipe = yaml.load(f)
            except yaml.scanner.ScannerError:
                print("Not valid YAML: {}".format(
                    os.path.join(dirpath, filename)))
                continue

            latex = generate_latex(recipe, src_dir)

            output_filename = os.path.splitext(filename)[0] + '.tex'
            pdf_filename = os.path.splitext(filename)[0] + '.pdf'

            with open(output_filename, 'w') as f:
                f.write(latex)

            subprocess.call(['pdflatex', output_filename],
                            stdout=subprocess.PIPE)

            dest_dir = dirpath.replace(src_dir, dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

            shutil.copyfile(os.path.join(temp_dir, pdf_filename), os.path.abspath(
                os.path.join(dest_dir, pdf_filename)))

    shutil.rmtree(temp_dir)


def _get_blank(item):
    if item is None:
        return ''
    return item


def generate_latex(recipe, src_dir):
    latex = r"""
\1class{book}

\usepackage{graphicx}
\usepackage[margin=0.5in]{geometry}
\usepackage{tabularx}
\usepackage{nicefrac}
\usepackage{gensymb}

\pagenumbering{gobble}

\begin{document}

\begin{large}       % for larger text

"""

    # image
    if recipe.get('image') is not None:
        image = os.path.abspath(os.path.join(src_dir, recipe['image']))
        latex += r'\begin{center}' + "\n"
        latex += r'\fbox{\includegraphics[height=2in]{' + image + r'}}' + "\n"
        latex += r'\end{center}' + "\n"

    # header
    latex += r'\begin{center}' + "\n"
    latex += r'\begin{tabularx}{\textwidth}{ X r }' + "\n"
    latex += r'{\Huge \bfseries {' + str(_get_blank(recipe.get('name'))) + r'}} & ' + str(
        _get_blank(recipe.get('servings'))) + r' \\' + "\n"
    latex += r'\hline' + "\n"
    latex += r'& ' + str(_get_blank(recipe.get('time'))) + r' \\' + "\n"
    latex += r'\end{tabularx}' + "\n"
    latex += r'\end{center}' + "\n"

    for step in recipe.get('steps', []):

        if step.get('ingredients') is not None:
            latex += r'\begin{center}' + "\n"
            latex += r'\begin{tabularx}{\textwidth}{ >{\raggedright}p{3in} >{\raggedright}X }' + "\n"
            text = ''
            for ingredient in step.get('ingredients'):
                text += ingredient + ' \\newline' + "\n"
            text += "&\n"
            text += step.get('text') + "\\\\ \n"

            latex += text
            latex += r"""
\end{tabularx}
\end{center}
"""

        else:
            latex += r"""
\begin{center}
\begin{tabularx}{\textwidth}{ >{\raggedright}X }
""" + step.get('text') + r"""\\
\end{tabularx}
\end{center}
"""

    if recipe.get('notes') is not None:
        latex += r"""
\begin{center}
\begin{tabularx}{\textwidth}{ >{\raggedright}X }
{\Large \bfseries Notes: }""" + recipe.get('notes') + r"""\\
\end{tabularx}
\end{center}
"""

    latex += r"\end{large}" + "\n" + r"\end{document}"

    latex = re.sub(r'(\d+)/(\d+)', r'\\nicefrac{\1}{\2}', latex)
    # For some reason, \degree eats a following space, so escape it
    latex = re.sub(r'\\0\s', '\\degree\\\\ ', latex)
    latex = re.sub(r'\\0', '\\degree', latex)

    return latex


if __name__ == "__main__":
    main()