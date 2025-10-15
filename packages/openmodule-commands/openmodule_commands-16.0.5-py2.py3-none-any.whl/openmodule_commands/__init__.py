import argparse
import sys

from openmodule_commands.translate import create_translation, poedit, check_translations


def openmodule_makemessages():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', help='Output directory where to save translation files', default="docker/translation")
    parser.add_argument('--files', help='Input files or directories for translation', nargs="*", default=["src/"])
    parser.add_argument('--packages', help='Python packages for translation', nargs="*", default=[])
    parser.add_argument('--force-dir', help='Disable check if directory is a openmodule directory', required=False,
                        action="count")
    parser.add_argument('--no-translate', help='Do not open editor for translation', required=False,
                        action="count")
    parser.add_argument('--hardware', help='The service is only a hardware package with no actual code. '
                                           'Only translate hardware keywords.',
                        required=False,  action="count")
    parser.add_argument('--library', help='Do not add __READABLE_NAME and __DESCRIPTION.',
                        required=False,  action="count")
    parser.add_argument('--languages', help='Languages to translate to (lowercase iso2)', nargs="*",
                        default=["en", "de"])
    args = parser.parse_args()
    create_translation(args.out, args.files, args.packages, args.force_dir, args.no_translate, args.hardware,
                       args.library, args.languages)


def openmodule_translate():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='Directory of the locale directory', default="docker/translation")
    parser.add_argument('--lang', help='Language for translation', required=False, default="de")
    args = parser.parse_args()
    poedit(args.dir, args.lang)


def openmodule_check_translation():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', help='Directory of the locale directory', default="docker/translation")
    parser.add_argument('--files', help='Input files or directories for translation', nargs="*", default=["src/"])
    parser.add_argument('--packages', help='Python packages for translation', nargs="*", default=[])
    parser.add_argument('--ignore-keywords', help='Ignore the special keywords defined in openmodule', action="count")
    parser.add_argument('--hardware', help='The service is only a hardware package with no actual code. '
                                           'Only translate hardware keywords.',
                        required=False,  action="count")
    parser.add_argument('--library', help='Do not add __READABLE_NAME and __DESCRIPTION.',
                        required=False,  action="count")
    parser.add_argument('--languages', help='Languages to translate to (lowercase iso2)', nargs="*",
                        default=["en", "de"])
    args = parser.parse_args()
    sys.exit(check_translations(args.dir, args.files, args.packages, bool(args.ignore_keywords), args.hardware,
                                args.library, args.languages))
