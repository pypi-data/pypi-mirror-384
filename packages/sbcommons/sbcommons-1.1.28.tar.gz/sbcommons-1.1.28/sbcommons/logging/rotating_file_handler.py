import datetime as dt
from logging import FileHandler
from pathlib import Path
from typing import Union


class InvalidLogNameError(Exception):
    DEFAULT_MSG = 'The log file name {LOG_FILE_NAME} should be formatted as follows: ' \
                  ' <base_file_name>__<year>_<month>_<day>.<extension>.'

    def __init__(self, msg=None, file_name=None, *args):
        self.file_name = file_name
        msg = msg if msg else self.DEFAULT_MSG.format(LOG_FILE_NAME=file_name)
        Exception.__init__(self, msg, *args)


class RotatingFileHandler(FileHandler):
    """ A FileHandler that rotates the file it writes to every day by appending a date suffix
        to the file name.

        Attributes:
            __file_path: The pathlib.Path object for the file path of the log file.
            backup_count: The maximum number of log files to keep in the same directory before
                starting to discard old log files.
    """

    def __init__(self, file_path, mode='a', encoding=None, delay=False, errors=None,
                 backup_count=0):
        """
        Open the specified file and use it as the stream for logging.
        """
        self.__file_path = Path(file_path)
        self.backup_count = backup_count
        self.rotate_file()
        FileHandler.__init__(self, file_path, mode, encoding, delay, errors)

    def rotate_file(self) -> bool:
        """ Rotates a file by adding a suffix to the file name and optionally discarding old files.

        Before we write any new logs, if the file path was last modified on a previous date,
        we rename the file by adding its last modified date as a suffix to the file name. If there
        are more than <backup_count> files saved with the same prefix, then the oldest one is
        discarded, if <backup_count> is set to be larger than 0.

        Returns:
            True if a file has been rotated, False otherwise.
        """
        last_modified_date = self.get_last_modified_date(self.__file_path)
        today_date = dt.datetime.now().date()

        # If the file doesn't exist or the last modified date is today, don't rotate
        if not last_modified_date or last_modified_date == today_date:
            return False

        # Rename old file by adding a date suffix
        self.add_date_suffix(self.__file_path, last_modified_date)

        # Discard old files with the same name if self.backup_count is set to be larger than 0
        self.discard_old_files()

        return True

    @staticmethod
    def get_last_modified_date(path: Path) -> Union[dt.date, None]:
        """ Gets last modified date from file path. Returns None if file doesn't exist. """
        if not path.exists():
            return
        return dt.datetime.fromtimestamp(path.stat().st_mtime).date()

    @staticmethod
    def add_date_suffix(path: Path, date: dt.date) -> Union[dt.date, None]:
        """ Adds the date suffix to the file name. Returns None if file doesn't exist. """
        if not path.exists():
            return
        # Creating new file name, skipping the last extension since it is automatically added when
        # calling path.rename()
        file_name, extensions = path.stem.split('.')[0], path.suffixes
        file_name += f'__{date.year}_{date.month}_{date.day}' + ''.join(extensions[:-1])
        path.rename(path.with_stem(file_name))

    @staticmethod
    def get_date_suffix(path: Path):
        """ Gets date suffix from file path.

        Args:
            path: The file path object.

        Raises:
            InvalidLogNameError if the name of the file is not formatted as follows:
                <base_name>__<year>_<month>_<day>.<extension>.
        """
        try:
            filename = path.stem.split('.')[0]
            date = filename.split('__')[1]
            year, month, day = date.split('_')
            return dt.datetime(int(year), int(month), int(day))
        except (IndexError, ValueError):
            raise InvalidLogNameError(file_name=filename)

    def discard_old_files(self):
        """ Discard old files with the same name if self.backup_count is set to be larger than 0."""
        if not self.backup_count or not self.__file_path.exists:
            return

        file_name, extensions = self.__file_path.stem.split('.')[0], self.__file_path.suffixes
        # Get log files that have the same base file name within the directory, sorted by timestamp
        log_files = sorted(self.__file_path.parent.absolute().glob(f'{file_name}__*.*'),
                           key=lambda x: self.get_date_suffix(x), reverse=True)
        # If we exceed the maximum number of files with the same name, delete the oldest files
        if len(log_files) > self.backup_count:
            discard_list = log_files[self.backup_count:]
            for path in discard_list:
                path.unlink()
