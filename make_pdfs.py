#!/usr/bin/env python3

# Author: Mitchell Then

import os
import re
import shutil
import subprocess
import sys
import tempfile
import yaml
import jinja2
import argparse


def print_file_error(filename, message, detailed_message=''):
    print(f"{filename}: {message}")
    if detailed_message:
        for line in detailed_message.splitlines():
            print(f"\t{line}")


def create_invalid_step_error(step_type, step):
    error = [f"invalid {step_type} step:"]
    for line in yaml.dump(step, default_flow_style=False).splitlines():
        error.append(f"\t{line}")
    return "\n".join(error)


def validate_recipe(recipe, src_dir):
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
            if 'section' in step and (not step['section'] or len(step) != 1):
                errors.append(create_invalid_step_error('section', step))
            elif 'ingredients' in step:
                if not step['ingredients'] and not 'text' in step and not step['text'] or len(step) != 2:
                    errors.append(create_invalid_step_error('ingredients', step))
            elif 'text' in step and (not step['text'] or len(step) != 1):
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
        print_file_error(filename, "Invalid recipe", "\n".join([f"  {error}" for error in recipe_errors]))
        return None

    if 'image' in recipe:
        recipe['image'] = os.path.abspath(os.path.join(src_dir, recipe['image']))

    return recipe

def template_recipe(recipe):
    file_loader = jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__)))
    env = jinja2.Environment(loader=file_loader)
    env.variable_start_string = '<{'
    env.variable_end_string = '}>'
    env.trim_blocks = True
    env.lstrip_blocks = True
    template = env.get_template('recipe.tex.j2')
    file_content = template.render(recipe=recipe)
    return file_content

def create_recipe_latex_file(file_content, output_filename):
    file_content = re.sub(r'(\d+)/(\d+)', r'\\nicefrac{\1}{\2}', file_content)
    # For some reason, \degree eats a following space, so escape it
    file_content = re.sub(r'\\0\s', '\\degree\\\\ ', file_content)
    file_content = re.sub(r'\\0', '\\degree', file_content)

    with open(output_filename, 'w') as f:
        f.write(file_content)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_dir", type=str, help="directory containing recipe sources")
    parser.add_argument("dest_dir", type=str, help="destination directory for PDFs")
    return parser.parse_args()

def main():
    args = get_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        for (dirpath, _, filenames) in os.walk(args.src_dir):
            # skip special "images" directory
            if "images" in dirpath:
                continue

            pdf_dest_dir = dirpath.replace(args.src_dir, args.dest_dir)

            for filename in filenames:
                # skip hidden files and files that are not YAML
                if filename[0] == '.':
                    continue
                if os.path.splitext(filename)[1] != '.yml':
                    print("Skipping: {}".format(os.path.join(dirpath, filename)))
                    continue

                recipe = create_recipe(dirpath, filename, args.src_dir)
                if recipe is None:
                    continue

                latex_filename = os.path.splitext(filename)[0] + '.tex'
                pdf_filename = os.path.splitext(filename)[0] + '.pdf'

                latex_file_content = template_recipe(recipe)

                create_recipe_latex_file(latex_file_content, latex_filename)

                cmd = subprocess.run(['pdflatex', latex_filename],
                                stdout=subprocess.PIPE)

                if cmd.returncode != 0:
                    print("Something bad happened (likely bad latex): {}".format(cmd.stdout))
                    exit(1)

                os.makedirs(pdf_dest_dir, exist_ok=True)

                shutil.copyfile(os.path.join(temp_dir, pdf_filename), os.path.abspath(
                    os.path.join(pdf_dest_dir, pdf_filename)))


if __name__ == "__main__":
    main()
