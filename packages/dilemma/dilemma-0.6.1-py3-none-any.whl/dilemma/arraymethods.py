from typing import Any, Sequence
from lark import Token

from .errors import DilemmaError, ContainerError


class ArrayMethods:
    def _ensure_iterable(self, value: Any, func_name: str) -> Sequence[Any]:
        if not isinstance(value, (list, tuple)):
            raise ContainerError(
                template_key="wrong_container",
                operation=f"{func_name} (expects list/tuple)",
            )
        return value

    def _eval_predicate_on_item(self, pred_token: Token, item: Any) -> bool:
        # pred_token is a RESOLVER_EXPR token like `...`
        raw_expr = pred_token.value[1:-1]  # strip backticks

        # Instead of using resolve_path, we need to evaluate this as a dilemma expression
        # Import here to avoid circular imports
        from . import lang

        try:
            # Evaluate the expression with the current item as context
            result = lang.evaluate(raw_expr, item)
            return bool(result)
        except Exception as e:
            # Log the error for debugging but return False to continue processing
            try:
                from .logconf import get_logger

                log = get_logger(__name__)
                log.debug(
                    f"Predicate evaluation failed for '{raw_expr}' with item {item}: {e}"
                )
            except ImportError:
                # If logging fails, just continue silently
                pass
            return False

    def func_call(self, items: list[Token | Any]) -> int | bool:
        # items = [FUNC_NAME token, expr_value, (optional) RESOLVER_EXPR token]
        func_name: str = items[0].value
        collection: Any = items[1]
        predicate: Token | None = items[2] if len(items) > 2 else None

        coll: Sequence[Any] = self._ensure_iterable(collection, func_name)

        if func_name == "count_of":
            if predicate is None:
                return len(coll)
            return sum(1 for it in coll if self._eval_predicate_on_item(predicate, it))

        elif func_name == "any_of":
            if predicate is None:
                return any(bool(x) for x in coll)
            return any(self._eval_predicate_on_item(predicate, it) for it in coll)

        elif func_name == "all_of":
            if predicate is None:
                return all(bool(x) for x in coll)
            return all(self._eval_predicate_on_item(predicate, it) for it in coll)

        elif func_name == "none_of":
            if predicate is None:
                return not any(bool(x) for x in coll)
            return not any(self._eval_predicate_on_item(predicate, it) for it in coll)

        else:
            raise DilemmaError(template_key="unknown_function", function=func_name)
