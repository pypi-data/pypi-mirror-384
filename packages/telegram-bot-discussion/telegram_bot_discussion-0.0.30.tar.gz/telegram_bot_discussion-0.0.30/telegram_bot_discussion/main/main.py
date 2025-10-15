from optparse import OptionParser
from os import path
from shutil import copytree


def main():
    usage = "Params: -n/--new-project project_path"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-n",
        "--new-project",
        dest="new_project",
        help="new_project_path",
        metavar="FILE",
    )
    (options, _) = parser.parse_args()
    if not options.new_project:
        print(usage)
        exit(1)
    from_dir = path.join(path.dirname(path.abspath(__file__)), "template_bot")
    to_dir = path.join(path.abspath("./"), str(options.new_project))
    if path.exists(to_dir):
        print(f"Dir `{to_dir}` already exists")
        exit(1)
    copytree(
        from_dir,
        to_dir,
        False,
    )
