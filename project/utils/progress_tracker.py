"""
by Keelin Becker-Wheeler, Mar 2020
"""


class ProgressTracker:
    """
    Convenience class to print helpful progress percentage during runtime.
    """

    def __init__(self, msg, show_percentage=True):
        self.msg = f"{msg}.."
        print(self.msg, flush=True, end='')

        self.progress_txt = ''
        self.progress_sum = 0
        self.maximum = 100

        if show_percentage:
            self.set(0)

    def txt(self, msg):
        self.clear()
        self.msg = f"{msg}.."
        print(self.msg, flush=True, end='')

    def clear(self):
        self.clear_progress_txt()
        self.remove_printed_text(self.msg)

    def set(self, progress, maximum=100):
        self.progress_sum = progress
        self.maximum = maximum

        # Clear previous progress text if exists, and replace with new percentage
        self.clear_progress_txt(f" {100*self.progress_sum/self.maximum:.1f}%")
        print(self.progress_txt, flush=True, end='')

    def add(self, progress, maximum=100):
        # Scale current percentage to new maximum if necessary
        if self.maximum != maximum:
            self.progress_sum = maximum * self.progress_sum/self.maximum

        self.set(self.progress_sum+progress, maximum)

    def clear_progress_txt(self, new_progress_txt=''):
        self.remove_printed_text(self.progress_txt)
        self.progress_txt = new_progress_txt

    @staticmethod
    def remove_printed_text(msg):
        """
        Removes the given text assuming it was printed to the console.
        Also assumes \b works as backspace in the console.

        :type msg: str
        """

        print('\b'*len(msg), flush=True, end=' '*len(msg))
        print('\b'*len(msg), flush=True, end='')

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        # Clean up when exiting context
        self.clear()
