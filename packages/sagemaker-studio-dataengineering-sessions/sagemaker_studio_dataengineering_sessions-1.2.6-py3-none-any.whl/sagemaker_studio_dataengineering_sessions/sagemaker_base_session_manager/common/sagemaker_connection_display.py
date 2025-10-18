import sys

from IPython.display import HTML, Markdown
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.ipython_display import IpythonDisplay

class SageMakerConnectionDisplay:
    _instance = IpythonDisplay()

    @classmethod
    def display(cls, to_display):
        cls._instance.display(to_display)

    @classmethod
    def display_markdown(cls, markdown_str):
        cls._instance.display(Markdown(markdown_str))

    @classmethod
    def send_error(cls, output_error):
        sys.stderr.write(f"{output_error}\n")
        cls._instance.stderr_flush()

    @classmethod
    def html(cls, to_display):
        cls._instance.display(HTML(to_display))


    @classmethod
    def write_msg(cls, msg):
        sys.stdout.write(f"{msg}\n")
        cls._instance.stdout_flush()

    @classmethod
    def write_critical_msg(cls, msg):
        """
        To write a critical message.
        Use this function to display messages that is critical to other functionalities
        Messages that are displayed using this function should not be changed without careful evaluation
        """
        sys.stdout.write(f"{msg}\n")
        cls._instance.stdout_flush()

    @classmethod
    def writeln(cls, msg):
        cls._instance.write("{}\n".format(msg))
