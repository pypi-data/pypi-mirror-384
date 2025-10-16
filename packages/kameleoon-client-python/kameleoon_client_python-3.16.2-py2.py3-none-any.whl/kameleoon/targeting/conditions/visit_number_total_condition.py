"""Visit number total condition"""

from typing import Any, Dict, Union

from kameleoon.data.visitor_visits import VisitorVisits
from kameleoon.targeting.conditions.number_condition import NumberCondition


class VisitNumberTotalCondition(NumberCondition):
    """Visit number total condition uses in case if you need to target by value numeric"""

    def __init__(self, json_condition: Dict[str, Union[str, int, Any]]):
        super().__init__(json_condition, "visitCount")

    # pylint: disable=C0103
    def check(self, data: Any) -> bool:
        visitor_visits, ok = VisitorVisits.get_visitor_visits(data)
        if ok and (self._condition_value is not None):
            return self._check_targeting(len(visitor_visits.prev_visits) + 1)  # +1 for current visit
        return False
