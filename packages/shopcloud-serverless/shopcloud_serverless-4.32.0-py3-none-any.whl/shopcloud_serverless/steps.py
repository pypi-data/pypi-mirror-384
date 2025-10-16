import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from . import exceptions, helpers
from .configs import Config


class Step:
    def __init__(self):
        pass

    def run(self, config: Config, simulate: bool = False):
        raise NotImplementedError()


class StepCreatDir(Step):
    def __init__(self, path: str):
        self.path = path

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Creating {self.path} directory')
        if not Path(self.path).exists():
            Path(self.path).mkdir(parents=True, exist_ok=True)


class StepDeleteDir(Step):
    def __init__(self, path: str):
        self.path = path

    def run(self, config: Config, simulate: bool = False):
        if not Path(self.path).exists():
            return None
        print(f'+ Deleting {self.path} directory')
        shutil.rmtree(self.path)


class StepCopyFileContent(Step):
    def __init__(self, file_a_path: str, file_b_path: str):
        self.file_a_path = file_a_path
        self.file_b_path = file_b_path

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Copy {self.file_a_path} to {self.file_b_path}')
        with open(self.file_a_path) as fr:
            with open(self.file_b_path, "w") as fw:
                fw.write(fr.read())


class StepAppendFileContent(Step):
    def __init__(self, file_path: str, content: List[str]):
        """
        Initialize a new instance of the class.

        Args:
            file_path (str): The path of the file to append content to.
            content (List[str]): The content to be appended to the file as a list of strings.

        """
        self.file_path = file_path
        self.content = content

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Append to {self.file_path}')
        with open(self.file_path, "a") as f:
            f.write("\n".join(self.content))


class StepCreateFile(Step):
    def __init__(self, file_path: str, content: str):
        """
        Initialize a new instance of the class.

        Args:
            file_path (str): The path of the file to be created.
            content (str): The content to be written to the file.

        """
        self.file_path = file_path
        self.content = content

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Append to {self.file_path}')
        with open(self.file_path, "w") as f:
            f.write(self.content)


class StepCopyDir(Step):
    def __init__(self, path_a: str, path_b: str):
        """
        Initialize a new instance of the class.

        Args:
            path_a (str): The source directory path to be copied.
            path_b (str): The destination directory path.

        """
        self.path_a = path_a
        self.path_b = path_b

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Copy {self.path_a} to {self.path_b}')
        shutil.copytree(self.path_a, self.path_b)


class StepCommand(Step):
    def __init__(self, command: List[str], **kwargs):
        """
        The StepCommand class represents a step that executes a command. It takes a command as a list of strings and supports optional configuration options such as the working directory, failure tolerance, retries, and verbosity. The run method executes the command, capturing the output and handling failure scenarios based on the configuration provided.

        Args:
            command (List[str]): The command to be executed.
            **kwargs: Additional keyword arguments.

        Keyword Args:
            work_dir (str): The working directory for the command execution.
            can_fail (bool): Flag indicating if the command is allowed to fail (default: False).
            retry (int): Number of times to retry the command execution (default: 0).
            verbose (bool): Flag indicating if verbose output should be enabled (default: False).
        """
        self.command = command
        self.work_dir = kwargs.get('work_dir')
        self.can_fail = kwargs.get('can_fail', False)
        self.retry = kwargs.get('retry', 0)
        self.verbose = kwargs.get('verbose', False)
        self.is_async = kwargs.get('is_async', True)

    def run(self, config: Config, simulate: bool = False):
        print('+ Run command:')
        print(" ".join(self.command))
        if not simulate:
            while True:
                count = 0
                p = subprocess.Popen(
                    self.command,
                    cwd=self.work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if self.is_async:
                    while True:
                        output = p.stdout.readline()
                        if output == '' and p.poll() is not None:
                            break
                        if output:
                            print(output.strip().decode(sys.stdout.encoding))
                        error = p.stderr.readline()
                        if error:
                            print(error.strip().decode(sys.stderr.encoding))
                else:
                    stdout, stderr = p.communicate()
                    print(stdout.strip().decode(sys.stdout.encoding))
                    print(stderr.strip().decode(sys.stderr.encoding))
                    p.wait()
                if not self.can_fail:
                    if p.returncode != 0:
                        if count < self.retry:
                            count += 1
                            continue
                        raise exceptions.CommandError('command not success')
                break


class StepFunction(Step):
    def __init__(self, name: str, function):
        self.name = name
        self.function = function

    def run(self, config: Config, simulate: bool = False):
        print(f'+ Run {self.name}')
        self.function(config)


class Manager:
    def __init__(self, config: Config, steps: list, **kwargs):
        self.config = config
        self.steps = steps
        self.simulate = kwargs.get('simulate', False)

    def run(self) -> int:
        if self.simulate:
            print(helpers.bcolors.WARNING + '+ Simulate' + helpers.bcolors.ENDC)
        for step in self.steps:
            try:
                step.run(self.config, self.simulate)
            except Exception as e:
                print(helpers.bcolors.FAIL + f'ERROR: {e}' + helpers.bcolors.ENDC)
                return 1
        return 0
