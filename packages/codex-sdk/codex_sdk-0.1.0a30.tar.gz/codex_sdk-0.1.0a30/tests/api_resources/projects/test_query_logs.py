# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from codex import Codex, AsyncCodex
from tests.utils import assert_matches_type
from codex._utils import parse_datetime
from codex.pagination import (
    SyncOffsetPageQueryLogs,
    AsyncOffsetPageQueryLogs,
    SyncOffsetPageQueryLogGroups,
    AsyncOffsetPageQueryLogGroups,
)
from codex.types.projects import (
    QueryLogListResponse,
    QueryLogRetrieveResponse,
    QueryLogListGroupsResponse,
    QueryLogListByGroupResponse,
    QueryLogUpdateMetadataResponse,
    QueryLogAddUserFeedbackResponse,
    QueryLogStartRemediationResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestQueryLogs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Codex) -> None:
        query_log = client.projects.query_logs.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.retrieve(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            client.projects.query_logs.with_raw_response.retrieve(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(SyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(SyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(SyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.list(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_user_feedback(self, client: Codex) -> None:
        query_log = client.projects.query_logs.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        )
        assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add_user_feedback(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add_user_feedback(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_add_user_feedback(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.add_user_feedback(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
                key="key",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            client.projects.query_logs.with_raw_response.add_user_feedback(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                key="key",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_by_group(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_by_group_with_all_params(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            needs_review=True,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            remediation_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_by_group(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_by_group(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_by_group(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.list_by_group(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_groups(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_groups_with_all_params(self, client: Codex) -> None:
        query_log = client.projects.query_logs.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            needs_review=True,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(SyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_groups(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(SyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_groups(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(SyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_groups(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.list_groups(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start_remediation(self, client: Codex) -> None:
        query_log = client.projects.query_logs.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_start_remediation(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_start_remediation(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_start_remediation(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.start_remediation(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            client.projects.query_logs.with_raw_response.start_remediation(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_metadata(self, client: Codex) -> None:
        query_log = client.projects.query_logs.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        )
        assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_metadata(self, client: Codex) -> None:
        response = client.projects.query_logs.with_raw_response.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = response.parse()
        assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_metadata(self, client: Codex) -> None:
        with client.projects.query_logs.with_streaming_response.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = response.parse()
            assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_metadata(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.query_logs.with_raw_response.update_metadata(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
                body={},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            client.projects.query_logs.with_raw_response.update_metadata(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                body={},
            )


class TestAsyncQueryLogs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.retrieve(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(QueryLogRetrieveResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.retrieve(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.retrieve(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AsyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(AsyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(AsyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.list(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(AsyncOffsetPageQueryLogs[QueryLogListResponse], query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.list(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_user_feedback(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        )
        assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add_user_feedback(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add_user_feedback(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.add_user_feedback(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(QueryLogAddUserFeedbackResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_add_user_feedback(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.add_user_feedback(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
                key="key",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.add_user_feedback(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                key="key",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_by_group(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_by_group_with_all_params(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            needs_review=True,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            remediation_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_by_group(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_by_group(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.list_by_group(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(QueryLogListByGroupResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_by_group(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.list_by_group(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_groups(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AsyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_groups_with_all_params(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            created_at_end=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_start=parse_datetime("2019-12-27T18:11:19.117Z"),
            custom_metadata="custom_metadata",
            expert_review_status="good",
            failed_evals=["string"],
            guardrailed=True,
            has_tool_calls=True,
            limit=1,
            needs_review=True,
            offset=0,
            order="asc",
            passed_evals=["string"],
            primary_eval_issue=["hallucination"],
            search_text="search_text",
            sort="created_at",
            tool_call_names=["string"],
            was_cache_hit=True,
        )
        assert_matches_type(AsyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_groups(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(AsyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_groups(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.list_groups(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(AsyncOffsetPageQueryLogGroups[QueryLogListGroupsResponse], query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_groups(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.list_groups(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start_remediation(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_start_remediation(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_start_remediation(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.start_remediation(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(QueryLogStartRemediationResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_start_remediation(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.start_remediation(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.start_remediation(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_metadata(self, async_client: AsyncCodex) -> None:
        query_log = await async_client.projects.query_logs.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        )
        assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_metadata(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.query_logs.with_raw_response.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        query_log = await response.parse()
        assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_metadata(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.query_logs.with_streaming_response.update_metadata(
            query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            body={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            query_log = await response.parse()
            assert_matches_type(QueryLogUpdateMetadataResponse, query_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_metadata(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.update_metadata(
                query_log_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                project_id="",
                body={},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `query_log_id` but received ''"):
            await async_client.projects.query_logs.with_raw_response.update_metadata(
                query_log_id="",
                project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                body={},
            )
