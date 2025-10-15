from typing import List, Optional

import skorplandgpt
from skorplandgpt._logging import verbose_logger
from skorplandgpt.constants import X_SKORPLANDGPT_DISABLE_CALLBACKS
from skorplandgpt.integrations.custom_logger import CustomLogger
from skorplandgpt.skorplandgpt_core_utils.llm_request_utils import (
    get_proxy_server_request_headers,
)
from skorplandgpt.proxy._types import CommonProxyErrors
from skorplandgpt.types.utils import StandardCallbackDynamicParams


class EnterpriseCallbackControls:
    @staticmethod
    def is_callback_disabled_dynamically(
            callback: skorplandgpt.CALLBACK_TYPES, 
            skorplandgpt_params: dict,
            standard_callback_dynamic_params: StandardCallbackDynamicParams
        ) -> bool:
            """
            Check if a callback is disabled via the x-skorplandgpt-disable-callbacks header or via `skorplandgpt_disabled_callbacks` in standard_callback_dynamic_params.
            
            Args:
                callback: The callback to check (can be string, CustomLogger instance, or callable)
                skorplandgpt_params: Parameters containing proxy server request info
                
            Returns:
                bool: True if the callback should be disabled, False otherwise
            """
            from skorplandgpt.skorplandgpt_core_utils.custom_logger_registry import (
                CustomLoggerRegistry,
            )

            try:
                disabled_callbacks = EnterpriseCallbackControls.get_disabled_callbacks(skorplandgpt_params, standard_callback_dynamic_params)
                verbose_logger.debug(f"Dynamically disabled callbacks from {X_SKORPLANDGPT_DISABLE_CALLBACKS}: {disabled_callbacks}")
                verbose_logger.debug(f"Checking if {callback} is disabled via headers. Disable callbacks from headers: {disabled_callbacks}")
                if disabled_callbacks is not None:
                    #########################################################
                    # premium user check
                    #########################################################
                    if not EnterpriseCallbackControls._premium_user_check():
                        return False
                    #########################################################
                    if isinstance(callback, str):
                        if callback.lower() in disabled_callbacks:
                            verbose_logger.debug(f"Not logging to {callback} because it is disabled via {X_SKORPLANDGPT_DISABLE_CALLBACKS}")
                            return True
                    elif isinstance(callback, CustomLogger):
                        # get the string name of the callback
                        callback_str = CustomLoggerRegistry.get_callback_str_from_class_type(callback.__class__)
                        if callback_str is not None and callback_str.lower() in disabled_callbacks:
                            verbose_logger.debug(f"Not logging to {callback_str} because it is disabled via {X_SKORPLANDGPT_DISABLE_CALLBACKS}")
                            return True
                return False
            except Exception as e:
                verbose_logger.debug(
                    f"Error checking disabled callbacks header: {str(e)}"
                )
                return False
    @staticmethod
    def get_disabled_callbacks(skorplandgpt_params: dict, standard_callback_dynamic_params: StandardCallbackDynamicParams) -> Optional[List[str]]:
        """
        Get the disabled callbacks from the standard callback dynamic params.
        """

        #########################################################
        # check if disabled via headers
        #########################################################
        request_headers = get_proxy_server_request_headers(skorplandgpt_params)
        disabled_callbacks = request_headers.get(X_SKORPLANDGPT_DISABLE_CALLBACKS, None)
        if disabled_callbacks is not None:
            disabled_callbacks = set([cb.strip().lower() for cb in disabled_callbacks.split(",")])
            return list(disabled_callbacks)
        

        #########################################################
        # check if disabled via request body
        #########################################################
        if standard_callback_dynamic_params.get("skorplandgpt_disabled_callbacks", None) is not None:
            return standard_callback_dynamic_params.get("skorplandgpt_disabled_callbacks", None)
        
        return None
    
    @staticmethod
    def _premium_user_check():
        from skorplandgpt.proxy.proxy_server import premium_user
        if premium_user:
            return True
        verbose_logger.warning(f"Disabling callbacks using request headers is an enterprise feature. {CommonProxyErrors.not_premium_user.value}")
        return False