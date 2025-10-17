from typing import no_type_check

import pytest

from nuclia_models.events.activity_logs import (
    DEFAULT_SHOW_ASK_VALUES,
    DEFAULT_SHOW_CHAT_VALUES,
    DEFAULT_SHOW_SEARCH_VALUES,
    DEFAULT_SHOW_VALUES,
    ActivityLogsAsk,
    ActivityLogsAskQuery,
    ActivityLogsChat,
    ActivityLogsChatQuery,
    DownloadActivityLogsAskQuery,
    DownloadActivityLogsChatQuery,
    QueryFiltersAsk,
    QueryFiltersChat,
    QueryFiltersCommon,
    QueryFiltersSearch,
    QuestionFilter,
)


def test_query_filters_fields() -> None:
    chat_fields = set(QueryFiltersChat.model_fields.keys())
    ask_fields = set(QueryFiltersAsk.model_fields.keys())
    search_fields = set(QueryFiltersSearch.model_fields.keys())
    common_fields = set(QueryFiltersCommon.model_fields.keys())
    question_fields = set(QuestionFilter.model_fields.keys())

    # common_fields are part of chat, ask and search fields
    assert common_fields.issubset(chat_fields)
    assert common_fields.issubset(ask_fields)
    assert common_fields.issubset(search_fields)

    # question_fields are part of chat and ask
    assert question_fields.issubset(chat_fields)
    assert question_fields.issubset(ask_fields)

    # chat_fields + search_fields = ask_fields
    assert chat_fields.union(search_fields) == ask_fields

    # any of the search fields are part of the chat_fields (except the common fields and question fields)
    non_common_search_fields = search_fields - common_fields
    assert non_common_search_fields.intersection(chat_fields - common_fields) == question_fields


@no_type_check
def test_ask_and_chat_does_not_warn(recwarn: pytest.WarningsRecorder) -> None:
    _ = QueryFiltersAsk()
    _ = DownloadActivityLogsAskQuery(year_month="2025-05", filters=QueryFiltersAsk())
    _ = ActivityLogsAsk(year_month="2025-05", filters=QueryFiltersAsk())
    _ = ActivityLogsAskQuery(year_month="2025-05", filters=QueryFiltersAsk())

    _ = QueryFiltersChat()
    _ = DownloadActivityLogsChatQuery(year_month="2025-05", filters=QueryFiltersChat())
    _ = ActivityLogsChat(year_month="2025-05", filters=QueryFiltersChat())
    _ = ActivityLogsChatQuery(year_month="2025-05", filters=QueryFiltersChat())

    warnings_ = recwarn.list
    assert len(warnings_) == 0, "Expected no warnings"


def test_default_show_values() -> None:
    assert {"id", "date"} == DEFAULT_SHOW_VALUES
    assert {"id", "date", "question", "resources_count"} == DEFAULT_SHOW_SEARCH_VALUES
    assert {
        "id",
        "date",
        "question",
        "rephrased_question",
        "rag_strategies_names",
        "answer",
    } == DEFAULT_SHOW_CHAT_VALUES
    assert {
        "id",
        "date",
        "question",
        "rephrased_question",
        "rag_strategies_names",
        "answer",
        "resources_count",
    } == DEFAULT_SHOW_ASK_VALUES
