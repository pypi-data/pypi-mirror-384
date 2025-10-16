"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_usage_mcp_server.server import mcp


class TestUsageTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_usage_mcp_server.server.get_usage_client")
    async def test_get_summarized_usage(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_request_summarized_response = create_autospec(oci.response.Response)
        mock_request_summarized_response.data = oci.usage_api.models.QueryCollection(
            items=[
                oci.usage_api.models.UsageSummary(
                    compartment_id="test_compartment_id",
                    compartment_name="test_compartment_name",
                    computed_amount=6.731118997232,
                    computed_quantity=69.842410393953,
                    service="Database",
                )
            ]
        )

        mock_client.request_summarized_usages.return_value = (
            mock_request_summarized_response
        )
        print("mock response", mock_request_summarized_response)
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_summarized_usage",
                    {
                        "tenant_id": "test_tenant_id",
                        "start_time": "2023-01-01T00:00:00Z",
                        "end_time": "2023-01-02T00:00:00Z",
                        "group_by": ["compartment"],
                        "compartment_depth": 1.0,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["compartment_id"] == "test_compartment_id"
            assert result[0]["service"] == "Database"
            assert result[0]["computed_amount"] == 6.731118997232
