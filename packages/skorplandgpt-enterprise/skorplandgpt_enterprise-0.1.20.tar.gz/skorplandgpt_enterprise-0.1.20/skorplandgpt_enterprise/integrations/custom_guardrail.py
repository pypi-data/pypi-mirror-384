from typing import List, Optional, Union

from skorplandgpt.types.guardrails import GuardrailEventHooks, Mode


class EnterpriseCustomGuardrailHelper:
    @staticmethod
    def _should_run_if_mode_by_tag(
        data: dict,
        event_hook: Optional[
            Union[GuardrailEventHooks, List[GuardrailEventHooks], Mode]
        ],
    ) -> Optional[bool]:
        """
        Assumes check for event match is done in `should_run_guardrail`
        Returns True if the guardrail should be run by tag
        """
        from skorplandgpt.skorplandgpt_core_utils.skorplandgpt_logging import (
            StandardLoggingPayloadSetup,
        )
        from skorplandgpt.proxy._types import CommonProxyErrors
        from skorplandgpt.proxy.proxy_server import premium_user

        if not premium_user:
            raise Exception(
                f"Setting tag based guardrail modes is only available in skorplandgpt-enterprise. {CommonProxyErrors.not_premium_user.value}."
            )

        if event_hook is None or not isinstance(event_hook, Mode):
            return None

        metadata: dict = data.get("skorplandgpt_metadata") or data.get("metadata", {})
        proxy_server_request = data.get("proxy_server_request", {})

        request_tags = StandardLoggingPayloadSetup._get_request_tags(
            metadata=metadata,
            proxy_server_request=proxy_server_request,
        )

        if request_tags and any(tag in event_hook.tags for tag in request_tags):
            return True
        elif event_hook.default and any(
            tag in event_hook.default for tag in request_tags
        ):
            return True

        return False
