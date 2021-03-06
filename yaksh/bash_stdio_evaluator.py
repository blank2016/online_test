#!/usr/bin/env python
from __future__ import unicode_literals
import subprocess
import os
from os.path import isfile

#local imports
from .stdio_evaluator import StdIOEvaluator
from .file_utils import copy_files, delete_files


class BashStdioEvaluator(StdIOEvaluator):
    """Evaluates Bash StdIO based code"""

    def setup(self):
        super(BashStdioEvaluator, self).setup()
        self.files = []
        self.submit_code_path = self.create_submit_code_file('Test.sh')

    def teardown(self):
        os.remove(self.submit_code_path)
        if self.files:
            delete_files(self.files)
        super(BashStdioEvaluator, self).teardown()

    def compile_code(self, user_answer, file_paths, expected_input, expected_output, weight):
        if file_paths:
            self.files = copy_files(file_paths)
        if not isfile(self.submit_code_path):
            msg = "No file at %s or Incorrect path" % self.submit_code_path
            return False, msg
        user_code_directory = os.getcwd() + '/'
        user_answer = user_answer.replace("\r", "")
        self.write_to_submit_code_file(self.submit_code_path, user_answer)

    def check_code(self, user_answer, file_paths, partial_grading,
        expected_input, expected_output, weight):
        success = False
        test_case_weight = 0.0

        expected_input = str(expected_input).replace('\r', '')
        proc = subprocess.Popen("bash ./Test.sh",
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        success, err = self.evaluate_stdio(user_answer, proc,
                                           expected_input,
                                           expected_output
                                           )
        test_case_weight = float(weight) if partial_grading and success else 0.0
        return success, err, test_case_weight
