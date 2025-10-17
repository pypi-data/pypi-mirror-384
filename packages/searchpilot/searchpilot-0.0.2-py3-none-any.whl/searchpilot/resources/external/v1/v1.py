# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .rules import (
    RulesResource,
    AsyncRulesResource,
    RulesResourceWithRawResponse,
    AsyncRulesResourceWithRawResponse,
    RulesResourceWithStreamingResponse,
    AsyncRulesResourceWithStreamingResponse,
)
from .steps import (
    StepsResource,
    AsyncStepsResource,
    StepsResourceWithRawResponse,
    AsyncStepsResourceWithRawResponse,
    StepsResourceWithStreamingResponse,
    AsyncStepsResourceWithStreamingResponse,
)
from .values import (
    ValuesResource,
    AsyncValuesResource,
    ValuesResourceWithRawResponse,
    AsyncValuesResourceWithRawResponse,
    ValuesResourceWithStreamingResponse,
    AsyncValuesResourceWithStreamingResponse,
)
from .accounts import (
    AccountsResource,
    AsyncAccountsResource,
    AccountsResourceWithRawResponse,
    AsyncAccountsResourceWithRawResponse,
    AccountsResourceWithStreamingResponse,
    AsyncAccountsResourceWithStreamingResponse,
)
from .sections import (
    SectionsResource,
    AsyncSectionsResource,
    SectionsResourceWithRawResponse,
    AsyncSectionsResourceWithRawResponse,
    SectionsResourceWithStreamingResponse,
    AsyncSectionsResourceWithStreamingResponse,
)
from .customers import (
    CustomersResource,
    AsyncCustomersResource,
    CustomersResourceWithRawResponse,
    AsyncCustomersResourceWithRawResponse,
    CustomersResourceWithStreamingResponse,
    AsyncCustomersResourceWithStreamingResponse,
)
from ...._compat import cached_property
from .experiments import (
    ExperimentsResource,
    AsyncExperimentsResource,
    ExperimentsResourceWithRawResponse,
    AsyncExperimentsResourceWithRawResponse,
    ExperimentsResourceWithStreamingResponse,
    AsyncExperimentsResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from .seo_experiment_results import (
    SeoExperimentResultsResource,
    AsyncSeoExperimentResultsResource,
    SeoExperimentResultsResourceWithRawResponse,
    AsyncSeoExperimentResultsResourceWithRawResponse,
    SeoExperimentResultsResourceWithStreamingResponse,
    AsyncSeoExperimentResultsResourceWithStreamingResponse,
)

__all__ = ["V1Resource", "AsyncV1Resource"]


class V1Resource(SyncAPIResource):
    @cached_property
    def accounts(self) -> AccountsResource:
        return AccountsResource(self._client)

    @cached_property
    def customers(self) -> CustomersResource:
        return CustomersResource(self._client)

    @cached_property
    def experiments(self) -> ExperimentsResource:
        return ExperimentsResource(self._client)

    @cached_property
    def rules(self) -> RulesResource:
        return RulesResource(self._client)

    @cached_property
    def sections(self) -> SectionsResource:
        return SectionsResource(self._client)

    @cached_property
    def seo_experiment_results(self) -> SeoExperimentResultsResource:
        return SeoExperimentResultsResource(self._client)

    @cached_property
    def steps(self) -> StepsResource:
        return StepsResource(self._client)

    @cached_property
    def values(self) -> ValuesResource:
        return ValuesResource(self._client)

    @cached_property
    def with_raw_response(self) -> V1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return V1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> V1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return V1ResourceWithStreamingResponse(self)


class AsyncV1Resource(AsyncAPIResource):
    @cached_property
    def accounts(self) -> AsyncAccountsResource:
        return AsyncAccountsResource(self._client)

    @cached_property
    def customers(self) -> AsyncCustomersResource:
        return AsyncCustomersResource(self._client)

    @cached_property
    def experiments(self) -> AsyncExperimentsResource:
        return AsyncExperimentsResource(self._client)

    @cached_property
    def rules(self) -> AsyncRulesResource:
        return AsyncRulesResource(self._client)

    @cached_property
    def sections(self) -> AsyncSectionsResource:
        return AsyncSectionsResource(self._client)

    @cached_property
    def seo_experiment_results(self) -> AsyncSeoExperimentResultsResource:
        return AsyncSeoExperimentResultsResource(self._client)

    @cached_property
    def steps(self) -> AsyncStepsResource:
        return AsyncStepsResource(self._client)

    @cached_property
    def values(self) -> AsyncValuesResource:
        return AsyncValuesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncV1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#accessing-raw-response-data-eg-headers
        """
        return AsyncV1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncV1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/adamsteele-sp/searchpilot-python#with_streaming_response
        """
        return AsyncV1ResourceWithStreamingResponse(self)


class V1ResourceWithRawResponse:
    def __init__(self, v1: V1Resource) -> None:
        self._v1 = v1

    @cached_property
    def accounts(self) -> AccountsResourceWithRawResponse:
        return AccountsResourceWithRawResponse(self._v1.accounts)

    @cached_property
    def customers(self) -> CustomersResourceWithRawResponse:
        return CustomersResourceWithRawResponse(self._v1.customers)

    @cached_property
    def experiments(self) -> ExperimentsResourceWithRawResponse:
        return ExperimentsResourceWithRawResponse(self._v1.experiments)

    @cached_property
    def rules(self) -> RulesResourceWithRawResponse:
        return RulesResourceWithRawResponse(self._v1.rules)

    @cached_property
    def sections(self) -> SectionsResourceWithRawResponse:
        return SectionsResourceWithRawResponse(self._v1.sections)

    @cached_property
    def seo_experiment_results(self) -> SeoExperimentResultsResourceWithRawResponse:
        return SeoExperimentResultsResourceWithRawResponse(self._v1.seo_experiment_results)

    @cached_property
    def steps(self) -> StepsResourceWithRawResponse:
        return StepsResourceWithRawResponse(self._v1.steps)

    @cached_property
    def values(self) -> ValuesResourceWithRawResponse:
        return ValuesResourceWithRawResponse(self._v1.values)


class AsyncV1ResourceWithRawResponse:
    def __init__(self, v1: AsyncV1Resource) -> None:
        self._v1 = v1

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithRawResponse:
        return AsyncAccountsResourceWithRawResponse(self._v1.accounts)

    @cached_property
    def customers(self) -> AsyncCustomersResourceWithRawResponse:
        return AsyncCustomersResourceWithRawResponse(self._v1.customers)

    @cached_property
    def experiments(self) -> AsyncExperimentsResourceWithRawResponse:
        return AsyncExperimentsResourceWithRawResponse(self._v1.experiments)

    @cached_property
    def rules(self) -> AsyncRulesResourceWithRawResponse:
        return AsyncRulesResourceWithRawResponse(self._v1.rules)

    @cached_property
    def sections(self) -> AsyncSectionsResourceWithRawResponse:
        return AsyncSectionsResourceWithRawResponse(self._v1.sections)

    @cached_property
    def seo_experiment_results(self) -> AsyncSeoExperimentResultsResourceWithRawResponse:
        return AsyncSeoExperimentResultsResourceWithRawResponse(self._v1.seo_experiment_results)

    @cached_property
    def steps(self) -> AsyncStepsResourceWithRawResponse:
        return AsyncStepsResourceWithRawResponse(self._v1.steps)

    @cached_property
    def values(self) -> AsyncValuesResourceWithRawResponse:
        return AsyncValuesResourceWithRawResponse(self._v1.values)


class V1ResourceWithStreamingResponse:
    def __init__(self, v1: V1Resource) -> None:
        self._v1 = v1

    @cached_property
    def accounts(self) -> AccountsResourceWithStreamingResponse:
        return AccountsResourceWithStreamingResponse(self._v1.accounts)

    @cached_property
    def customers(self) -> CustomersResourceWithStreamingResponse:
        return CustomersResourceWithStreamingResponse(self._v1.customers)

    @cached_property
    def experiments(self) -> ExperimentsResourceWithStreamingResponse:
        return ExperimentsResourceWithStreamingResponse(self._v1.experiments)

    @cached_property
    def rules(self) -> RulesResourceWithStreamingResponse:
        return RulesResourceWithStreamingResponse(self._v1.rules)

    @cached_property
    def sections(self) -> SectionsResourceWithStreamingResponse:
        return SectionsResourceWithStreamingResponse(self._v1.sections)

    @cached_property
    def seo_experiment_results(self) -> SeoExperimentResultsResourceWithStreamingResponse:
        return SeoExperimentResultsResourceWithStreamingResponse(self._v1.seo_experiment_results)

    @cached_property
    def steps(self) -> StepsResourceWithStreamingResponse:
        return StepsResourceWithStreamingResponse(self._v1.steps)

    @cached_property
    def values(self) -> ValuesResourceWithStreamingResponse:
        return ValuesResourceWithStreamingResponse(self._v1.values)


class AsyncV1ResourceWithStreamingResponse:
    def __init__(self, v1: AsyncV1Resource) -> None:
        self._v1 = v1

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithStreamingResponse:
        return AsyncAccountsResourceWithStreamingResponse(self._v1.accounts)

    @cached_property
    def customers(self) -> AsyncCustomersResourceWithStreamingResponse:
        return AsyncCustomersResourceWithStreamingResponse(self._v1.customers)

    @cached_property
    def experiments(self) -> AsyncExperimentsResourceWithStreamingResponse:
        return AsyncExperimentsResourceWithStreamingResponse(self._v1.experiments)

    @cached_property
    def rules(self) -> AsyncRulesResourceWithStreamingResponse:
        return AsyncRulesResourceWithStreamingResponse(self._v1.rules)

    @cached_property
    def sections(self) -> AsyncSectionsResourceWithStreamingResponse:
        return AsyncSectionsResourceWithStreamingResponse(self._v1.sections)

    @cached_property
    def seo_experiment_results(self) -> AsyncSeoExperimentResultsResourceWithStreamingResponse:
        return AsyncSeoExperimentResultsResourceWithStreamingResponse(self._v1.seo_experiment_results)

    @cached_property
    def steps(self) -> AsyncStepsResourceWithStreamingResponse:
        return AsyncStepsResourceWithStreamingResponse(self._v1.steps)

    @cached_property
    def values(self) -> AsyncValuesResourceWithStreamingResponse:
        return AsyncValuesResourceWithStreamingResponse(self._v1.values)
