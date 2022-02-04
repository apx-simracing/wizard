from subprocess import check_output, Popen, PIPE
from re import match
import glob
from os import listdir
from json import loads


def get_rfcmp_info_command(env, *args, **kwargs):
    files = args[0]
    pattern = r"(Name|Version|Type)=(.*)"
    results = {}
    for file in files:
        results[file] = {}
        try:
            ps = Popen(('strings', file), stdout=PIPE)
            output = check_output(
                ('grep', '-E', '(Version|Name|Type)'), stdin=ps.stdout)
            ps.wait()
            raw_matches = output.decode("utf-8").split("\n")
            for raw_match in raw_matches:
                if raw_match:
                    got = match(pattern, raw_match)
                    name = got.groups(1)[0]
                    value = got.groups(1)[1]
                    results[file][name] = value
        except:
            print("File read error")
            return False
    print(results)
    return True


def get_components_in_directory_command(env, *args, **kwargs):
    base_folder = args[0][0]
    files = glob.glob(base_folder + '/**/*.rfcmp', recursive=True)
    components = []
    for file in files:
        component_in_file = get_rfcmp_info_command(env, [file], kwargs)
        components.append(component_in_file)
    print(components)
    return True


def check_config_command(env, *args, **kwargs):
    config = args[0][0]
    with open(config, "r") as file:
        data = loads(file.read())
        print(data)
