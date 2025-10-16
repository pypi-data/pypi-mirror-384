from typing import List, Optional, Union, Any, Mapping

from ..graphql_handler import MondayGraphQL
from ..query_templates import get_boards_query, get_board_by_id_query, get_board_items_query, get_columns_by_board_query
from ..types import MondayApiResponse, Item, ItemsPage, BoardKind, BoardState, BoardsOrderBy
from ..utils import sleep_according_to_complexity, construct_updated_at_query_params
from ..constants import DEFAULT_PAGE_LIMIT_BOARDS, DEFAULT_PAGE_LIMIT_ITEMS


class BoardModule:
    def __init__(self, graphql_client: MondayGraphQL):
        self.client = graphql_client
    def fetch_boards(
        self,
        limit: Optional[int] = DEFAULT_PAGE_LIMIT_BOARDS,
        page: Optional[int] = None,
        ids: Optional[List[int]] = None,
        board_kind: Optional[BoardKind] = None,
        state: Optional[BoardState] = None,
        order_by: Optional[BoardsOrderBy] = None,
    ) -> MondayApiResponse:
        query = get_boards_query(ids=ids, limit=limit, page=page, board_kind=board_kind, state=state, order_by=order_by)
        return self.client.execute(query)

    def fetch_boards_by_id(self, board_id: Union[int, str]) -> MondayApiResponse:
        query = get_board_by_id_query(board_id)
        return self.client.execute(query)

    def fetch_all_items_by_board_id(
        self,
        board_id: Union[int, str],
        query_params: Optional[Mapping[str, Any]] = None,
        limit: Optional[int] = DEFAULT_PAGE_LIMIT_ITEMS,
    ) -> List[Item]:
        """
        Fetches all items from a board by board ID, includes paginating
        todo: add support for multiple board IDs
        """
        items: List[Item] = []
        cursor = None

        while True:
            query = get_board_items_query(board_id, query_params=query_params, cursor=cursor, limit=limit)
            response = self.client.execute(query)
            items_page = response.data.boards[0].items_page if cursor is None else response.data.next_items_page

            items.extend(items_page.items)
            complexity = response.data.complexity.query
            cursor = items_page.cursor

            if cursor:
                sleep_according_to_complexity(complexity)
            else:
                break

        return items

    def fetch_item_by_board_id_by_update_date(
        self,
        board_id: Union[int, str],
        updated_after: str,
        updated_before: str,
        limit: Optional[int] = DEFAULT_PAGE_LIMIT_ITEMS,
    ) -> List[Item]:
        """
        Fetches items from a board by board ID by update date, useful for incremental fetching
        todo: add type hints for updated_after and updated_before and validate them
        """
        if not updated_after and not updated_before:
            raise ValueError(
                "Either updated_after or updated_before must be provided when fetching items by update date"
            )
        query_params = construct_updated_at_query_params(updated_after, updated_before)
        return self.fetch_all_items_by_board_id(board_id, query_params=query_params, limit=limit)

    def fetch_columns_by_board_id(self, board_id: Union[int, str]) -> MondayApiResponse:
        query = get_columns_by_board_query(board_id)
        return self.client.execute(query)
