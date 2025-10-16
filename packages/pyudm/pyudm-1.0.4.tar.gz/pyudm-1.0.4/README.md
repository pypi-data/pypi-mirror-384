# Unified Dependency Manager

Unified Dependency Manager is a simple yet powerful tool aimed at simplifying dependency handling of nested projects and vcs interoperability.

This tool lets users define the dependencies of each project in a simple and clean fashion inspired by svn:externals workflow and performs all the routine operations needed to checkout, update and track supbrojects.

Dependecies can be defined in the specific file `.deps.udm` as a list of arguments such as destination folder, repository URL and other optional parameters.
Currently, both svn and git repositories can be used as dependencies. Also, udm implements a feature that automatically converts the dependency defenitions for projects that already use svn externals or git submodules (see `convert` command below).

[Git externals](https://github.com/develer-staff/git-externals) syntax is supported for conversion as well.

## Usage example

Create a deps file named `.deps.udm` in your main repository root folder, for example:
```yaml
lib/libraryA:
  url: https://gitlab.com/test/libraryA

lib/libraryB:
  url: https://gitlab.com/test/libraryB
  tag: 1.0.0
  path: src/

lib/libraryC:
  url: http://repository.com/svn/projects/libraryC
  branch: release

lib/libraryD:
  url: git@gitlab.com:user/mylib
  commit: 82749DE4
  options:
    - "--sparse"
    - "--depth"
    - 1
```

Then simply run `udm udpate`: it will create the dependecy subfolders and checkout/clone all the repositories inside as specified in the deps file. Note: this will update/pull the main repository as well, unless the argument `--only-deps` is given.

To later integrate remote changes performed on the depency repositories run `udm udpate` again.

See the list of commands below for more details and advanced uses.

## Installation

Quick method:

```sh
pip install pyudm
```

If you want to make changes you can also checkout this repository and from its root directory run
```sh
pip install -e .
```
to install the development version of the package respoinding to local changes dynamically.

## Main commands

Udm operation is performed by main executable subcommands, each subcommand has its function and may have specific flags. 
Global flags applying to each subcommand must be passed before the subcommand itself and are:
* `--prohibit-externals`: stop execution at the first repository containing svn externals or git submodules
* `--ignpore-deps`: perform operation only on current repo, do not traverse dependencies
* `--force`: forces possibly harmful operations
* `--no-color`: disable colored output (usefull if run in scripts or when capturing output)
* `--quiet`: run in quiet mode suppressing all output except error messages
* `--version`: print version information and exit

Each subcommand, as well as the root executable, expose usage information through the `-h` or `--help` flags.

### `clone` (also `checkout` or `co`)
Clone a repository and its dependencies into a new directory. By passing the `--convert` argument, `udm` will automatically create the `.deps.udm` file based on the existing definitions of svn externals or git submodules.

usage:
```sh
udm clone [-h] [--convert] url destination
```

### `update` (also `up` or `pull`)
Fetch and integrate changes from the remote repository. The update action is also perfomed on dependecy repositories by default.

usage:
```sh
udm update [-h] [--only-deps] [--no-deps]
```

### `convert`
Create the `.deps.udm` file based on the existing definitions of svn externals or git submodules. If `--no-update` argument is specified, only create the `.deps.udm` file, otherwise the creation will automatically be followed by an update operation.

usage:
```sh
udm convert [-h] [--no-update]
```

### `status` (also `st` or `stat`)
Print the status of the main repository and its dependencies.

usage:
```sh
udm status [-h]
```

### `edit-deps` (also `ed`)
Open the file of dependencies with the default editor or with the specified one.

usage:
```sh
udm edit-deps [-h] [--editor-cmd EDITOR]
```

### `ls-files` (also `ls`)
List tracked files of the main repository and its dependencies.

usage:
```sh
udm ls-files [-h]
```

### `ls-deps` (also `show` or `deps`)
List configured dependencies with remote tracking info

usage:
```sh
udm ls-deps [-h]
```

### `local` (also `l`)
Pass additional arguments directly to local repository structure, print local repository type if no argument is specified.

usage:
```sh
udm local [-h]
```

## Dependencies file

The dependencies file `.deps.udm` follows yaml syntax and is a root mapping where each key/value pair represents a dependency of the project.
The keys are the paths relative to the directory containing the `.deps.udm` file where the dependency will be checked out, the value is a mapping with the folowing fields:
* `url` (_mandatory_): the url of the dependency remote repository
* `tag`: checkout a specific tag, tag name for git repositories, folder name inside `^/tags` for svn repositories
* `commit`: specific commit/revision, commit hash for git repositories, revision number for svn repositories
* `branch`: desired branch (track branch head), branch name for git repositories, folder name inside `^/branches` for svn repositories
* `path`: remote path to checkout, perform a sparse checkout for git repositories, checkout subpath for svn repositories
* `options`: additional options to pass to git/svn when performing checkout/update operations

If no `tag`, `commit` or `branch` option is selected, the dependency will track latest commit in default branch for git repositories or `^/trunk` for svn repositories.

See [Usage example](#usage-example) for an example.

## Configurations

Configuration files can be used to set default values for all commandline flags. Configuration files are in yaml syntax and are read from various locations:
1. `/etc/udm.conf`
2. `/etc/default/udm.conf`
3. `~/.config/udm.conf`
4. `~/.udm.conf`

If any of these files is found, it will be read overriding the previously obtained values, thus giving priority to the files in the user home.

These files are yaml mappings where each key is the name of a commandline flag, a default config file with current commandline default values is:
```yaml
force: false
quiet: false
no-color: false

prohibit-externals: false
ignore-deps: false

convert: false
no-update: false

no-deps: false
only-deps: false

editor-cmd: null
```

## License

Distributed under the GNU GPLv2 license. See ``LICENSE`` for more information.

## Contributing

See `CONTRIBUTING.md`.
