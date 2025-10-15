# Copyright (c) Yugabyte, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations
# under the License.


from setuptools import setup  # type: ignore
from setuptools import find_packages


if __name__ == '__main__':
    # This is based on the instructions from
    # https://packaging.python.org/guides/making-a-pypi-friendly-readme/
    from os import path
    this_directory = path.abspath(path.dirname(__file__))
    with open(path.join(this_directory, 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    setup(
        name='llvm-installer',
        version='1.4.12',
        url='https://github.com/yugabyte/llvm-installer',
        author='Mikhail Bautin',
        author_email='mbautin@users.noreply.github.com',
        description='Allows installing pre-built LLVM packages for various operating systems',
        packages=find_packages(where='src'),
        package_dir={"": "src"},
        package_data={'llvm_installer': ['py.typed', 'release_tags.json']},
        install_requires=[
            'packaging',
            'sys-detection',
            'downloadutil',
        ],
        long_description=long_description,
        long_description_content_type='text/markdown',
        extras_require={
            # Following advice given in this answer: https://stackoverflow.com/a/28842733/220215
            # Install with:
            #   . venv/bin/activate
            #   pip install --editable '.[dev]'
            'dev': [
                'codecheck',
                'pycodestyle',
                'mypy',
                'PyGithub',
                'twine',
            ]
        },
        entry_points={
            'console_scripts': ['llvm-installer=llvm_installer.__main__:main'],
        }
    )
