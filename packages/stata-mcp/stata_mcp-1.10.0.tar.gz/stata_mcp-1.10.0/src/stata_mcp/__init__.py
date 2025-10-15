import os
import platform
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import dotenv
from mcp.server.fastmcp import FastMCP, Image
from packaging.version import Version
from pydantic_core._pydantic_core import ValidationError

from .__version__ import __version__
from .core.data_info import CsvDataInfo, DtaDataInfo
from .core.stata import StataController, StataDo, StataFinder
from .utils.Prompt import pmp

__author__ = "Song Tan <sepine@statamcp.com>"

dotenv.load_dotenv()

mcp_version = Version(version('mcp'))

try:
    from mcp.server.fastmcp import Icon

    # Use different logic for init MCP Server
    if mcp_version >= Version("1.16.0"):
        # v1.16.0 requires icons-sizes as list[str]
        stata_mcp = FastMCP(
            name="stata-mcp",
            instructions="Stata-MCP lets you and LLMs can run Stata do-file and fetch the results",
            website_url="https://www.statamcp.com",
            icons=[Icon(
                src="https://r2.statamcp.com/android-chrome-512x512.png",
                mimeType="image/png",
                sizes=["512x512"]
            )]
        )
    elif mcp_version == Version("1.15.0"):
        # v1.15.0 requires icons-sizes as str | None
        stata_mcp = FastMCP(
            name="stata-mcp",
            instructions="Stata-MCP lets you and LLMs can run Stata do-file and fetch the results",
            website_url="https://www.statamcp.com",
            icons=[Icon(
                src="https://r2.statamcp.com/android-chrome-512x512.png",
                mimeType="image/png",
                sizes="512x512"
            )]
        )
    else:
        # Before v1.15.0, there is not a option named icons, just use the minimal config.
        print(f"Suggest upgrade your mcp version to v{mcp_version}")
        stata_mcp = FastMCP(name="stata-mcp")
except ValidationError as e:
    print(f"Unknown Error: {e}\nTry to use non-config way.")
    try:
        stata_mcp = FastMCP()
    except ValidationError as e:
        print(f"Still error: {e}! \nIf you need help, leave issues on https://github.com/sepinetam/stata-mcp/issues")
        sys.exit(1)


# Initialize optional parameters
SYSTEM_OS = platform.system()

# Determine documents path
if SYSTEM_OS in ["Darwin", "Linux"]:
    documents_path = os.getenv(
        "documents_path",
        os.path.expanduser("~/Documents")
    )
elif SYSTEM_OS == "Windows":
    documents_path = os.getenv(
        "documents_path",
        os.path.join(os.getenv("USERPROFILE", "~"), "Documents"),
    )
else:
    # Here, if unknown system -> exit.
    sys.exit("Unknown System")

# Use configured output path if available
output_base_path = os.path.join(documents_path, "stata-mcp-folder")
os.makedirs(output_base_path, exist_ok=True)  # make sure this folder exists

try:
    # find stata_cli, env first, then default path
    finder = StataFinder()
    STATA_CLI = finder.find_stata(os_name=SYSTEM_OS, is_env=True)
except FileNotFoundError as e:
    sys.exit(str(e))

# Create a series of folder
log_base_path = os.path.join(output_base_path, "stata-mcp-log")
os.makedirs(log_base_path, exist_ok=True)
dofile_base_path = os.path.join(output_base_path, "stata-mcp-dofile")
os.makedirs(dofile_base_path, exist_ok=True)
result_doc_path = os.path.join(output_base_path, "stata-mcp-result")
os.makedirs(result_doc_path, exist_ok=True)

tmp_base_path = os.path.join(output_base_path, "stata-mcp-tmp")
os.makedirs(tmp_base_path, exist_ok=True)

lang = os.getenv("lang", "en")
if lang not in ["en", "cn"]:
    lang = "en"  # Default to English if not set or invalid
pmp.set_lang(lang)


