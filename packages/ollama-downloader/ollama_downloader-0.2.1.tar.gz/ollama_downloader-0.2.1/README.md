[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=3776ab&labelColor=e4e4e4)](https://www.python.org/downloads/release/python-3120/) [![pytest](https://github.com/anirbanbasu/ollama-downloader/actions/workflows/uv-pytest.yml/badge.svg)](https://github.com/anirbanbasu/ollama-downloader/actions/workflows/uv-pytest.yml) ![GitHub commits since latest release](https://img.shields.io/github/commits-since/anirbanbasu/ollama-downloader/latest)
 [![PyPI](https://img.shields.io/pypi/v/ollama-downloader?label=pypi%20package)](https://pypi.org/project/ollama-downloader/#history)

# Ollama (library and Hugging Face) model downloader

Rather evident from the name, this is a tool to help download models for [Ollama](https://ollama.com/) including [supported models from Hugging Face](https://huggingface.co/models?apps=ollama). However, doesn't Ollama already download models from its library using `ollama pull <model:tag>`?

Yes, but wait, not so fast...!

### How did we get here?

While `ollama pull <model:tag>` certainly works, not always will you get lucky. This is a documented problem, see [issue 941](https://github.com/ollama/ollama/issues/941). The crux of the problem is that Ollama fails to pull a model from its library spitting out an error message as follows.

> `Error: digest mismatch, file must be downloaded again: want sha256:1a640cd4d69a5260bcc807a531f82ddb3890ebf49bc2a323e60a9290547135c1, got sha256:5eef5d8ec5ce977b74f91524c0002f9a7adeb61606cdbdad6460e25d58d0f454`

People have been facing this for a variety of unrelated reasons and have found specific solutions that perhaps work for only when those specific reasons exist.

[Comment 2989194688](https://github.com/ollama/ollama/issues/941#issuecomment-2989194688) in the issue thread proposes a manual way to download the models from the library. This solution is likely to work more than others.

_Hence, this tool – an automation of that manual process_!

This Ollama downloader can also _download supported models from Hugging Face_!

### Apart from `ollama pull`

Ollama's issues with the `ollama pull` command can also implicitly bite you when using `ollama create`.

As shown in the official [example of customising a prompt using a Modelfile](https://github.com/ollama/ollama?tab=readme-ov-file#customize-a-prompt), if you omit the step `ollama pull llama3.2`, then Ollama will automatically pull that model when you run `ollama create mario -f ./Modelfile`. Thus, if Ollama had issues with pulling that model, then those issues will hinder the custom model creation.

Likewise, a more obvious command that will encounter the same issues as `ollama pull` is `ollama run`, which implicitly pulls the model if it does not exist.

Thus, the safer route is to pull the model, in advance, using this downloader so that Ollama does not try to pull it implicitly (and fail at it).

### Yet another downloader?
Yes, and there exist others, possibly with different purposes.
 - [Ollama-model-downloader](https://github.com/raffaeleguidi/Ollama-model-downloader)
 - [ollama-dl](https://github.com/akx/ollama-dl)
 - [ollama-direct-downloader](https://github.com/Gholamrezadar/ollama-direct-downloader)
 - [ollama-gguf-downloader](https://github.com/olamide226/ollama-gguf-downloader)

## Installation

The directory where you clone this repository will be referred to as the _working directory_ or _WD_ hereinafter.

### Using `pip`
Although the rest of this README details the installation and usage of this downloader tool using the `uv` package manager, you can also use `pip` to install it from PyPI in a virtual environment of your choice by running `pip install ollama-downloader`. Thereafter, the scripts `od` and `ollama-downloader` will be available to you in that virtual environment.

### Using `uv` (preferred)
Install [uv](https://docs.astral.sh/uv/getting-started/installation/). To install the project with its minimal dependencies in a virtual environment, run the following in the _WD_. To install all non-essential dependencies (_which are required for developing and testing_), replace the `--no-dev` with the `--all-groups` flag in the following command.

```bash
uv sync --no-dev
```

## Configuration

There will exist, upon execution of the tool, a configuration file `conf/settings.json` in _WD_. It will be created upon the first run. However, you will need to modify it depending on your Ollama installation.

Let's explore the configuration in details. The default content is as follows.

```json
{
    "ollama_server": {
        "url": "http://localhost:11434",
        "api_key": null,
        "remove_downloaded_on_error": true
    },
    "ollama_library": {
        "models_path": "~/.ollama/models",
        "registry_base_url": "https://registry.ollama.ai/v2/library/",
        "library_base_url": "https://ollama.com/library",
        "verify_ssl": true,
        "timeout": 120.0,
        "user_group": null
    }
}
```

There are two main configuration groups: `ollama_server` and `ollama_library`. The former refers to the server for which you wish to download the model. The latter refers to the Ollama library where the model and related information ought to be downloaded from.

### `ollama_server`

 - The `url` points to the HTTP endpoint of your Ollama server. While the default is http://localhost:11434, note that your Ollama server may actually be running on a different machine, in which case, the URL will have to point to that endpoint correctly.
 - The `api_key` is only necessary if your Ollama server endpoint expects an API key to connect, which is typically not the case.
 - The `remove_downloaded_on_error` is a boolean flag, typically set to `true`. This helps specify whether this downloader tool should remove downloaded files (including temporary files) if it fails to connect to the Ollama server or fails to find the downloaded model.

### `ollama_library`

 - The `models_path` points to the models directory of your Ollama installation. On Linux/UNIX systems, if it has been installed for your own user only then the path is the default `~/.ollama/models`. If it has been installed as a service, however, it could be, for example on Ubuntu 22.04, `/usr/share/ollama/.ollama/models`. Also note that the path could be a network share, if Ollama is on a different machine.
 - The `registry_base_url` is the URL to the Ollama registry. Unless you have a custom Ollama registry, use the default value as shown above.
 - Likewise, the `library_base_url` is the URL to the Ollama library. Keep the default value unless you really need to point it to some mirror.
 - The `verify_ssl` is a flag that tells the downloader tool to verify the authenticity of the HTTPS connections it makes to the Ollama registry or the library. Turn this off only if you have a man-in-the-middle proxy with self-signed certificates. Even in that case, typically environment variables `SSL_CERT_FILE` and `SSL_CERT_DIR` can be correctly configured to validate such certificates.
 - The self-explanatory `timeout` specifies the number of seconds to wait before any HTTPS connection to the Ollama registry or library should be allowed to fail.
 - The `user_group` is a specification of the _user_ and the _group_ (as a tuple, e.g., `"user_group": ["user", "group"]`) that owns the path specified by `models_path`. If, for instance, your local Ollama is a service and its model path is `/usr/share/ollama/.ollama/models` then, in order to write to that path, you must run this downloader as _root_. However, the ownership of file objects in that path must be assigned to the user _ollama_ and group _ollama_. If your model path is on a writable network share then you most likely need not specify the user and group.

## Environment variables

All the environment variables, listed below, are _optional_. If not specified, their default values will be used.

| Variable           | Description and default value(s)                                     |
|--------------------|----------------------------------------------------------------------|
| `LOG_LEVEL`        | The level to be set for the logger. Default value is `INFO`. See all valid values in [Python 3 logging documentation](https://docs.python.org/3/library/logging.html#levels).|
| `OD_SETTINGS_FILE` | The name of the settings file. Default value is `conf/settings.json` relative to the _WD_.|
| `OD_UA_NAME_VER`   | The application name and version to be prepended to the User-Agent header when making HTTP(S) requests. Default value is `ollama-downloader/0.1.0`.|

## Usage
The preferred way to run this downloader is using the `od` script, such as `uv run od --help`, or `od --help`, if you installed the downloader using `pip`. The script `ollama-downloader` is also available and is an alias of `od`.

However, if you need to run it with superuser rights (i.e., using `sudo`) for model download then you should install the script in the `uv` created virtual environment by running `uv pip install -e .`, or install the `ollama-downloader` package from PyPI in a virtual environment. Then you can invoke it as `sudo .venv/bin/od --help` (assuming that your virtual environment exists in `.venv`).

The `od` script provides the following commands. All its commands can be listed by running `uv run od --help`.

```bash
Usage: od [OPTIONS] COMMAND [ARGS]...

 A command-line interface for the Ollama downloader.

╭─ Options ────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────╮
│ version             Shows the app version of Ollama downloader.                          │
│ show-config         Shows the application configuration as JSON.                         │
│ auto-config         Displays an automatically inferred configuration.                    │
│ list-models         Lists all available models in the Ollama library. If pagination      │
│                     options are not provided, all models will be listed.                 │
│ list-tags           Lists all tags for a specific model.                                 │
│ model-download      Downloads a specific Ollama model with the given tag.                │
│ hf-list-models      Lists available models from Hugging Face that can be downloaded into │
│                     Ollama.                                                              │
│ hf-list-tags        Lists all available quantisations as tags for a Hugging Face model   │
│                     that can be downloaded into Ollama. Note that these are NOT the same │
│                     as Hugging Face model tags.                                          │
│ hf-model-download   Downloads a specified Hugging Face model.                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

You can also use `--help` on each command to see command-specific help.

### `version`

The `version` command displays the application version.

Running `uv run od version --help` displays the following.

```bash
Usage: od version [OPTIONS]

 Shows the app version of Ollama downloader.

╭─ Options ────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

### `show-config`

The `show-config` command simply displays the current configuration from the settings file in the configurations directory, if it exists. If it does not exist, it creates that file with the default settings and shows the content of that file.

Running `uv run od show-config --help` displays the following.

```bash
Usage: od show-config [OPTIONS]

 Shows the application configuration as JSON.


╭─ Options ────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────╯
```

### `auto-config`

The `auto-config` command is **experimental** to display the inferred configuration for the variables `ollama_server.url`, `ollama_library.models_path` and `ollama_library.user_group`.

_Note that the `auto-config` output may be wrong. Use with caution!_

Running `uv run od auto-config --help` displays the following.

```bash
Usage: od auto-config [OPTIONS]

 Display an automatically inferred configuration.


╭─ Options ────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────╯
```

### `list-models`

The `list-models` command displays an up-to-date list of models that exist in the Ollama library. _Note that unlike the pagination options for Hugging Face, the entire model list from the Ollama library is fetched and then pagination is applied locally_.

Running `uv run od list-models --help` displays the following.

```bash
Usage: od list-models [OPTIONS]

 Lists all available models in the Ollama library. If pagination options are not provided,
 all models will be listed.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────╮
│ --page             INTEGER RANGE [x>=1]       The page number to retrieve (1-indexed).     │
│ --page-size        INTEGER RANGE [1<=x<=100]  The number of models to retrieve per page.   │
│ --help                                        Show this message and exit.                  │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```
### `list-tags`

The `list-tags` command shows the tags available for a specified model in the Ollama library.

Running `uv run od list-tags --help` displays the following.

```bash
Usage: od list-tags [OPTIONS] MODEL_IDENTIFIER

 Lists all tags for a specific model.


╭─ Arguments ─────────────────────────────────────────────────────────────────╮
│ *    model_identifier      TEXT  The name of the model to list tags for,    │
│                                  e.g., llama3.1.                            │
│                                  [default: None]                            │
│                                  [required]                                 │
╰─────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────╯
```
### `model-download`

The `model-download` downloads the specified model and its tag from the Ollama library.

During the process of downloading, the following are performed.

1. Validation of the manifest for the specified model and tag.
2. Validation of the SHA256 hash of each downloaded BLOB.
3. Post-download verification with the Ollama server specified by `ollama_server.url` in the configuration that the downloaded model is available.

As an example, run `uv run od model-download all-minilm` to download the `all-minilm:latest` embedding model. _Note that if not specified, the tag is assumed to be `latest`_. Specify a tag as `<model>:<tag>`. For instance, run `uv run od model-download llama3.2:3b` to download the `llama3.2` model with the `3b` tag.

Running `uv run od model-download --help` displays the following.

```bash
Usage: od model-download [OPTIONS] MODEL_TAG

 Downloads a specific Ollama model with the given tag.


╭─ Arguments ──────────────────────────────────────────────────╮
│ *    model_tag      TEXT  The name of the model and a        │
│                           specific to download, specified as │
│                           <model>:<tag>, e.g.,               │
│                           llama3.1:8b. If no tag is          │
│                           specified, 'latest' will be        │
│                           assumed.                           │
│                           [default: None]                    │
│                           [required]                         │
╰──────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────╯
```

The following screencast shows the process of downloading the model `all-minilm:latest` on a machine running Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-60-generic x86_64) with Ollama installed as a service. Hence, the command `sudo .venv/bin/od model-download all-minilm` was used.

_Notice that there are warnings that SSL verification has been disabled. This is intentional to illustrate the process of downloading through a HTTPS proxy (picked up from the `HTTPS_PROXY` environment variable) that has self-signed certificates_.

![demo-model-download](https://raw.githubusercontent.com/anirbanbasu/ollama-downloader/master/screencasts/demo_model_download.gif "model-download demo")

### `hf-model-download`

The `hfmodel-download` downloads the specified model from Hugging Face.

During the process of downloading, the following are performed.

1. Validation of the manifest for the specified model for the specified repository and organisation. _Note that not all Hugging Face models have the necessary files that can be downloaded into Ollama automatically._
2. Validation of the SHA256 hash of each downloaded BLOB.
3. Post-download verification with the Ollama server specified by `ollama_server.url` in the configuration that the downloaded model is available.

As an example, run `uv run od hf-model-download unsloth/gemma-3-270m-it-GGUF:Q4_K_M` to download the `gemma-3-270m-it-GGUF:Q4_K_M` model from `unsloth`, the details of which can be found at https://huggingface.co/unsloth/gemma-3-270m-it-GGUF.

Running `uv run od hf-model-download --help` displays the following.

```bash
Usage: od hf-model-download [OPTIONS] USER_REPO_QUANT

 Downloads a specified Hugging Face model.


╭─ Arguments ───────────────────────────────────────────────────────────────────╮
│ *    user_repo_quant      TEXT  The name of the specific Hugging Face model   │
│                                 to download, specified as                     │
│                                 <username>/<repository>:<quantisation>, e.g., │
│                                 bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M.  │
│                                 [default: None]                               │
│                                 [required]                                    │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                   │
╰───────────────────────────────────────────────────────────────────────────────╯
```

### `hf-list-models`

The `hf-list-models` lists available available Hugging Face models that can be downloaded into Ollama.

Running `uv run od hf-list-models --help` displays the following.

```bash
Usage: od hf-list-models [OPTIONS]

 Lists available models from Hugging Face that can be downloaded into Ollama.

╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --page             INTEGER RANGE [x>=1]       The page number to retrieve             │
│                                               (1-indexed).                            │
│                                               [default: 1]                            │
│ --page-size        INTEGER RANGE [1<=x<=100]  The number of models to retrieve per    │
│                                               page.                                   │
│                                               [default: 25]                           │
│ --help                                        Show this message and exit.             │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

_Note that due to the lack of offset-based paging support in the Hugging Face Hub API, the results will be limited to a certain maximum number (e.g., 100) models only with a link provided to browse through the full list. The message with the link will be displayed only if the `LOG_LEVEL` is set to `WARNING` or more verbose._

### `hf-list-tags`

The `hf-list-tags` lists available quantisations as tags for a specified Hugging Face model that can be downloaded into Ollama.

Running `uv run od hf-list-tags --help` displays the following.

```bash
Usage: od hf-list-tags [OPTIONS] MODEL_IDENTIFIER

 Lists all available quantisations as tags for a Hugging Face model that can
 be downloaded into Ollama. Note that these are NOT the same as Hugging Face
 model tags.


╭─ Arguments ─────────────────────────────────────────────────────────────────╮
│ *    model_identifier      TEXT  The name of the model to list tags for,    │
│                                  e.g.,                                      │
│                                  bartowski/Llama-3.2-1B-Instruct-GGUF.      │
│                                  [default: None]                            │
│                                  [required]                                 │
╰─────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────╯
```

## Testing, coverage and profiling

To run the provided set of tests using `pytest`, execute the following in _WD_. Append the flag `--capture=tee-sys` to the following command to see the console output during the tests. Note that the model download tests run as sub-processes. Their outputs will not be visible by using this flag.

```bash
uv run --group test pytest tests/
```

To get a report on coverage while invoking the tests, run the following two commands.

```bash
uv run --group test coverage run -m pytest tests/
uv run coverage report
```

This will result in an output similar to the following.

```bash
Name                                                          Stmts   Miss  Cover
---------------------------------------------------------------------------------
src/ollama_downloader/__init__.py                                18      3    83%
src/ollama_downloader/cli.py                                    194     21    89%
src/ollama_downloader/data/__init__.py                            0      0   100%
src/ollama_downloader/data/data_models.py                        86     19    78%
src/ollama_downloader/downloader/__init__.py                      0      0   100%
src/ollama_downloader/downloader/hf_model_downloader.py          90      6    93%
src/ollama_downloader/downloader/model_downloader.py            167     43    74%
src/ollama_downloader/downloader/ollama_model_downloader.py      91      9    90%
src/ollama_downloader/sysinfo.py                                115     20    83%
tests/__init__.py                                                 0      0   100%
tests/test_data_models.py                                        33      1    97%
tests/test_system_info.py                                        54      0   100%
tests/test_typer.py                                              78      0   100%
---------------------------------------------------------------------------------
TOTAL                                                           926    122    87%
```

There is a handy script for running tests `run_tests.sh` in _WD_. It can accept any parameters to be passed to `pytest`. Thus, tests can be filtered using the `-k` to specify tests to run or not. Likewise, profiling can be done by calling `./run_tests.sh --profile`. The resulting profile information will be generated and saved in _WD_`/prof`. A SVG of the complete profile can be generated by calling `./run_tests.sh --profile --profile-svg`.

Profile information can also be filtered and a SVG of the filtered profile generated by editing the somewhat hacky script _WD_`/tests/filter_profile_data.py`.
The script can be run using `uv` as `uv run tests/filter_profile_data.py`.

## Native compilation and execution

This is an _experimental feature_ by which Ollama downloader can be compiled into a single executable binary file -- `od-native` -- using [Nuitka](https://nuitka.net/). To compile the native binary on your platform, run the script `./compile_native.sh`. Notice that you must have the `dev` group dependencies of the project installed.

_Note that having a `.env` file may cause the natively compiled binary to crash, with an error message `OSError: Starting path not found`._ Should you want to pass any of the environment variables to the executable, do so using the command line interface.

Once the native executable has been created, run it from the command line interface as `./od-native` on UNIX/Linux systems and simply `od-native` on Windows. The native executable may have executable file type extension (`.exe`) on Windows.

_Note that the natively compiled binary is unlikely to be significantly faster than the Python code that you can execute using `uv`_. After all, the bottleneck in most of the operations in Ollama downloader is more likely to be the network speed as opposed to code execution speed.

## Installation on macOS and Linux using Homebrew

Ollama downloader can be installed on macOS and Linux using Homebrew so that the installation of Python and the management of a virtual environment is all done by Homebrew leaving a single command `ollama-downloader` available on the command line interface.

To do so, add the new tap by running: `brew tap anirbanbasu/tap`. Then, Ollama downloader can be installed using `brew install ollama-downloader`.

## Contributing

Install [`pre-commit`](https://pre-commit.com/) for Git by using the `--all-groups` flag for `uv sync`.

Then enable `pre-commit` by running the following in the _WD_.

```bash
pre-commit install
```
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/).
