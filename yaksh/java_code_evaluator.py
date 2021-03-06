#!/usr/bin/env python
from __future__ import unicode_literals
import traceback
import pwd
import os
from os.path import join, isfile
import subprocess
import importlib

# Local imports
from .code_evaluator import CodeEvaluator
from .file_utils import copy_files, delete_files


class JavaCodeEvaluator(CodeEvaluator):
    """Tests the Java code obtained from Code Server"""
    def setup(self):
        super(JavaCodeEvaluator, self).setup()
        self.files = []
        self.submit_code_path = self.create_submit_code_file('Test.java')
        self.compiled_user_answer = None
        self.compiled_test_code = None
        self.user_output_path = ""
        self.ref_output_path = ""

    def teardown(self):
        # Delete the created file.
        os.remove(self.submit_code_path)
        if os.path.exists(self.user_output_path):
            os.remove(self.user_output_path)
        if os.path.exists(self.ref_output_path):
            os.remove(self.ref_output_path)
        if self.files:
            delete_files(self.files)
        super(JavaCodeEvaluator, self).teardown()


    def get_commands(self, clean_ref_code_path, user_code_directory):
        compile_command = 'javac  {0}'.format(self.submit_code_path),
        compile_main = ('javac {0} -classpath '
                        '{1} -d {2}').format(clean_ref_code_path,
                                             user_code_directory,
                                             user_code_directory)
        return compile_command, compile_main

    def set_file_paths(self, directory, file_name):
        output_path = "{0}{1}.class".format(directory, file_name)
        return output_path

    def compile_code(self, user_answer, file_paths, test_case, weight):
        if self.compiled_user_answer and self.compiled_test_code:
            return None
        else:
            ref_code_path = test_case
            clean_ref_code_path, clean_test_case_path = \
                     self._set_test_code_file_path(ref_code_path)
            if file_paths:
                self.files = copy_files(file_paths)
            if not isfile(clean_ref_code_path):
                msg = "No file at %s or Incorrect path" % clean_ref_code_path
                return False, msg
            if not isfile(self.submit_code_path):
                msg = "No file at %s or Incorrect path" % self.submit_code_path
                return False, msg

            user_code_directory = os.getcwd() + '/'
            self.write_to_submit_code_file(self.submit_code_path, 
                user_answer
            )
            ref_file_name = (clean_ref_code_path.split('/')[-1]).split('.')[0]
            self.user_output_path = self.set_file_paths(user_code_directory, 
                'Test'
            )
            self.ref_output_path = self.set_file_paths(user_code_directory,
                ref_file_name
            )
            compile_command, self.compile_main = self.get_commands(
                clean_ref_code_path,
                user_code_directory
            )
            self.run_command_args = "java -cp {0} {1}".format(
                user_code_directory,
                ref_file_name
            )
            self.compiled_user_answer = self._run_command(compile_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.compiled_test_code = self._run_command(self.compile_main,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            return self.compiled_user_answer, self.compiled_test_code

    def check_code(self, user_answer, file_paths, partial_grading, test_case, weight):
        """ Function validates student code using instructor code as
        reference.The first argument ref_code_path, is the path to
        instructor code, it is assumed to have executable permission.
        The second argument submit_code_path, is the path to the student
        code, it is assumed to have executable permission.

        Returns
        --------

        returns (True, "Correct answer") : If the student function returns
        expected output when called by reference code.

        returns (False, error_msg): If the student function fails to return
        expected output when called by reference code.

        Returns (False, error_msg): If mandatory arguments are not files or
        if the required permissions are not given to the file(s).

        """
        success = False
        test_case_weight = 0.0

        proc, stdnt_out, stdnt_stderr = self.compiled_user_answer
        stdnt_stderr = self._remove_null_substitute_char(stdnt_stderr)

        # Only if compilation is successful, the program is executed
        # And tested with testcases
        if stdnt_stderr == '':
            proc, main_out, main_err = self.compiled_test_code
            main_err = self._remove_null_substitute_char(main_err)

            if main_err == '':
                ret = self._run_command(self.run_command_args, shell=True,
                                         stdin=None,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                proc, stdout, stderr = ret
                if proc.returncode == 0:
                    success, err = True, "Correct answer"
                    test_case_weight = float(weight) if partial_grading else 0.0
                else:
                    err = stdout + "\n" + stderr
            else:
                err = "Error:"
                try:
                    error_lines = main_err.splitlines()
                    for e in error_lines:
                        if ':' in e:
                            err = err + "\n" + e.split(":", 1)[1]
                        else:
                            err = err + "\n" + e
                except:
                        err = err + "\n" + main_err
        else:
            err = "Compilation Error:"
            try:
                error_lines = stdnt_stderr.splitlines()
                for e in error_lines:
                    if ':' in e:
                        err = err + "\n" + e.split(":", 1)[1]
                    else:
                        err = err + "\n" + e
            except:
                err = err + "\n" + stdnt_stderr
        return success, err, test_case_weight
