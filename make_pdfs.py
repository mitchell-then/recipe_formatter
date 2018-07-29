#!/usr/bin/env python3

# Author: Mitchell Then

import argparse
import jinja2
import os
import re
import shutil
import subprocess
import tempfile
import yaml


def print_file_error(filename, message, detailed_message=''):
    """ Print an error for a file.

    Args:
        filename: Name of erroneous file.
        message: Short error message.
        detailed_message: Optional long error message.
    """
    print(f"{filename}: {message}")
    for line in detailed_message.splitlines():
        print(f"\t{line}")


def create_invalid_step_error(step_type, step):
    """ Create a formatted error message for invalid steps.

    Args:
        step_type: Type of step.
        step: Step dict.

    Returns:
        Formatted error message as string.
    """
    error_lines = [f"invalid {step_type} step:"]
    for line in yaml.dump(step, default_flow_style=False).splitlines():
        error_lines.append(f"\t{line}")
    return "\n".join(error_lines)


def section_step_is_valid(step):
    """ Return bool if section step is valid """
    return (step['section'] and len(step) == 1)


def ingredients_step_is_valid(step):
    """ Return bool if ingredients step is valid """
    return (step['ingredients'] and 'text' in step and step['text'] and len(step) == 2)


def text_step_is_valid(step):
    """ Return bool if text step is valid """
    return (step['text'] and len(step) == 1)


def validate_recipe(recipe, src_dir):
    """ Determine if a recipe is valid.

    Args:
        recipe: Recipe dictionary to validate.
        src_dir: Directory of source recipe files.

    Returns:
        List of error strings.
    """
    errors = []

    required_keys = ['name', 'steps']
    optional_keys = ['servings', 'time', 'image', 'notes']

    for key in required_keys:
        if key not in recipe:
            errors.append(f"required key {key} missing")
        elif not recipe[key]:
            errors.append(f"key {key} must be defined")

    if not errors:
        for step in recipe['steps']:
            if 'section' in step:
                if not section_step_is_valid(step):
                    errors.append(create_invalid_step_error('section', step))
            elif 'ingredients' in step:
                if not ingredients_step_is_valid(step):
                    errors.append(create_invalid_step_error('ingredients', step))
            elif 'text' in step:
                if not text_step_is_valid(step):
                    errors.append(create_invalid_step_error('text', step))

    for key in optional_keys:
        if key in recipe and not recipe[key]:
            errors.append(f"optional key {key} exists but must be defined")

    if 'image' in recipe and recipe['image']:
        image = os.path.abspath(os.path.join(src_dir, recipe['image']))
        if not os.path.isfile(image):
            errors.append(f"image file does not exist: {image}")

    return errors


def create_recipe(dirpath, filename, src_dir):
    """ Load, validate, and return a recipe from a given a recipe YAML file.

    Args:
        dirpath: Path to recipe file from src_dir.
        filename: Name of recipe file.
        src_dir: Path to recipe source directory.

    Returns:
        Recipe dict.
    """
    try:
        with open(os.path.join(dirpath, filename), 'r') as f:
            recipe = yaml.load(f)
    except yaml.scanner.ScannerError as e:
        print_file_error(filename, "Not valid YAML")
        return None
    except Exception as e:
        print_file_error(filename, "Exception for file", str(e))
        return None

    recipe_errors = validate_recipe(recipe, src_dir)

    if recipe_errors:
        print_file_error(filename, "Invalid recipe", "\n".join([f"  {e}" for e in recipe_errors]))
        return None

    if 'image' in recipe:
        recipe['image'] = os.path.abspath(os.path.join(src_dir, recipe['image']))

    return recipe


def template_recipe(recipe):
    """ Produce LaTeX file content from recipe.

    Args:
        recipe: Recipe to create LaTeX content.

    Returns:
        String of LaTeX file content of formatted recipe.
    """
    file_loader = jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__)))
    env = jinja2.Environment(loader=file_loader)
    env.variable_start_string = '<{'
    env.variable_end_string = '}>'
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env.get_template('recipe.tex.j2').render(recipe=recipe)


def create_recipe_latex_file(file_content, output_filename):
    """ Write LaTeX file content to file.

    Args:
        file_content: LaTeX file content.
        output_filename: Name of LaTeX file.
    """

    file_content = re.sub(r'(\d+)/(\d+)', r'\\nicefrac{\1}{\2}', file_content)
    # For some reason, \degree eats a following space, so escape it
    file_content = re.sub(r'\\0\s', '\\degree\\\\ ', file_content)
    file_content = re.sub(r'\\0', '\\degree', file_content)

    with open(output_filename, 'w') as f:
        f.write(file_content)


def get_args():
    """ Setup script arguments.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("src_dir", type=str, help="directory containing recipe sources")
    parser.add_argument("dest_dir", type=str, help="destination directory for PDFs")
    return parser.parse_args()


def main():
    args = get_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        temp_dest = os.path.join(temp_dir, 'temp_dest') + os.sep

        for (dirpath, _, filenames) in os.walk(args.src_dir):
            # skip special "images" directory
            if "images" in dirpath:
                continue

            pdf_temp_dest = dirpath.replace(args.src_dir, temp_dest)

            for filename in filenames:
                # skip hidden files and files that are not YAML
                if filename[0] == '.':
                    continue
                if os.path.splitext(filename)[1] != '.yml':
                    print_file_error(os.path.join(dirpath, filename), "Not YAML file")
                    continue

                recipe = create_recipe(dirpath, filename, args.src_dir)
                if recipe is None:
                    continue

                latex_filename = os.path.splitext(filename)[0] + '.tex'
                pdf_filename = os.path.splitext(filename)[0] + '.pdf'

                latex_file_content = template_recipe(recipe)

                create_recipe_latex_file(latex_file_content, latex_filename)

                cmd = subprocess.run(['pdflatex', latex_filename], stdout=subprocess.PIPE)

                if cmd.returncode != 0:
                    print("Something bad happened (likely bad latex): {}".format(cmd.stdout))
                    exit(1)

                os.makedirs(pdf_temp_dest, exist_ok=True)

                shutil.copyfile(os.path.join(temp_dir, pdf_filename), os.path.abspath(
                    os.path.join(pdf_temp_dest, pdf_filename)))

        if os.path.exists(args.dest_dir):
            shutil.rmtree(args.dest_dir)
        shutil.copytree(temp_dest, args.dest_dir)


if __name__ == "__main__":
    main()
