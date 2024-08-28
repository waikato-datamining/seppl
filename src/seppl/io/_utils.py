import glob
import os

from typing import Union, List


def locate_files(inputs: Union[str, List[str]], input_lists: Union[str, List[str]] = None,
                 recursive: bool = False, fail_if_empty: bool = False, default_glob: str = None) -> List[str]:
    """
    Locates all the files from the specified inputs, which may contain globs.
    glob results get sorted to ensure the same file order each time.
    If default_glob is not None and the inputs are pointing to directories, then default_glob
    gets appended.

    :param inputs: the input path(s) with optional globs
    :type inputs: str or list
    :param input_lists: text file(s) that list the actual input files to use
    :type input_lists: str or list
    :param recursive: for supporting recursive globs
    :type recursive: bool
    :param fail_if_empty: whether to throw an exception if no files were located
    :type fail_if_empty: bool
    :param default_glob: the default glob to use, ignored if None
    :type default_glob: str
    :return: the expanded list of files
    :rtype: list
    """
    if (inputs is None) and (input_lists is None):
        raise Exception("Neither input paths nor input lists provided!")

    if inputs is not None:
        if isinstance(inputs, str):
            inputs = [inputs]
        elif isinstance(inputs, list):
            inputs = inputs
        else:
            raise Exception("Invalid inputs, must be string(s)!")

        if default_glob is not None:
            for i, inp in enumerate(inputs):
                if os.path.isdir(inp):
                    inputs[i] = os.path.join(inp, default_glob)

    if input_lists is not None:
        if isinstance(input_lists, str):
            input_lists = [input_lists]
        elif isinstance(input_lists, list):
            input_lists = input_lists
        else:
            raise Exception("Invalid input lists, must be string(s)!")

    result = []

    # globs
    if inputs is not None:
        for inp in inputs:
            for f in sorted(glob.glob(inp, recursive=recursive)):
                if os.path.isdir(f):
                    continue
                result.append(f)

    # path lists
    if input_lists is not None:
        for inp in input_lists:
            if not os.path.exists(inp):
                print("WARNING: Input list does not exist: %s" % inp)
                continue
            if os.path.isdir(inp):
                print("WARNING: Input list points to directory: %s" % inp)
                continue
            with open(inp, "r") as fp:
                lines = [x.strip() for x in fp.readlines()]
            for line in lines:
                if not os.path.exists(line):
                    print("WARNING: Path from input list '%s' does not exist: %s" % (inp, line))
                    continue
                result.append(line)

    if fail_if_empty and (len(result) == 0):
        raise Exception("Failed to locate any files using: %s" % str(inputs))

    return result
