# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Implementation of the XML report writer
"""

from pathlib import Path
from xml.sax.saxutils import escape

import io
import os
import time
import traceback as tb

import threading
import queue

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class AsyncWriter(threading.Thread):
    """
    Write the report asynchronously
    """
    def __init__(self, report_filename: Path):
        threading.Thread.__init__(self)
        self._writer_queue = queue.Queue(100)
        # File must remain open
        # pylint: disable = consider-using-with
        self._report = io.open(report_filename, "w", encoding='utf8')
        self._stopped = False


    def __del__(self):
        self.close()


    def close(self):
        """
        Stop writing
        """
        self._stopped = True
        if self._report is not None:
            while not self._writer_queue.empty():
                time.sleep(0.1)
            self._report.flush()
            self._report.close()
            self._report = None


    def run(self):
        """
        Start writing
        """
        if self._report is None:
            return
        while not self._stopped or not self._writer_queue.empty():
            self._report.write(self._writer_queue.get())


    def write(self, data: str):
        """
        Write the given string asynchronously
        """
        if not self._stopped:
            self._writer_queue.put(data)


class XmlReport():
    """
    Public interface of the XML report
    """
    def __init__(self, suite_name: str, report_filename: Path) -> None:
        report_filename = Path(report_filename)
        self._filename = str(report_filename)
        try:
            os.makedirs(report_filename.parent, exist_ok=True)
            if report_filename.exists():
                os.remove(report_filename)

            self._report = AsyncWriter(report_filename)
            self._report.start()

            timestamp = time.strftime(TIME_FORMAT, time.localtime())
            header = []
            header.append('<?xml version="1.0" encoding="UTF-8"?>')
            header.append('<TestReport version="1.0" >')
            header.append(' <test type="testsuite">')
            header.append(f'  <prolog time="{timestamp}">')
            header.append(f'   <name>{suite_name}</name>')
            header.append('  </prolog>')
            self._report.write("\n".join(header) + "\n")
        except:
            print("Unable to create report")
            raise


    def __del__(self):
        self.end_report()


    def get_folder(self) -> Path:
        """
        Return the path to the report folder
        """
        return Path(self._filename).parent.resolve()


    def end_report(self):
        """
        Write final tags and close the report
        """
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        footer = []
        footer.append(f'  <epilog time="{timestamp}"/>')
        footer.append(' </test>')
        footer.append('</TestReport>')
        self._report.write("\n".join(footer) + "\n")
        self._report.close()
        self._report.join()


    def start_test_case(self, name):
        """
        Write tags to start a test case
        """
        indent = 2 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<test type="testcase">')
        lines.append(indent + f' <prolog time="{timestamp}">')
        lines.append(indent + f'  <name>{escape(name)}</name>')
        lines.append(indent +  ' </prolog>')
        self._report.write("\n".join(lines) + "\n")


    def end_test_case(self):
        """
        Write tags to finish a test case
        """
        indent = 2 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent + f' <epilog time="{timestamp}"/>')
        lines.append(indent +  '</test>')
        self._report.write("\n".join(lines) + "\n")


    def start_feature(self, name, description):
        """
        Write tags to start a feature
        """
        indent = 3 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<test type="feature">')
        lines.append(indent + f' <prolog time="{timestamp}">')
        lines.append(indent + f'  <name>{escape(name)}</name>')
        lines.append(
            indent + f'  <description>{escape(description)}</description>')
        lines.append(indent + ' </prolog>')
        self._report.write("\n".join(lines) + "\n")


    def end_feature(self):
        """
        Write tags to finish a feature
        """
        indent = 3 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent + f' <epilog time="{timestamp}"/>')
        lines.append(indent +  '</test>')
        self._report.write("\n".join(lines) + "\n")


    def start_scenario(self, name, description):
        """
        Write tags to start a scenario
        """
        indent = 4 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<test type="scenario">')
        lines.append(indent + f' <prolog time="{timestamp}">')
        lines.append(indent + f'  <name>{escape(name)}</name>')
        lines.append(
            indent + f'  <description>{escape(description)}</description>')
        lines.append(indent + ' </prolog>')
        self._report.write("\n".join(lines) + "\n")


    def start_example(self, headings, values):
        """
        Add example to current scenario
        """
        indent = 5 * " "
        lines = []
        lines.append(indent +  '<example>')
        for name, value in zip(headings, values):
            lines.append(indent +  f' <{name}>{value}</{name}>')
        lines.append(indent +  '</example>')
        self._report.write("\n".join(lines) + "\n")


    def end_scenario(self):
        """
        Write tags to finish a scenario
        """
        indent = 4 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent + f' <epilog time="{timestamp}"/>')
        lines.append(indent +  '</test>')
        self._report.write("\n".join(lines) + "\n")


    def start_step(self, name):
        """
        Write tags to start a step
        """
        indent = 5 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<test type="step">')
        lines.append(indent + f' <prolog time="{timestamp}">')
        lines.append(indent + f'  <name>{escape(name)}</name>')
        lines.append(indent +  ' </prolog>')
        self._report.write("\n".join(lines) + "\n")


    def end_step(self):
        """
        Write tags to finish a step
        """
        indent = 5 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent + f' <epilog time="{timestamp}"/>')
        lines.append(indent +  '</test>')
        self._report.write("\n".join(lines) + "\n")


    def log(self, text: str, log_type="LOG"):
        """
        Log the given message
        """
        indent = 6 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent + f'<message time="{timestamp}" type="{log_type}">')
        lines.append(indent + f'  <text>{escape(text)}</text>')
        lines.append(indent +  '</message>')
        self._report.write("\n".join(lines) + "\n")


    def passed(self, text: str, details: str):
        """
        Write tags for a successful verification
        """
        indent = 6 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<verification>')
        lines.append(
            indent + f' <scriptedVerificationResult type="PASS" time="{timestamp}">')
        lines.append(indent + f'  <text>{escape(text)}</text>')
        lines.append(indent + f'  <detail>{escape(details)}</detail>')
        lines.append(indent +  ' </scriptedVerificationResult>')
        lines.append(indent +  '</verification>')
        self._report.write("\n".join(lines) + "\n")


    def failed(self, text: str, details: str, trace = None):
        """
        Write tags for a failed verification
        """
        max_nb_frames = 5
        if trace is None:
            summary = tb.StackSummary.extract(tb.walk_stack(None))
            # Skip current frame
            start_index = 1
        else:
            summary = tb.StackSummary.extract(tb.walk_tb(trace))
            # Skip Behave frames
            start_index = 2 if len(summary) > 2 else 0
        indent = 6 * " "
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        lines = []
        lines.append(indent +  '<verification>')
        # Stacktrace
        lines.append(indent +  ' <stacktrace>')
        for frame in summary[start_index:start_index + max_nb_frames]:
            lines.append(indent +  '  <frame>')
            lines.append(indent +  '   <location>')
            lines.append(indent + f'    {frame.filename}:{frame.lineno}:{frame.name}')
            lines.append(indent +  '   </location>')
            lines.append(indent +  '   <line>')
            lines.append(indent + f'    {frame.line}')
            lines.append(indent +  '   </line>')
            lines.append(indent +  '  </frame>')
        lines.append(indent +  ' </stacktrace>')
        # Results
        lines.append(
            indent + f' <scriptedVerificationResult type="FAIL" time="{timestamp}">')
        lines.append(indent + f'  <text>{escape(text)}</text>')
        lines.append(indent + f'  <detail>{escape(details)}</detail>')
        lines.append(indent +  ' </scriptedVerificationResult>')
        lines.append(indent +  '</verification>')
        self._report.write("\n".join(lines) + "\n")
