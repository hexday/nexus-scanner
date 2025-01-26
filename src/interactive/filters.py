from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import re
from enum import Enum
import operator
from datetime import datetime
import logging


class FilterType(Enum):
    SEVERITY = "severity"
    CATEGORY = "category"
    DATE = "date"
    STATUS = "status"
    CUSTOM = "custom"


class FilterOperator(Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    IN = "in"
    NOT_IN = "not_in"


@dataclass
class Filter:
    name: str
    type: FilterType
    operator: FilterOperator
    value: Any
    description: str
    enabled: bool = True


class FilterHandler:
    def __init__(self):
        self.logger = logging.getLogger("nexus.filters")
        self.filters: Dict[str, Filter] = {}
        self.operators = {
            FilterOperator.EQUALS: operator.eq,
            FilterOperator.NOT_EQUALS: operator.ne,
            FilterOperator.GREATER_THAN: operator.gt,
            FilterOperator.LESS_THAN: operator.lt,
            FilterOperator.CONTAINS: lambda x, y: y in x,
            FilterOperator.NOT_CONTAINS: lambda x, y: y not in x,
            FilterOperator.MATCHES: lambda x, y: bool(re.search(y, x)),
            FilterOperator.IN: lambda x, y: x in y,
            FilterOperator.NOT_IN: lambda x, y: x not in y
        }
        self._setup_default_filters()

    def _setup_default_filters(self):
        """Setup default system filters"""
        self.add_filter(
            name="high_severity",
            type=FilterType.SEVERITY,
            operator=FilterOperator.EQUALS,
            value="HIGH",
            description="Show only high severity findings"
        )

        self.add_filter(
            name="recent",
            type=FilterType.DATE,
            operator=FilterOperator.GREATER_THAN,
            value=datetime.now().timestamp() - (24 * 60 * 60),
            description="Show findings from last 24 hours"
        )

    def add_filter(self,
                   name: str,
                   type: FilterType,
                   operator: FilterOperator,
                   value: Any,
                   description: str):
        """Add a new filter"""
        filter = Filter(
            name=name,
            type=type,
            operator=operator,
            value=value,
            description=description
        )
        self.filters[name] = filter

    def remove_filter(self, name: str):
        """Remove a filter"""
        if name in self.filters:
            del self.filters[name]

    def apply_filters(self, items: List[Dict]) -> List[Dict]:
        """Apply all enabled filters to items"""
        filtered_items = items

        for filter in self.filters.values():
            if filter.enabled:
                filtered_items = self._apply_filter(filtered_items, filter)

        return filtered_items

    def _apply_filter(self, items: List[Dict], filter: Filter) -> List[Dict]:
        """Apply single filter to items"""
        try:
            filtered = []
            operator_func = self.operators[filter.operator]

            for item in items:
                if self._evaluate_filter(item, filter, operator_func):
                    filtered.append(item)

            return filtered

        except Exception as e:
            self.logger.error(f"Filter application error: {str(e)}")
            return items

    def _evaluate_filter(self, item: Dict, filter: Filter, operator_func: Callable) -> bool:
        """Evaluate single filter against item"""
        try:
            if filter.type == FilterType.CUSTOM:
                return self._evaluate_custom_filter(item, filter)

            value = self._get_item_value(item, filter.type)
            if value is None:
                return False

            return operator_func(value, filter.value)

        except Exception as e:
            self.logger.debug(f"Filter evaluation error: {str(e)}")
            return True

    def _evaluate_custom_filter(self, item: Dict, filter: Filter) -> bool:
        """Evaluate custom filter logic"""
        try:
            if callable(filter.value):
                return filter.value(item)
            return False
        except Exception as e:
            self.logger.debug(f"Custom filter error: {str(e)}")
            return True

    def _get_item_value(self, item: Dict, filter_type: FilterType) -> Any:
        """Extract value from item based on filter type"""
        type_map = {
            FilterType.SEVERITY: "severity",
            FilterType.CATEGORY: "category",
            FilterType.DATE: "timestamp",
            FilterType.STATUS: "status"
        }

        if filter_type in type_map:
            return item.get(type_map[filter_type])
        return None

    def enable_filter(self, name: str):
        """Enable a filter"""
        if name in self.filters:
            self.filters[name].enabled = True

    def disable_filter(self, name: str):
        """Disable a filter"""
        if name in self.filters:
            self.filters[name].enabled = False

    def get_active_filters(self) -> List[Filter]:
        """Get list of active filters"""
        return [f for f in self.filters.values() if f.enabled]

    def clear_filters(self):
        """Remove all filters"""
        self.filters.clear()
        self._setup_default_filters()

    def create_custom_filter(self,
                             name: str,
                             callback: Callable[[Dict], bool],
                             description: str):
        """Create custom filter with callback function"""
        self.add_filter(
            name=name,
            type=FilterType.CUSTOM,
            operator=FilterOperator.EQUALS,
            value=callback,
            description=description
        )
