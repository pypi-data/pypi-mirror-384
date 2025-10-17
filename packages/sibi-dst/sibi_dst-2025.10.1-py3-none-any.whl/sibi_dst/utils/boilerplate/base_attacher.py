from typing import Any, Awaitable, Callable, Sequence, Type


class AttachmentMaker:
    """
    Async attacher class.
    Skips work if any param value is falsy ([], None, {}, etc.).
    """

    def __init__(
            self,
            cube_cls: Type,
            fieldnames: Sequence[str],
            column_names: Sequence[str],
    ):
        self.cube_cls = cube_cls
        self.fieldnames = tuple(fieldnames)
        self.column_names = list(column_names)

    async def attach(self, *, logger=None, debug: bool = False, **params: Any):
        if any(not v for v in params.values()):
            return None
        call_params = {
            "fieldnames": self.fieldnames,
            "column_names": self.column_names,
            **params,
        }
        return await self.cube_cls(logger=logger, debug=debug).aload(**call_params)


# Factory function for backward compatibility
def make_attacher(
        cube_cls: Type,
        fieldnames: Sequence[str],
        column_names: Sequence[str],
) -> Callable[..., Awaitable[Any]]:
    """
    Factory for async attachers.
    Skips work if any param value is falsy ([], None, {}, etc.).
    """
    attacher = AttachmentMaker(cube_cls, fieldnames, column_names)
    return attacher.attach


__all__ = ['AttachmentMaker', 'make_attacher']
# from typing import Any, Awaitable, Callable, Sequence, Type
#
# def make_attacher(
#     cube_cls: Type,
#     fieldnames: Sequence[str],
#     column_names: Sequence[str],
# ) -> Callable[..., Awaitable[Any]]:
#     """
#     Factory for async attachers.
#     Skips work if any param value is falsy ([], None, {}, etc.).
#     """
#
#     async def attach(*, logger=None, debug: bool = False, **params: Any):
#         if any(not v for v in params.values()):
#             return None
#         call_params = {
#             "fieldnames": tuple(fieldnames),
#             "column_names": list(column_names),
#             **params,
#         }
#         return await cube_cls(logger=logger, debug=debug).aload(**call_params)
#
#     return attach
#
# __all__ = ['make_attacher']