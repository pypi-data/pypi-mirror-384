#! /usr/bin/env python3

################################################################################
""" Code for running a subprocess, optionally capturing stderr and/or stdout and
    optionally echoing either or both to the console in realtime and storing.

    Uses threads to capture and output stderr and stdout since this seems to be
    the only way to do it (Popen does not have the ability to output the process
    stdout output to the stdout output).

    Intended for more versatile replacement for the thingy process.run() function
    which can handle all combinations of foreground/background console/return
    stderr/stdout/both options. """

# TODO: This does not run on Python versions <3.5 (so Ubuntu 14.04 is a problem!)
################################################################################

################################################################################
# Imports

import sys
import subprocess
import threading
import shlex

import thingy.tidy as tidy

################################################################################

class RunError(Exception):
    """ Run exception """

    def __init__(self, msg, status=1):
        super().__init__(msg)
        self.msg = msg
        self.status = status

################################################################################

# TODO: This is the _process() and run() replacement once additional parameters have been implemented
# as those functions are probably over-specified, so need to work out what functionality is ACTUALLY being used!

def command(cmd, show_stdout=False, show_stderr=False):
    """
    Run an external command and optionally stream its stdout/stderr to the console
    while capturing them.

    Args:
        cmd: Command to run (string or argv list). If a string, it will be split with shlex.split().
        show_stdout: If True, echo stdout lines to the console as they arrive.
        show_stderr: If True, echo stderr lines to the console as they arrive.

    Returns:
        (returncode, stdout_lines, stderr_lines)
    """

    def _pump(stream, sink, echo):
        """Thread to capture and optionally echo output from subprocess.Popen"""

        # Read line-by-line until EOF

        for line in iter(stream.readline, ""):
            # Strip trailing newline when storing; keep original when echoing
            sink.append(line.rstrip("\n"))

            if echo:
                print(tidy.convert_ansi(line), end="", flush=True)

        stream.close()

    # Normalize command to be a string

    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    # Storage for stdout/stderr

    stdout_lines = []
    stderr_lines = []

    # Start process with separate pipes; line-buffering for timely reads

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,                 # decode to str
        bufsize=1,                 # line-buffered
        universal_newlines=True,   # compatibility alias
        errors="replace"           # avoid crashes on decoding issues
    )

    # Threads to read both streams concurrently (prevents deadlocks)

    t_out = threading.Thread(target=_pump, args=(proc.stdout, stdout_lines, show_stdout))
    t_err = threading.Thread(target=_pump, args=(proc.stderr, stderr_lines, show_stderr))

    t_out.start()
    t_err.start()

    # Wait for process to complete and threads to drain

    returncode = proc.wait()
    t_out.join()
    t_err.join()

    # Return the status, stdout and stderr

    return returncode, stdout_lines, stderr_lines

################################################################################

def capture_output(cmd, input_stream, output_streams):
    """ Capture data from a stream (input_stream), optionally
        outputting it (if output_streams is not None and optionally
        saving it into a variable (data, if not None), terminating
        when the specified command (cmd, which is presumed to be the process
        outputting to the input stream) exits.
        TODO: Use of convert_ansi should be controlled via a parameter (off/light/dark)
        TODO: Another issue is that readline() only returns at EOF or EOL, so if you get a prompt "Continue?" with no newline you do not see it until after you respond to it.
    """

    while True:
        output = input_stream.readline()

        if output:
            if output_streams:
                for stream in output_streams:
                    if isinstance(stream, list):
                        stream.append(output.rstrip())
                    else:
                        if stream in (sys.stdout, sys.stderr):
                            stream.write(tidy.convert_ansi(output))
                        else:
                            stream.write(output)

        elif cmd.poll() is not None:
            return

################################################################################