@stata_mcp.prompt()
def stata_assistant_role(lang: str = None) -> str:
    """
    Return the Stata assistant role prompt content.

    This function retrieves a predefined prompt that defines the role and capabilities
    of a Stata analysis assistant. The prompt helps set expectations and context for
    the assistant's behavior when handling Stata-related tasks.

    Args:
        lang (str, optional): Language code for localization of the prompt content.
            If None, returns the default language version. Defaults to None.
            Examples: "en" for English, "cn" for Chinese.

    Returns:
        str: The Stata assistant role prompt text in the requested language.

    Examples:
        >>> stata_assistant_role()  # Returns default language version
        "I am a Stata analysis assistant..."

        >>> stata_assistant_role(lang="en")  # Returns English version
        "I am a Stata analysis assistant..."

        >>> stata_assistant_role(lang="cn")  # Returns Chinese version
        "我是一个Stata分析助手..."
    """
    return pmp.get_prompt(prompt_id="stata_assistant_role", lang=lang)


@stata_mcp.prompt()
def stata_analysis_strategy(lang: str = None) -> str:
    """
    Return the Stata analysis strategy prompt content.

    This function retrieves a predefined prompt that outlines the recommended
    strategy for conducting data analysis using Stata. The prompt includes
    guidelines for data preparation, code generation, results management,
    reporting, and troubleshooting.

    Args:
        lang (str, optional): Language code for localization of the prompt content.
            If None, returns the default language version. Defaults to None.
            Examples: "en" for English, "cn" for Chinese.

    Returns:
        str: The Stata analysis strategy prompt text in the requested language.

    Examples:
        >>> stata_analysis_strategy()  # Returns default language version
        "When conducting data analysis using Stata..."

        >>> stata_analysis_strategy(lang="en")  # Returns English version
        "When conducting data analysis using Stata..."

        >>> stata_analysis_strategy(lang="cn")  # Returns Chinese version
        "使用Stata进行数据分析时，请遵循以下策略..."
    """
    return pmp.get_prompt(prompt_id="stata_analysis_strategy", lang=lang)


# As AI-Client does not support Resource at a board yet, we still keep the prompt
@stata_mcp.resource(
    uri="help://stata/{cmd}",
    name="help",
    description="Get help for a Stata command"
)
@stata_mcp.prompt(name="help", description="Get help for a Stata command")
@stata_mcp.tool(name="help", description="Get help for a Stata command")
def help(cmd: str) -> str:
    """
    Execute the Stata 'help' command and return its output.

    Args:
        cmd (str): The name of the Stata command to query, e.g., "regress" or "describe".

    Returns:
        str: The help text returned by Stata for the specified command,
             or a message indicating that no help was found.
    """
    controller = StataController(STATA_CLI)
    std_error_msg = (
        f"help {cmd}\r\n"
        f"help for {cmd} not found\r\n"
        f"try help contents or search {cmd}"
    )
    help_result = controller.run(f"help {cmd}")

    if help_result != std_error_msg:
        return help_result
    else:
        return "No help found for the command: " + cmd


@stata_mcp.tool(
    name="read_file",
    description="Reads a file and returns its content as a string"
)
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The full path to the file to be read.
        encoding (str, optional): The encoding used to decode the file. Defaults to "utf-8".

    Returns:
        str: The content of the file as a string.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    try:
        with open(file_path, "r", encoding=encoding) as file:
            log_content = file.read()
        return log_content
    except IOError as e:
        raise IOError(f"An error occurred while reading the file: {e}")


