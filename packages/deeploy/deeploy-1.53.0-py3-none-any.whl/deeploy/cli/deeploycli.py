import os
import shutil
import sys
from enum import Enum
from typing import Dict

import click
from jinja2 import Environment, PackageLoader

from deeploy._version import __version__
from deeploy.cli.utils import validate_project_name

ALLOWED_TYPES = {"model", "explainer", "transformer"}

env = Environment(loader=PackageLoader("deeploy", "cli/templates"), autoescape=True)


class Instances(Enum):
    model = "model"
    explainer = "explainer"
    transformer = "transformer"

    def __str__(self):
        return self.value


@click.group()
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@click.option(
    "--name",
    "-n",
    prompt="Name of Project",
    help="Provide name of the project to be initialized.",
    callback=validate_project_name,
)
@click.option(
    "--initialization",
    "-i",
    default=["model"],
    help="State for which components the templates should be generated.\n"
    "Three options: -i model -i transformer -i explainer.\n"
    "Select one or more.",
    multiple=True,
)
def generate_template(name: str, initialization: list[str]):
    """Generates Sample Docker Image Template for Custom Docker Image"""
    # Validate initialization types
    invalid_types = set(initialization) - ALLOWED_TYPES
    if invalid_types:
        raise RuntimeError(
            f"Invalid initialization types: {', '.join(invalid_types)}. "
            f"Allowed types are: {', '.join(ALLOWED_TYPES)}."
        )

    projectname = name
    click.echo(f"Creating Project '{projectname}'.")
    os.makedirs(projectname, exist_ok=True)

    template_vars = {
        "projectname": projectname,
        "model": "model" in initialization,
        "explainer": "explainer" in initialization,
        "transformer": "transformer" in initialization,
        "version": __version__,
    }

    # Generate common files
    generate_readme(projectname, template_vars)
    click.echo("Generated README.")

    generate_metadata(projectname)
    click.echo("Generated metadata.")

    generate_script(projectname, template_vars)
    click.echo("Generated build script.")

    # Generate instance-specific templates
    for instance in Instances:
        if instance.value in initialization:
            response = generate_instance(projectname, template_vars, instance.value)
            if response:
                click.echo(f"Docker Image Template for {instance.value} is generated.")
            else:
                click.echo(f"Skipping {instance.value} since the files already exist.")

    click.echo(f"All templates for project '{projectname}' have been created!")


def generate_metadata(projectname: str):
    """Generates metadata.json file"""
    generate_file_from_template(
        template_name="metadata.json.j2",
        output_path=os.path.join(projectname, "metadata.json"),
        context={},
    )


def generate_readme(projectname: str, template_vars: Dict):
    """Generates Primary Readme file"""
    generate_file_from_template(
        template_name="README.md.j2",
        output_path=os.path.join(projectname, "README.md"),
        context=template_vars,
    )


def generate_script(projectname: str, template_vars: Dict):
    """Generates Script file"""
    generate_file_from_template(
        template_name="build.sh.j2",
        output_path=os.path.join(projectname, "build.sh"),
        context=template_vars,
    )


def generate_instance(projectname: str, template_vars: Dict, instance_type: str) -> bool:
    """Generates subdirectories and files of provided instance type"""
    template_vars["instance"] = instance_type
    instance_folder = os.path.join(projectname, f"{projectname}_{instance_type}")

    if not create_directory(instance_folder):
        return False

    # Generate instance-specific files
    generate_file_from_template(
        template_name=f"{instance_type}/Dockerfile.j2",
        output_path=os.path.join(instance_folder, "Dockerfile"),
        context=template_vars,
    )
    generate_file_from_template(
        template_name=f"{instance_type}/requirements.txt.j2",
        output_path=os.path.join(instance_folder, "requirements.txt"),
        context=template_vars,
    )
    generate_file_from_template(
        template_name=f"{instance_type}/__main__.py.j2",
        output_path=os.path.join(instance_folder, "__main__.py"),
        context=template_vars,
    )
    generate_file_from_template(
        template_name=f"{instance_type}/sample_{instance_type}.py.j2",
        output_path=os.path.join(instance_folder, f"sample_{instance_type}.py"),
        context=template_vars,
    )

    # Copy additional files if required
    copy_instance_files(projectname, instance_folder, instance_type)

    # Generate reference file
    reference_folder = os.path.join(projectname, instance_type)
    create_directory(reference_folder)
    generate_file_from_template(
        template_name="reference.json.j2",
        output_path=os.path.join(reference_folder, "reference.json"),
        context=template_vars,
    )

    return True


def generate_file_from_template(template_name: str, output_path: str, context: Dict):
    """Generates a file from a Jinja2 template"""
    template = env.get_template(template_name)
    content = template.render(context)
    with open(output_path, "w+") as file:
        file.write(content)


def create_directory(path: str) -> bool:
    """Creates a directory if it doesn't exist"""
    if not os.path.exists(path):
        os.mkdir(path)
        return True
    return False


def copy_instance_files(projectname: str, instance_folder: str, instance_type: str):
    """Copies instance-specific files if required"""
    pkgdir = sys.modules[str(sys.modules[__name__].__name__).split(".")[0]].__path__[0]
    if instance_type == "explainer":
        shutil.copy(
            os.path.join(pkgdir, f"cli/templates/{instance_type}/{instance_type}.dill"),
            os.path.join(instance_folder, f"{instance_type}.dill"),
        )
    elif instance_type == "model":
        shutil.copy(
            os.path.join(pkgdir, f"cli/templates/{instance_type}/{instance_type}.bst"),
            os.path.join(instance_folder, f"{instance_type}.bst"),
        )


def main():
    cli()