def _process(command,
             stdout=None, stderr=None,
             output=None):
    """ Run an external command.

        stdout and stderr indicate whether stdout/err are output and/or sent to a file and/or stored in a variable.
        They can be boolean (True: output to sys.stdout/err, False: Do nothing), a file handle or a variable, or an
        array of any number of these (except booleans).

        If output is True then stdout and stderr are both output as if stdout=True and stderr=True (in addition to
        any other values passed in those parameters)

        The return value is a tuple consisting of the status code, captured stdout (if any) and captured
        stderr (if any).

        Will raise OSError if the command could not be run and RunError if the command returned a non-zero status code.
    """

    # If stdout/stderr are booleans then output to stdout/stderr if True, else discard output

    if isinstance(stdout, bool):
        stdout = sys.stdout if stdout else None

    if isinstance(stderr, bool):
        stderr = sys.stderr if stderr else None

    # If stdout/stderr are not arrays then make them so

    if not isinstance(stdout, list):
        stdout = [stdout] if stdout else []

    if not isinstance(stderr, list):
        stderr = [stderr] if stderr else []

    # If output is True then add stderr/out to the list of outputs

    if output:
        if sys.stdout not in stdout:
            stdout.append(sys.stdout)

        if sys.stderr not in stderr:
            stderr.append(sys.stderr)

    # Capture stdout/stderr to arrays

    stdout_data = []
    stderr_data = []

    stdout.append(stdout_data)
    stderr.append(stderr_data)

    if isinstance(command, str):
        command = shlex.split(command, comments=True)

    # Use a pipe for stdout/stderr if are are capturing it
    # and send it to /dev/null if we don't care about it at all.

    if stdout == [sys.stdout] and not stderr:
        stdout_stream = subprocess.STDOUT
        stderr_stream = subprocess.DEVNULL
    else:
        stdout_stream = subprocess.PIPE if stdout else subprocess.DEVNULL
        stderr_stream = subprocess.PIPE if stderr else subprocess.DEVNULL

    # Run the command with no buffering and capturing output if we
    # want it - this will raise OSError if there was a problem running
    # the command.

    cmd = subprocess.Popen(command,
                           bufsize=0,
                           stdout=stdout_stream,
                           stderr=stderr_stream,
                           text=True,
                           errors='ignore',
                           encoding='ascii')

    # Create threads to capture stderr and/or stdout if necessary

    if stdout_stream == subprocess.PIPE:
        stdout_thread = threading.Thread(target=capture_output, args=(cmd, cmd.stdout, stdout), daemon=True)
        stdout_thread.start()
    else:
        stdout_thread = None

    if stderr_stream == subprocess.PIPE:
        stderr_thread = threading.Thread(target=capture_output, args=(cmd, cmd.stderr, stderr), daemon=True)
        stderr_thread.start()
    else:
        stderr_thread = None

    # Wait until the command terminates (and set the returncode)

    if stdout_thread:
        stdout_thread.join()

    if stderr_thread:
        stderr_thread.join()

    cmd.wait()

    # If the command failed, raise an exception

    if cmd.returncode:
        raise RunError('\n'.join(stderr_data) if stderr_data else 'Error %d running "%s"' % (cmd.returncode, ' '.join(command)))

    # Return status, stdout, stderr (the latter 2 may be empty if we did not capture data).

    return {'status': cmd.returncode, 'stdout': stdout_data, 'stderr': stderr_data}

################################################################################

def run(command,
        stdout=None,
        stderr=None,
        output=None):
    """ Simple interface to the _process() function
        Has the same parameters, with the same defaults.
        The return value is either the data output to stdout, if any
        or the data output to stderr otherwise.
        The status code is not returned, but the function will raise an exception
        if it is non-zero """

    result = _process(command=command,
                      stdout=stdout,
                      stderr=stderr,
                      output=output)

    return result['stdout'] if result['stdout'] else result['stderr']

################################################################################

if __name__ == '__main__':
    def test_run(cmd,
                 stdout=None, stderr=None):
        """ Test wrapper for the process() function. """

        print('-' * 80)
        print('Running: %s' % (cmd if isinstance(cmd, str) else ' '.join(cmd)))

        result = _process(cmd, stdout=stdout, stderr=stderr)

        print('Status: %d' % result['status'])

    def test():
        """ Test code """

        test_run('echo nothing')

        test_run(['ls', '-l', 'run_jed'])
        test_run(['ls -l run_*'], stdout=True)
        test_run('false')
        test_run('true', stdout=sys.stdout)
        test_run(['git', 'status'], stdout=sys.stdout, stderr=sys.stderr)

        test_run(['make'], stderr=sys.stderr)
        test_run(['make'], stdout=sys.stdout, stderr=[sys.stderr])
        test_run(['make'], stdout=True)
        test_run(['make'], stdout=sys.stdout)
        test_run(['make'])

        output = []
        test_run('ls -l x*; sleep 1; echo "Bye!"', stderr=[sys.stderr, output], stdout=sys.stdout)
        print('Output=%s' % output)

    test()