@stata_mcp.tool(
    name="get_data_info",
    description="Get descriptive statistics for the data file"
)
def get_data_info(data_path: str | Path,
                  vars_list: List[str] | str | None = None,
                  encoding: str = "utf-8",
                  file_extension: Optional[str] = None,
                  **kwargs) -> Dict[str, dict]:
    """
    Get data file vars information.

    Args:
        data_path (str | Path): the data file's absolutely path.
        vars_list (List[str] | str | None): the vars you want to get info (default is None, means all vars).
        encoding (str): data file encoding method (dta file is not supported this arg).
        file_extension (Optional[str]): the data file's extension, default is None, then would find it automatically.

        **kwargs:
            is_save (Optional[bool]): default = rue, whether save the result to a txt file.
            save_path (str): the data-info saved file path, 
                             if None would be saved rooted in `{tmp_base_path}` with name same as data, 
                             like: data_path = "/Users/username/Documents/stata-mcp-folder/stata-mcp-tmp/some_data.dta",
                                 -> "/Users/your_name/Documents/stata-mcp-folder/stata-mcp-tmp/some_data.txt"
            info_file_encoding (Optional[str]): default = "utf-8", the data-info saved file encoding.
    Returns:
        Dict[str, dict]: the data file vars information.

    Examples:
        >>> get_data_info(data_path="https://example-data.statamcp.com/01_OLS.dta")
        >>> # the info file will be ~/Documents/stata-mcp-folder/stata-mcp-tmp/01_OLS.txt
        ->
        {
            'summary': {
                'overview': {
                    'obs': 10000,
                    'var_numbers': 3
                },
                'vars_detail': {
                    'height': {
                        'type': 'float',
                        'obs': 10000,
                        'summary': {
                            'mean': 170.0025177001953,
                            'se': np.float64(0.07957535743713379),
                            'min': 134.2535858154297,
                            'max': 204.62001037597656
                        }
                    },
                    'weight': {...},
                    'id': {...}
                }
            }
        }
    """
    EXTENSION_METHOD_MAPPING: Dict[str, Callable] = {
        "dta": DtaDataInfo,
        "csv": CsvDataInfo
    }
    if file_extension is None:
        file_extension = Path(data_path).suffix
    file_extension = file_extension.split(".")[-1].lower()
    if file_extension not in EXTENSION_METHOD_MAPPING:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    cls = EXTENSION_METHOD_MAPPING.get(file_extension)
    data_info = cls(data_path=data_path, vars_list=vars_list, encoding=encoding, **kwargs).info

    if kwargs.get("is_save", True):
        save_path = kwargs.get("save_path", None)
        if save_path is None:
            data_name = Path(data_path).name.split(".")[0]
            data_info_path = os.path.join(tmp_base_path, data_name, ".txt")
        else:
            data_info_path = save_path

        os.makedirs(os.path.dirname(data_info_path), exist_ok=True)
        with open(data_info_path, "w", encoding=kwargs.get("info_file_encoding", "utf-8")) as f:
            f.write(data_info)

    return data_info


@stata_mcp.prompt()
def results_doc_path() -> str:
    """
    Generate and return a result document storage path based on the current timestamp.

    This function performs the following operations:
    1. Gets the current system time and formats it as a '%Y%m%d%H%M%S' timestamp string
    2. Concatenates this timestamp string with the preset result_doc_path base path to form a complete path
    3. Creates the directory corresponding to that path (no error if directory already exists)
    4. Returns the complete path string of the newly created directory

    Returns:
        str: The complete path of the newly created result document directory, formatted as:
            `<result_doc_path>/<YYYYMMDDHHMMSS>`, where the timestamp portion is generated from the system time when the function is executed

    Notes:
        (The following content is not needed for LLM to understand)
        - Using the `exist_ok=True` parameter, no exception will be raised when the target directory already exists
        - The function uses the walrus operator (:=) in Python 3.8+ to assign a variable within an expression
        - The returned path is suitable for use as the output directory for Stata commands such as `outreg2`
        - In specific Stata code, you can set the file output path at the beginning.
    """
    os.makedirs(
        (path := os.path.join(
            result_doc_path,
            datetime.strftime(
                datetime.now(),
                "%Y%m%d%H%M%S"))),
        exist_ok=True,
    )
    return path


@stata_mcp.tool(
    name="write_dofile",
    description="write the stata-code to dofile"
)
def write_dofile(content: str, encoding: str = None) -> str:
    """
    Write stata code to a dofile and return the do-file path.

    Args:
        content (str): The stata code content which will be writen to the designated do-file.
        encoding (str): The encoding method for the dofile, default -> 'utf-8'

    Returns:
        the do-file path

    Notes:
        Please be careful about the first command in dofile should be use data.
        For avoiding make mistake, you can generate stata-code with the function from `StataCommandGenerator` class.
        Please avoid writing any code that draws graphics or requires human intervention for uncertainty bug.
        If you find something went wrong about the code, you can use the function from `StataCommandGenerator` class.

    Enhancement:
        If you have `outreg2`, `esttab` command for output the result,
        you should use the follow command to get the output path.
        `results_doc_path`, and use `local output_path path` the path is the return of the function `results_doc_path`.
        If you want to use the function `write_dofile`, please use `results_doc_path` before which is necessary.

    """
    file_path = os.path.join(
        dofile_base_path,
        datetime.strftime(datetime.now(), "%Y%m%d%H%M%S") + ".do"
    )
    encoding = encoding or "utf-8"
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
    return file_path


