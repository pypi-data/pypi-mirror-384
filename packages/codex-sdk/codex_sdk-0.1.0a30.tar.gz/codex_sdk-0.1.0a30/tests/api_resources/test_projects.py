# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from codex import Codex, AsyncCodex
from codex.types import (
    ProjectListResponse,
    ProjectReturnSchema,
    ProjectDetectResponse,
    ProjectRetrieveResponse,
    ProjectValidateResponse,
    ProjectInviteSmeResponse,
    ProjectRetrieveAnalyticsResponse,
)
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestProjects:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Codex) -> None:
        project = client.projects.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Codex) -> None:
        project = client.projects.create(
            config={
                "clustering_use_llm_matching": True,
                "eval_config": {
                    "custom_evals": {
                        "evals": {
                            "foo": {
                                "criteria": "criteria",
                                "eval_key": "eval_key",
                                "name": "name",
                                "context_identifier": "context_identifier",
                                "enabled": True,
                                "guardrailed_fallback_message": "guardrailed_fallback_message",
                                "is_default": True,
                                "priority": 0,
                                "query_identifier": "query_identifier",
                                "response_identifier": "response_identifier",
                                "should_escalate": True,
                                "should_guardrail": True,
                                "threshold": 0,
                                "threshold_direction": "above",
                            }
                        }
                    },
                    "default_evals": {
                        "context_sufficiency": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "query_ease": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_groundedness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_helpfulness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "trustworthiness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                    },
                },
                "llm_matching_model": "llm_matching_model",
                "llm_matching_quality_preset": "best",
                "lower_llm_match_distance_threshold": 0,
                "max_distance": 0,
                "query_use_llm_matching": True,
                "question_match_llm_prompt": "question_match_llm_prompt",
                "question_match_llm_prompt_with_answer": "question_match_llm_prompt_with_answer",
                "tlm_evals_model": "tlm_evals_model",
                "upper_llm_match_distance_threshold": 0,
            },
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            auto_clustering_enabled=True,
            description="description",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Codex) -> None:
        response = client.projects.with_raw_response.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Codex) -> None:
        with client.projects.with_streaming_response.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectReturnSchema, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Codex) -> None:
        project = client.projects.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Codex) -> None:
        response = client.projects.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Codex) -> None:
        with client.projects.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Codex) -> None:
        project = client.projects.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Codex) -> None:
        project = client.projects.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            auto_clustering_enabled=True,
            config={
                "clustering_use_llm_matching": True,
                "eval_config": {
                    "custom_evals": {
                        "evals": {
                            "foo": {
                                "criteria": "criteria",
                                "eval_key": "eval_key",
                                "name": "name",
                                "context_identifier": "context_identifier",
                                "enabled": True,
                                "guardrailed_fallback_message": "guardrailed_fallback_message",
                                "is_default": True,
                                "priority": 0,
                                "query_identifier": "query_identifier",
                                "response_identifier": "response_identifier",
                                "should_escalate": True,
                                "should_guardrail": True,
                                "threshold": 0,
                                "threshold_direction": "above",
                            }
                        }
                    },
                    "default_evals": {
                        "context_sufficiency": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "query_ease": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_groundedness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_helpfulness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "trustworthiness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                    },
                },
                "llm_matching_model": "llm_matching_model",
                "llm_matching_quality_preset": "best",
                "lower_llm_match_distance_threshold": 0,
                "max_distance": 0,
                "query_use_llm_matching": True,
                "question_match_llm_prompt": "question_match_llm_prompt",
                "question_match_llm_prompt_with_answer": "question_match_llm_prompt_with_answer",
                "tlm_evals_model": "tlm_evals_model",
                "upper_llm_match_distance_threshold": 0,
            },
            description="description",
            name="name",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Codex) -> None:
        response = client.projects.with_raw_response.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Codex) -> None:
        with client.projects.with_streaming_response.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectReturnSchema, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.update(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Codex) -> None:
        project = client.projects.list()
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Codex) -> None:
        project = client.projects.list(
            include_unaddressed_counts=True,
            limit=1,
            offset=0,
            order="asc",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            query="query",
            sort="created_at",
        )
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Codex) -> None:
        response = client.projects.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Codex) -> None:
        with client.projects.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectListResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Codex) -> None:
        project = client.projects.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert project is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Codex) -> None:
        response = client.projects.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert project is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Codex) -> None:
        with client.projects.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert project is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_detect(self, client: Codex) -> None:
        project = client.projects.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_detect_with_all_params(self, client: Codex) -> None:
        project = client.projects.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
            constrain_outputs=["string"],
            eval_config={
                "custom_evals": {
                    "evals": {
                        "foo": {
                            "criteria": "criteria",
                            "eval_key": "eval_key",
                            "name": "name",
                            "context_identifier": "context_identifier",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "is_default": True,
                            "priority": 0,
                            "query_identifier": "query_identifier",
                            "response_identifier": "response_identifier",
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        }
                    }
                },
                "default_evals": {
                    "context_sufficiency": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "query_ease": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "response_groundedness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "response_helpfulness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "trustworthiness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                },
            },
            messages=[
                {
                    "role": "assistant",
                    "audio": {"id": "id"},
                    "content": "string",
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "name": "name",
                    "refusal": "refusal",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            options={
                "custom_eval_criteria": [{}],
                "disable_persistence": True,
                "disable_trustworthiness": True,
                "log": ["string"],
                "max_tokens": 0,
                "model": "model",
                "num_candidate_responses": 0,
                "num_consistency_samples": 0,
                "num_self_reflections": 0,
                "reasoning_effort": "reasoning_effort",
                "similarity_measure": "similarity_measure",
                "use_self_reflection": True,
            },
            quality_preset="best",
            rewritten_question="rewritten_question",
            task="task",
            tools=[
                {
                    "function": {
                        "name": "name",
                        "description": "description",
                        "parameters": {},
                        "strict": True,
                    },
                    "type": "function",
                }
            ],
        )
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_detect(self, client: Codex) -> None:
        response = client.projects.with_raw_response.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_detect(self, client: Codex) -> None:
        with client.projects.with_streaming_response.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectDetectResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_detect(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.detect(
                project_id="",
                context="context",
                query="x",
                response="string",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_export(self, client: Codex) -> None:
        project = client.projects.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(object, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_export(self, client: Codex) -> None:
        response = client.projects.with_raw_response.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(object, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_export(self, client: Codex) -> None:
        with client.projects.with_streaming_response.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(object, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_export(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.export(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_invite_sme(self, client: Codex) -> None:
        project = client.projects.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        )
        assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_invite_sme(self, client: Codex) -> None:
        response = client.projects.with_raw_response.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_invite_sme(self, client: Codex) -> None:
        with client.projects.with_streaming_response.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_invite_sme(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.invite_sme(
                project_id="",
                email="email",
                page_type="query_log",
                url_query_string="url_query_string",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_analytics(self, client: Codex) -> None:
        project = client.projects.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_analytics_with_all_params(self, client: Codex) -> None:
        project = client.projects.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end=0,
            metadata_filters="metadata_filters",
            start=0,
        )
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_analytics(self, client: Codex) -> None:
        response = client.projects.with_raw_response.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_analytics(self, client: Codex) -> None:
        with client.projects.with_streaming_response.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_analytics(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.retrieve_analytics(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_validate(self, client: Codex) -> None:
        project = client.projects.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_validate_with_all_params(self, client: Codex) -> None:
        project = client.projects.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
            use_llm_matching=True,
            constrain_outputs=["string"],
            custom_eval_thresholds={"foo": 0},
            custom_metadata={},
            eval_scores={"foo": 0},
            messages=[
                {
                    "role": "assistant",
                    "audio": {"id": "id"},
                    "content": "string",
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "name": "name",
                    "refusal": "refusal",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            options={
                "custom_eval_criteria": [{}],
                "disable_persistence": True,
                "disable_trustworthiness": True,
                "log": ["string"],
                "max_tokens": 0,
                "model": "model",
                "num_candidate_responses": 0,
                "num_consistency_samples": 0,
                "num_self_reflections": 0,
                "reasoning_effort": "reasoning_effort",
                "similarity_measure": "similarity_measure",
                "use_self_reflection": True,
            },
            quality_preset="best",
            rewritten_question="rewritten_question",
            task="task",
            tools=[
                {
                    "function": {
                        "name": "name",
                        "description": "description",
                        "parameters": {},
                        "strict": True,
                    },
                    "type": "function",
                }
            ],
            x_client_library_version="x-client-library-version",
            x_integration_type="x-integration-type",
            x_source="x-source",
            x_stainless_package_version="x-stainless-package-version",
        )
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_validate(self, client: Codex) -> None:
        response = client.projects.with_raw_response.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = response.parse()
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_validate(self, client: Codex) -> None:
        with client.projects.with_streaming_response.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = response.parse()
            assert_matches_type(ProjectValidateResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_validate(self, client: Codex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.projects.with_raw_response.validate(
                project_id="",
                context="context",
                query="x",
                response="string",
            )


class TestAsyncProjects:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.create(
            config={
                "clustering_use_llm_matching": True,
                "eval_config": {
                    "custom_evals": {
                        "evals": {
                            "foo": {
                                "criteria": "criteria",
                                "eval_key": "eval_key",
                                "name": "name",
                                "context_identifier": "context_identifier",
                                "enabled": True,
                                "guardrailed_fallback_message": "guardrailed_fallback_message",
                                "is_default": True,
                                "priority": 0,
                                "query_identifier": "query_identifier",
                                "response_identifier": "response_identifier",
                                "should_escalate": True,
                                "should_guardrail": True,
                                "threshold": 0,
                                "threshold_direction": "above",
                            }
                        }
                    },
                    "default_evals": {
                        "context_sufficiency": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "query_ease": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_groundedness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_helpfulness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "trustworthiness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                    },
                },
                "llm_matching_model": "llm_matching_model",
                "llm_matching_quality_preset": "best",
                "lower_llm_match_distance_threshold": 0,
                "max_distance": 0,
                "query_use_llm_matching": True,
                "question_match_llm_prompt": "question_match_llm_prompt",
                "question_match_llm_prompt_with_answer": "question_match_llm_prompt_with_answer",
                "tlm_evals_model": "tlm_evals_model",
                "upper_llm_match_distance_threshold": 0,
            },
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            auto_clustering_enabled=True,
            description="description",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.create(
            config={},
            name="name",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectReturnSchema, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectRetrieveResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            auto_clustering_enabled=True,
            config={
                "clustering_use_llm_matching": True,
                "eval_config": {
                    "custom_evals": {
                        "evals": {
                            "foo": {
                                "criteria": "criteria",
                                "eval_key": "eval_key",
                                "name": "name",
                                "context_identifier": "context_identifier",
                                "enabled": True,
                                "guardrailed_fallback_message": "guardrailed_fallback_message",
                                "is_default": True,
                                "priority": 0,
                                "query_identifier": "query_identifier",
                                "response_identifier": "response_identifier",
                                "should_escalate": True,
                                "should_guardrail": True,
                                "threshold": 0,
                                "threshold_direction": "above",
                            }
                        }
                    },
                    "default_evals": {
                        "context_sufficiency": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "query_ease": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_groundedness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "response_helpfulness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                        "trustworthiness": {
                            "eval_key": "eval_key",
                            "name": "name",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "priority": 0,
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        },
                    },
                },
                "llm_matching_model": "llm_matching_model",
                "llm_matching_quality_preset": "best",
                "lower_llm_match_distance_threshold": 0,
                "max_distance": 0,
                "query_use_llm_matching": True,
                "question_match_llm_prompt": "question_match_llm_prompt",
                "question_match_llm_prompt_with_answer": "question_match_llm_prompt_with_answer",
                "tlm_evals_model": "tlm_evals_model",
                "upper_llm_match_distance_threshold": 0,
            },
            description="description",
            name="name",
        )
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectReturnSchema, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.update(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectReturnSchema, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.update(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.list()
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.list(
            include_unaddressed_counts=True,
            limit=1,
            offset=0,
            order="asc",
            organization_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            query="query",
            sort="created_at",
        )
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectListResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectListResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert project is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert project is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert project is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_detect(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_detect_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
            constrain_outputs=["string"],
            eval_config={
                "custom_evals": {
                    "evals": {
                        "foo": {
                            "criteria": "criteria",
                            "eval_key": "eval_key",
                            "name": "name",
                            "context_identifier": "context_identifier",
                            "enabled": True,
                            "guardrailed_fallback_message": "guardrailed_fallback_message",
                            "is_default": True,
                            "priority": 0,
                            "query_identifier": "query_identifier",
                            "response_identifier": "response_identifier",
                            "should_escalate": True,
                            "should_guardrail": True,
                            "threshold": 0,
                            "threshold_direction": "above",
                        }
                    }
                },
                "default_evals": {
                    "context_sufficiency": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "query_ease": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "response_groundedness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "response_helpfulness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                    "trustworthiness": {
                        "eval_key": "eval_key",
                        "name": "name",
                        "enabled": True,
                        "guardrailed_fallback_message": "guardrailed_fallback_message",
                        "priority": 0,
                        "should_escalate": True,
                        "should_guardrail": True,
                        "threshold": 0,
                        "threshold_direction": "above",
                    },
                },
            },
            messages=[
                {
                    "role": "assistant",
                    "audio": {"id": "id"},
                    "content": "string",
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "name": "name",
                    "refusal": "refusal",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            options={
                "custom_eval_criteria": [{}],
                "disable_persistence": True,
                "disable_trustworthiness": True,
                "log": ["string"],
                "max_tokens": 0,
                "model": "model",
                "num_candidate_responses": 0,
                "num_consistency_samples": 0,
                "num_self_reflections": 0,
                "reasoning_effort": "reasoning_effort",
                "similarity_measure": "similarity_measure",
                "use_self_reflection": True,
            },
            quality_preset="best",
            rewritten_question="rewritten_question",
            task="task",
            tools=[
                {
                    "function": {
                        "name": "name",
                        "description": "description",
                        "parameters": {},
                        "strict": True,
                    },
                    "type": "function",
                }
            ],
        )
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_detect(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectDetectResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_detect(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.detect(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectDetectResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_detect(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.detect(
                project_id="",
                context="context",
                query="x",
                response="string",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_export(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(object, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_export(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(object, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_export(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.export(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(object, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_export(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.export(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_invite_sme(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        )
        assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_invite_sme(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_invite_sme(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.invite_sme(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            email="email",
            page_type="query_log",
            url_query_string="url_query_string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectInviteSmeResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_invite_sme(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.invite_sme(
                project_id="",
                email="email",
                page_type="query_log",
                url_query_string="url_query_string",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_analytics(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_analytics_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end=0,
            metadata_filters="metadata_filters",
            start=0,
        )
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_analytics(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_analytics(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.retrieve_analytics(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectRetrieveAnalyticsResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_analytics(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.retrieve_analytics(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_validate(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_validate_with_all_params(self, async_client: AsyncCodex) -> None:
        project = await async_client.projects.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
            use_llm_matching=True,
            constrain_outputs=["string"],
            custom_eval_thresholds={"foo": 0},
            custom_metadata={},
            eval_scores={"foo": 0},
            messages=[
                {
                    "role": "assistant",
                    "audio": {"id": "id"},
                    "content": "string",
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "name": "name",
                    "refusal": "refusal",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            options={
                "custom_eval_criteria": [{}],
                "disable_persistence": True,
                "disable_trustworthiness": True,
                "log": ["string"],
                "max_tokens": 0,
                "model": "model",
                "num_candidate_responses": 0,
                "num_consistency_samples": 0,
                "num_self_reflections": 0,
                "reasoning_effort": "reasoning_effort",
                "similarity_measure": "similarity_measure",
                "use_self_reflection": True,
            },
            quality_preset="best",
            rewritten_question="rewritten_question",
            task="task",
            tools=[
                {
                    "function": {
                        "name": "name",
                        "description": "description",
                        "parameters": {},
                        "strict": True,
                    },
                    "type": "function",
                }
            ],
            x_client_library_version="x-client-library-version",
            x_integration_type="x-integration-type",
            x_source="x-source",
            x_stainless_package_version="x-stainless-package-version",
        )
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_validate(self, async_client: AsyncCodex) -> None:
        response = await async_client.projects.with_raw_response.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        project = await response.parse()
        assert_matches_type(ProjectValidateResponse, project, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_validate(self, async_client: AsyncCodex) -> None:
        async with async_client.projects.with_streaming_response.validate(
            project_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            context="context",
            query="x",
            response="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            project = await response.parse()
            assert_matches_type(ProjectValidateResponse, project, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_validate(self, async_client: AsyncCodex) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.projects.with_raw_response.validate(
                project_id="",
                context="context",
                query="x",
                response="string",
            )
