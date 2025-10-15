from importlib.util import find_spec
import os
import re
import subprocess

import yaml

keywords = ["__READABLE_NAME", "__DESCRIPTION"]
hw_keywords = keywords + ["__MODEL"]

PACKAGE_DATA_FILE = "package_data.py"


def get_package_dirs(packages):
    package_dirs = []
    for package in packages:
        package_spec = find_spec(package)
        if package_spec is None:
            print(f"Package {package} not found")
            return None
        package_dirs.append(os.path.dirname(package_spec.origin))
    return package_dirs


def get_filenames(files, packages):
    filenames = [PACKAGE_DATA_FILE]
    for x in files:
        if os.path.isdir(x):
            filenames += [os.path.join(dirpath, f)
                          for dirpath, dirnames, files in os.walk(x)
                          for f in files if any(f.endswith(ending) for ending in [".py", ".cpp", ".h", ".hpp", ".c"])]
        else:
            filenames.append(x)
    return filenames


def create_translation(out, files, packages, force_dir, no_translate, hardware, library, languages):
    global keywords

    if not force_dir:
        keys = ["docker"] if hardware else ["docker", "src"]
        for key in keys:
            if not os.path.exists(key):
                if key == "src":
                    print(
                        f"Directory {key} does not exist. Are you in the service base directory?"
                        f" If you want to translate a hardware package, use the '--hardware' option. "
                        f"To skip this check pass the argument '--force_dir'")
                else:
                    print(f"Directory {key} does not exist. Are you in the service base directory? "
                          f"To skip this check pass the argument '--force_dir'")
                return

    print(f"Translating service {os.path.basename(os.getcwd())}")

    def out_dir(path):
        return os.path.abspath(os.path.join(out, path))

    def lang_dir(lang, file, base_dir=out_dir("locale")):
        return os.path.abspath(os.path.join(base_dir, lang, "LC_MESSAGES", file))

    package_dirs = get_package_dirs(packages)
    if package_dirs is None:
        return

    kraken_config_exists = os.path.exists(out_dir("../kraken_config.yml"))
    keywords_to_add = [] if library or kraken_config_exists else (hw_keywords if hardware else keywords)
    if hardware:
        files = []
        packages = []
    else:
        files += package_dirs

    for language in languages:
        os.makedirs(lang_dir(language, ""), exist_ok=True)

    filenames = get_filenames(files, packages)

    with open(PACKAGE_DATA_FILE, "w") as tmp:
        for x in keywords_to_add:
            tmp.write(f'_("{x}")\n')

    try:
        cmd = ["xgettext", "--omit-head", "--from-code", "utf-8", "--no-location", "-d", "translation", "-o",
               out_dir("locale/translation.pot"), "--sort-output", "--no-wrap", "--keyword=_c:1c,2", "--keyword=__:1,2",
               "--keyword=__c:1c,2,3", "--keyword=___:1", *filenames]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if b"following msgid contains non-ASCII characters" in output:
            print(output.decode("utf8"))
            print("non-ASCII characters must not be in texts as they won't work in practise")
            return

        if not os.path.exists(out_dir("locale/translation.pot")):
            print("Nothing to translate")
            return

        print("Created new translations")
        for language in languages:
            if os.path.exists(lang_dir(language, "translation.po")):
                subprocess.check_output(["msgmerge", "--no-location", "-U", "--lang", language,
                                         lang_dir(language, "translation.po"),
                                         out_dir("locale/translation.pot")])
            else:
                subprocess.check_output(["cp", out_dir("locale/translation.pot"), lang_dir(language, "translation.po")])
            for package_dir in package_dirs:
                package_po = lang_dir(language, "translation.po",
                                      base_dir=os.path.join(package_dir, "translation/locale"))
                print(package_dir, package_po, os.path.exists(package_po))
                if os.path.exists(package_po):
                    subprocess.check_output(["msgcat", package_po, lang_dir(language, "translation.po"),
                                             "-o", lang_dir(language, "translation.po"), "--use-first"])
            subprocess.check_output(["msgfmt", "-o", lang_dir(language, "translation.mo"),
                                     lang_dir(language, "translation.po")])
            if not no_translate:
                poedit(out, language)
            if library:
                subprocess.check_output(["msgattrib", "-o", lang_dir(language, "translation.po"), "--no-obsolete",
                                         lang_dir(language, "translation.po")])

        print("Finished translation")
    finally:
        os.unlink(PACKAGE_DATA_FILE)


