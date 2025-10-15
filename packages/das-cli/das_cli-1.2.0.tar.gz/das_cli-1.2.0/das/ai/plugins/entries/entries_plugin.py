import logging
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from das.managers.entries_manager import EntryManager

logger = logging.getLogger(__name__)


class GetEntryByCodePlugin:
    def __init__(self):
        self.entry_manager = EntryManager()

    @kernel_function(name="GetEntryByCode", description="Get an entry by its code.")
    def get_entry_by_code(self, code: str):
        """Get the entry code based on the entry name."""	
        return self.entry_manager.get(code=code)