@stata_mcp.tool(
    name="append_dofile",
    description="append stata-code to an existing dofile or create a new one",
)
def append_dofile(original_dofile_path: str, content: str, encoding: str = None) -> str:
    """
    Append stata code to an existing dofile or create a new one if the original doesn't exist.

    Args:
        original_dofile_path (str): Path to the original dofile to append to.
            If empty or invalid, a new file will be created.
        content (str): The stata code content which will be appended to the designated do-file.
        encoding (str): The encoding method for the dofile, default -> 'utf-8'

    Returns:
        The new do-file path (either the modified original or a newly created file)

    Notes:
        When appending to an existing file, the content will be added at the end of the file.
        If the original file doesn't exist or path is empty, a new file will be created with the content.
        Please be careful about the syntax coherence when appending code to an existing file.
        For avoiding mistakes, you can generate stata-code with the function from `StataCommandGenerator` class.
        Please avoid writing any code that draws graphics or requires human intervention for uncertainty bug.
        If you find something went wrong about the code, you can use the function from `StataCommandGenerator` class.

    Enhancement:
        If you have `outreg2`, `esttab` command for output the result,
        you should use the follow command to get the output path.
        `results_doc_path`, and use `local output_path path` the path is the return of the function `results_doc_path`.
        If you want to use the function `append_dofile`, please use `results_doc_path` before which is necessary.
    """
    # Set encoding if None
    encoding = encoding or "utf-8"

    # Create a new file path for the output
    new_file_path = os.path.join(
        dofile_base_path, datetime.strftime(
            datetime.now(), "%Y%m%d%H%M%S") + ".do")

    # Check if original file exists and is valid
    original_exists = False
    original_content = ""
    if original_dofile_path and os.path.exists(original_dofile_path):
        try:
            with open(original_dofile_path, "r", encoding=encoding) as f:
                original_content = f.read()
            original_exists = True
        except Exception:
            # If there's any error reading the file, we'll create a new one
            original_exists = False

    # Write to the new file (either copying original content + new content, or
    # just new content)
    with open(new_file_path, "w", encoding=encoding) as f:
        if original_exists:
            f.write(original_content)
            # Add a newline if the original file doesn't end with one
            if original_content and not original_content.endswith("\n"):
                f.write("\n")
        f.write(content)

    return new_file_path


@stata_mcp.tool(name="ssc_install", description="Install a package from SSC")
def ssc_install(command: str, is_replace: bool = True) -> str:
    """
    Install a package from SSC

    Args:
        command (str): The name of the package to be installed from SSC.
        is_replace (bool): Whether to force replacement of an existing installation. Defaults to True.

    Returns:
        str: The execution log returned by Stata after running the installation.

    Examples:
        >>> ssc_install(command="outreg2")
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        opened on:  12 Oct 2025, 18:54:47

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012185447.do"

        . ssc install outreg2, replace
        checking outreg2 consistency and verifying not already installed...
        all files already exist and are up to date.

        .
        end of do-file

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        closed on:  12 Oct 2025, 18:54:55
        -------------------------------------------------------------------------------

        >>> ssc_install(command="a_fake_command")
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        opened on:  12 Oct 2025, 19:01:59

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012190159.do"

        . ssc install a_fake_command, replace
        ssc install: "a_fake_command" not found at SSC, type search a_fake_command
        (To find all packages at SSC that start with a, type ssc describe a)
        r(601);

        end of do-file

        r(601);

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        closed on:  12 Oct 2025, 19:02:00
        -------------------------------------------------------------------------------

    Notes:
        Avoid using this tool unless strictly necessary, as SSC installation can be time-consuming
        and may not be required if the package is already present.
    """
    replace_clause = ", replace" if is_replace else ""
    dofile_path = write_dofile(f"ssc install {command}{replace_clause}")
    result = stata_do(dofile_path)
    log_file_content = result["log_content"]
    return log_file_content


