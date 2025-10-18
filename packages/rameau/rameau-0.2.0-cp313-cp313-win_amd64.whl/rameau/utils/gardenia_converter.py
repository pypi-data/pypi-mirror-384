# Copyright 2025, BRGM
# 
# This file is part of Rameau.
# 
# Rameau is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# Rameau is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# Rameau. If not, see <https://www.gnu.org/licenses/>.
#
import pandas as pd
import datetime
import tempfile
import os
import pathlib
import rameau


def _parse_file(filepath, extension, version):
    # read RGA/GAR file to parse
    with open(filepath, 'r', encoding='cp1252') as f:
        lines = f.read().splitlines()

    # skip lines corresponding to free text
    ignore = 0
    for i, line in enumerate(lines, start=1):
        if "--- Fin du texte libre ---" in line:
            ignore = i
            break

    lines = lines[ignore:]

    # read RGA/GAR conversion file
    df = pd.read_csv(
        os.path.join(
            os.path.dirname(__file__),
            "gardenia_converters",
            f"gardenia+{extension}+v{version}-to-rameau.csv"
        ),
        delimiter='\t', encoding='cp1252', keep_default_na=False,
        header=0, skiprows=[1, 2]
    )

    # parse files
    content = {}
    locals_ = {}

    for i, row in df.iterrows():
        # assign TOML endpoint(s) directly matching RGA/GAR value(s)
        if row['eval']:
            key_paths = row['rameau'].split(',')
            indices = row['index'].split(',')
            evaluations = row['eval'].split('#')

            for key_path, index, evaluation in zip(
                    key_paths, indices, evaluations
            ):
                # only process lines where there is something to evaluate
                if evaluation:
                    # only collect RGA/GAR values if it corresponds to an actual line
                    if row['line'] > 0:
                        locals_['x'] = (
                            lines[i].split(row['sep'])[int(index)].strip()
                        )

                    # evaluate Python code
                    v = eval(evaluation, None, locals_)

                    if issubclass(v.__class__, Exception):
                        # there is an error to raise
                        raise v.__class__(
                            f"invalid value {str(v)} for parameter {key_path} "
                            f"in *.{extension} file line {i}"
                        )
                    elif v is not None:
                        # evaluation actually produced a value
                        # so assign value to TOML endpoint
                        content[key_path] = v

    return content


def convert_rga_gar_to_toml(
        rga_file: str, gar_file: str,
        toml_file: str, gardenia_version: str
):
    """Function to convert legacy Gardenia RGA and GAR files into TOML
    configuration file.

    Parameters
    ----------
    rga_file: `str`
        Path to the Gardenia RGA file (with extension *.rga) to parse.

    gar_file: `str`
        Path to the Gardenia GAR file (with extension *.gar) to parse.

    toml_file: `str`
        Path to the Gardenia TOML file (with extension *.toml) to create
        to store the `Model` settings.

    gardenia_version: `str`
        Number of the version of the Gardenia model for which RGA/GAR
        files are to be parsed.

        .. warning:: Only version 8.8.* supported at the moment.

    """
    if not gardenia_version.startswith(('8.8',)):
        raise NotImplementedError(
            f"parsing for version {repr(gardenia_version)} not supported yet"
        )
    gardenia_version = '.'.join(gardenia_version.split('.')[0:2])

    # parse RGA/GAR content
    content = _parse_file(rga_file, 'rga', gardenia_version)
    content.update(_parse_file(gar_file, 'gar', gardenia_version))

    # reorganise content into categories
    categories = [
        'files', 'input_format', 'outputs', 'spinup', 'forecast',
        'optimization', 'watershed.all'
    ]
    leaves_to_wrap = ['value', 'opti', 'lower', 'upper']

    content_categorised = {category: {} for category in categories + ['root']}

    for key_path, value in content.items():
        # deal with special case where keypath was set empty in converter
        # file simply to evaluate some Python code
        if not key_path:
            continue

        # reformat value based on type if necessary for TOML rendering
        if isinstance(value, datetime.timedelta):
            value = f'{{ seconds = {int(value.total_seconds())} }}'
        elif isinstance(value, str):
            value = f'"{value}"'
        elif isinstance(value, bool):
            value = f'{str(value).lower()}'
        elif value is None:
            continue

        # sort parameters in relevant category
        found = False

        for category in categories:
            if key_path.startswith(f'{category}.'):
                _key_path = key_path.split(f'{category}.')[-1]
                keys = _key_path.split('.')
                leaf = keys[-1]

                # check whether key path should be wrapped
                if leaf in leaves_to_wrap:
                    sub_path = '.'.join(keys[:-1])
                    if sub_path not in content_categorised[category]:
                        content_categorised[category][sub_path] = {leaf: value}
                    else:
                        content_categorised[category][sub_path][leaf] = value
                else:
                    content_categorised[category][_key_path] = value

                found = True
                break

        if not found:
            content_categorised['root'][key_path] = value

    # write content to TOML file
    pathlib.Path(os.path.dirname(toml_file)).mkdir(parents=True, exist_ok=True)
    with open(toml_file, 'w') as f:
        for key, value in content_categorised['root'].items():
            f.write(f'{key} = {value}\n')

        for category in categories:
            f.write(f'\n[{category}]\n')
            for key, value in content_categorised[category].items():
                if isinstance(value, dict):
                    f.write(
                        f'{key} = {{ '
                        + ', '.join([f'{k} = {v}' for k, v in value.items()])
                        + ' }\n'
                    )
                else:
                    f.write(f'{key} = {value}\n')


def create_model_from_rga_gar(
        rga_file: str, gar_file: str, gardenia_version: str,
        toml_file: str = None
) -> rameau.core.Model:
    """Function to create a `Model` from legacy Gardenia RGA and GAR files.

    Parameters
    ----------
    rga_file: `str`
        Path to the Gardenia RGA file (with extension *.rga) to parse.

    gar_file: `str`
        Path to the Gardenia GAR file (with extension *.gar) to parse.

    gardenia_version: `str`
        Number of the version of the Gardenia model for which RGA/GAR
        files are to be parsed.

    toml_file: `str`, optional
        Path to the Gardenia TOML file (with extension *.toml) to create
        to store the `Model` settings. If not provided, a temporary file
        is created.

    Returns
    -------
    `rameau.core.Model`

    """
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.toml', delete=False
    ) as tmp_toml:
        toml_file = toml_file if toml_file else tmp_toml.name

        convert_rga_gar_to_toml(
            rga_file=rga_file,
            gar_file=gar_file,
            toml_file=toml_file,
            gardenia_version=gardenia_version
        )

        model = rameau.core.Model.from_toml(toml_file)

    return model
