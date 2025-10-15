# artof

The artof package is a jupyter notebook tool to read, process and analyze data collected from angle resolved time of flight (ARTOF) sensors.

## Getting started

To use this package python version >=3.10 is needed. The installation can be done using the command:

```bash
pip install artof
```

## Documentation

The documentation can be found [here](https://artof-42d889.pages.hzdr.de/main/). It is automatically
generated from the docstrings in all python classes.

## Workflow

The implementation of a new feature should be conducted as follows:

1. Create a new branch with a sensible name as a fork from `dev`.
2. Implement features including documentation.
3. If required, make changes to the Sphinx documentation under `docs/source/`.
4. Check if all existing tests are still working (cmd: `pytest`) and write new test functions.
5. If there were changes to `dev` since the initial fork, merge it into your branch and resolve
   conflicts. Check again if all tests are running.
6. Make sure the pylint rating of each file is 8 or higher. To do so run

```bash
pylint src/artof/{file}
```

7. Update documentation in the `./docs` folder using `.rst` and `sphinx`. For automatic doc
   generation use `.. automodule:: artof.{module}` or `.. autoclass:: artof.{module}.{class}`. Do
   not forget to add new `.rst`-files to index.
8. Test the doc generation and ensure there are no warnings (else the pipeline will fail). To do
   so run

```bash
sphinx-build -M html docs/source docs/build
```

9. Increase version number in `setup.cfg` and `CITATION.cff` file.
10. Push all changes to the remote repository and create a merge request to `dev`.
11. Make sure all tests succeed in the pipeline and merge.
12. When enough changes accumulate, create a merge request to `main` once enough features
    accumulated
    to roll out a new version. Make again sure all test pipelines succeed.
13. After merging to `main` a new version of the package is released to PyPi upon a successful
    pipeline run.

## Major releases
In case of major releases, it is recommended to deploy seperate version for the docs, that will be available in the future. To do so, add a new entry to the `versions.json`-file (root directory).
```json 
[
    {
        "name": "latest (main)",
        "version": "main",
        "url": "https://artof-42d889.pages.hzdr.de/main/"
    },
    {
        "name": "testing (dev)",
        "version": "dev",
        "url": "https://artof-42d889.pages.hzdr.de/dev/"
    },  
    ...  
    {
        "name": "vx.x.x",
        "version": "vx.x.x",
        "url": "https://artof-42d889.pages.hzdr.de/vx.x.x/"
    },
]
```
After getting this version merged onto the main branch, add a tag to the according commit with the exact name of the version (`vx.x.x`). A new page deployment will be run automatically.

## Issues and new features

Issues and new feature requests can be
added [here](https://codebase.helmholtz.cloud/carl.meier/artof/-/issues).

## Development version

A version with features under development is available under the TestPyPi repository and can be
installed as followed:

```bash
pip install --index-url https://test.pypi.org/simple/ artof
```

The documentation can be found [here](https://artof-42d889.pages.hzdr.de/dev/).

## Terminology
General
- Iteration: One full measurements cycle
- Step/Frame: Step within one iteration
- Window:
- Trigger period: Time between two triggers. Usually the trigger is synched to revolution period (BESSY, approx. 800 ns / 32000 ticks). 

Pump probe
- Run: Individual run, where settings like f.e. the delay stage or oscillator delay have been changed. 
- Revolution: Revolutions of the synchrotron, which range from -1 to 205. Revolution 0 is the revolution of the pumb pulse.
- Revolution period: Average time between two revolutions, often given in TDC ticks. (BESSY, approx. 800 ns / 32000 ticks)