@stata_mcp.tool(name="load_figure")
def load_figure(figure_path: str) -> Image:
    """
    Load figure from device

    Args:
        figure_path (str): the figure file path, only support png and jpg format

    Returns:
        Image: the figure thumbnail
    """
    if not os.path.exists(figure_path):
        raise FileNotFoundError(f"{figure_path} not found")
    return Image(figure_path)


@stata_mcp.tool(name="mk_dir")
def mk_dir(path: str) -> bool:
    """
    Safely create a directory using pathvalidate for security validation.

    Args:
        path (str): the path you want to create

    Returns:
        bool: the state of the new path,
              if True -> the path exists now;
              else -> not success

    Raises:
        ValueError: if path is invalid or contains unsafe components
        PermissionError: if insufficient permissions to create directory
    """
    from pathvalidate import ValidationError, sanitize_filepath

    # Input validation
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")

    try:
        # Use pathvalidate to sanitize and validate path
        safe_path = sanitize_filepath(path, platform="auto")

        # Get absolute path for further validation
        absolute_path = os.path.abspath(safe_path)

        # Create directory with reasonable permissions
        os.makedirs(absolute_path, exist_ok=True, mode=0o755)

        # Verify successful creation
        return os.path.exists(absolute_path) and os.path.isdir(absolute_path)

    except ValidationError as e:
        raise ValueError(f"Invalid path detected: {e}")
    except PermissionError:
        raise PermissionError(f"Insufficient permissions to create directory: {path}")
    except OSError as e:
        raise OSError(f"Failed to create directory {path}: {str(e)}")


@stata_mcp.tool(name="stata_do", description="Run a stata-code via Stata")
def stata_do(dofile_path: str,
             log_file_name: str = None,
             is_read_log: bool = True) -> Dict[str, Union[str, None]]:
    """
    Execute a Stata do-file and return the log file path with optional log content.

    This function runs a Stata do-file using the configured Stata executable and
    generates a log file. It supports cross-platform execution (macOS, Windows, Linux).

    Args:
        dofile_path (str): Absolute or relative path to the Stata do-file (.do) to execute.
        log_file_name (str, optional): Set log file name without a time-string. If None, using nowtime as filename
        is_read_log (bool, optional): Whether to read and return the log file content.
                                    Defaults to True.

    Returns:
        Dict[str, Union[str, None]]: A dictionary containing:
            - "log_file_path" (str): Path to the generated Stata log file
            - "log_content" (str, optional): Content of the log file if is_read_log is True

    Raises:
        FileNotFoundError: If the specified do-file does not exist
        RuntimeError: If Stata execution fails or log file cannot be generated
        PermissionError: If there are insufficient permissions to execute Stata or write log files

    Example:
        >>> do_file_path: str | Path = ...
        >>> result = stata_do(do_file_path, is_read_log=True)
        >>> print(result[log_file_path])
        /path/to/logs/analysis.log
        >>> print(result[log_content])
        Stata log content...

        >>> result = stata_do(do_file_path, log_file_name="experience")
        >>> print(result[log_file_path])
        /log/file/base/experience.log

    Note:
        - The log file is automatically created in the configured log_file_path directory
        - Supports multiple operating systems through the StataDo executor
        - Log file naming follows Stata conventions with .log extension
    """
    # Initialize Stata executor with system configuration
    stata_executor = StataDo(
        stata_cli=STATA_CLI,  # Path to Stata executable
        log_file_path=log_base_path,  # Directory for log files
        dofile_base_path=dofile_base_path,  # Base directory for do-files
        sys_os=SYSTEM_OS  # Operating system identifier
    )

    # Execute the do-file and get log file path
    log_file_path = stata_executor.execute_dofile(dofile_path, log_file_name)

    # Return log content based on user preference
    if is_read_log:
        # Read and include log file content in response
        log_content = stata_executor.read_log(log_file_path)
        return {
            "log_file_path": log_file_path,
            "log_content": log_content
        }
    else:
        # Return only the log file path
        return {
            "log_file_path": log_file_path,
            "log_content": None
        }


if __name__ == "__main__":
    print(f"Hello Stata-MCP@version{__version__}")
