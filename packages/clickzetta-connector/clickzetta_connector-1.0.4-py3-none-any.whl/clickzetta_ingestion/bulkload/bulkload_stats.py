from abc import ABC, abstractmethod


class BulkLoadStats(ABC):
    """Abstract base class for bulk load statistics."""

    @abstractmethod
    def get_records_written(self) -> int:
        """Get the number of records written."""
        pass

    @abstractmethod
    def get_bytes_written(self) -> int:
        """Get the number of bytes written."""
        pass

    @abstractmethod
    def get_write_time_ms(self) -> int:
        """Get the write time in milliseconds."""
        pass
