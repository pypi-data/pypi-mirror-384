import logging
from typing import List
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class Helper:

    @staticmethod
    def map_to_dto(data: list, dto_class: T) -> List[T]:
        """
        Helper method to convert database results to DTO objects
        Args:
            data: List of database query results (dictionaries)
            dto_class: The DTO class to instantiate
        Returns:
            List of DTO instances
        """
        if not data:
            return []
        
        try:
            result = []
            for row in data:
                # Convert RealDictRow to regular dict
                if hasattr(row, 'items'):
                    row_dict = dict(row.items())
                else:
                    row_dict = dict(row)
                result.append(dto_class(**row_dict))
            return result
        except Exception as e:
            logger.error(f"Error mapping data to DTO: {str(e)}")
            raise