def poedit(out, language):
    def lang_dir(lang, file):
        return os.path.join(out, "locale", lang, "LC_MESSAGES", file)

    subprocess.check_output(["poedit", lang_dir(language, "translation.po")])
    subprocess.check_output(["msgfmt", "-o", lang_dir(language, "translation.mo"),
                             lang_dir(language, "translation.po")])
    print(f"Merged language {language}")
    return 0


MSG_EMTPY_REGEX = re.compile(r'^msgid\s*"(.*?)".*?\n.*?\n?^msgstr(\[\d*\])?\s*"(.*?)"', re.DOTALL)


def check_translations(directory, files, packages, check_keywords, hardware, library, languages):
    global keywords

    def out_dir(path):
        return os.path.abspath(os.path.join(directory, path))

    def lang_dir(lang, file):
        return os.path.abspath(os.path.join(out_dir("locale"), lang, "LC_MESSAGES", file))

    package_dirs = get_package_dirs(packages)
    if package_dirs is None:
        return 0

    kraken_config_fn = out_dir("../kraken_config.yml")
    kraken_config_exists = os.path.exists(kraken_config_fn)
    if kraken_config_exists:
        with open(kraken_config_fn, "r") as file:
            config = yaml.load(file, Loader=yaml.SafeLoader)
            if "translation" not in config or any(x not in config["translation"] for x in languages) \
                    or any(any(v not in lang for v in ["name", "description"])
                           for lang in config["translation"].values()):
                print("Translations in kraken_config.yml are missing or incomplete")
                return -1
        if not os.path.exists("docker/translation/locale/translation.pot"):
            print("No additional translations: Translations ok")
            return 0

    keywords_to_add = [] if library or kraken_config_exists else keywords
    if hardware:
        files = []
        packages = []
        keywords_to_add = hw_keywords
    else:
        files += package_dirs

    for language in languages:
        os.makedirs(lang_dir(language, ""), exist_ok=True)

    filenames = get_filenames(files, packages)

    with open(PACKAGE_DATA_FILE, "w") as tmp:
        for x in keywords_to_add:
            tmp.write(f'_("{x}")\n')
    try:
        cmd = ["xgettext", "--omit-head", "--from-code", "utf-8", "--no-location", "-d", "translation", "-o",
               out_dir("locale/translation.pot"), "--sort-output", "--no-wrap", "--keyword=_c:1c,2", "--keyword=__:1,2",
               "--keyword=__c:1c,2,3", "--keyword=___:1", *filenames]
        subprocess.check_output(cmd)
        os.unlink(PACKAGE_DATA_FILE)

        res = subprocess.check_output(["git", "status", "-s", "|", "grep", "docker/translation/"])
        if res.decode().strip():
            print("You do not have all strings in your translation file, create them with 'openmodule_makemessages'")
            print(res.decode().strip())
            print(subprocess.check_output(["git", "diff"]).decode())
            return -1

        print("Check translation files")
        empty_messages = dict()
        empty_keyword_messages = dict()
        for language in languages:
            with open(lang_dir(language, "translation.po"), "r") as file:
                data = file.read()
                # first entry is header
                results = MSG_EMTPY_REGEX.findall(data)
                empty_messages[language] = [x for x in results if x[0].strip() and x[0].strip()
                                            not in keywords_to_add and not x[2].strip()]
                empty_keyword_messages[language] = [x for x in results if x[0].strip() in keywords_to_add
                                                    and not x[2].strip()]

        fail = False
        for language in languages:
            if check_keywords and empty_keyword_messages[language]:
                print(f"Missing translated keywords in {language}: {', '.join(empty_keyword_messages[language])}")
                fail = True
            if language != "en" and empty_messages[language]:
                print(f"Missing translations in {language}: {len(empty_messages[language])}")
                print("\n".join([x[0] for x in empty_messages[language]]))
                fail = True

        if fail:
            return -1
        if os.path.exists(out_dir("../Dockerfile")):
            with open("docker/Dockerfile", "r") as file:
                if "ADD docker/translation /translation" not in file.read():
                    print("Translations are not added to docker image, add the line:")
                    print("ADD docker/translation /translation")
                    return -1

        print("Translations ok")
    finally:
        if os.path.exists(PACKAGE_DATA_FILE):
            os.unlink(PACKAGE_DATA_FILE)
    return 0
