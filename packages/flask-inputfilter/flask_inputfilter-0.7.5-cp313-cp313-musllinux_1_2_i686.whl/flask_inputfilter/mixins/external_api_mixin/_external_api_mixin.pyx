# cython: language=c++
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

import re
from typing import Any

from flask_inputfilter.models.cimports cimport ExternalApiConfig
from flask_inputfilter.exceptions import ValidationError


cdef class ExternalApiMixin:

    _PLACEHOLDER_PATTERN = re.compile(r"{{(.*?)}}")

    @staticmethod
    cdef object call_external_api(
            ExternalApiConfig config,
            object fallback,
            dict[str, Any] validated_data
    ):
        """
        The function constructs a request based on the given API
        configuration and validated data, including headers, parameters,
        and other request settings. It utilizes the `requests` library
        to send the API call and processes the response. If a fallback
        value is supplied, it is returned in case of any failure during
        the API call. If no fallback is provided, a validation error is
        raised.

        **Parameters:**

        - **config** (*ExternalApiConfig*):
          An object containing the configuration details for the
          external API call, such as URL, headers, method, and API key.
        - **fallback** (*Any*):
          The value to be returned in case the external API call fails.
        - **validated_data** (*dict[str, Any]*):
          The dictionary containing data used to replace placeholders
          in the URL and parameters of the API request.

        **Returns:**

        - (*Optional[Any]*):
          The JSON-decoded response from the API, or the fallback
          value if the call fails and a fallback is provided.

        **Raises:**

        - **ValidationError**:
          Raised if the external API call does not succeed and no
          fallback value is provided.
        """
        import logging

        import requests

        logger = logging.getLogger(__name__)

        data_key = config.data_key

        requestData = {
            "headers": {},
            "params": {},
        }

        if config.api_key:
            requestData["headers"]["Authorization"] = (
                f"Bearer {config.api_key}"
            )

        if config.headers:
            requestData["headers"].update(config.headers)

        if config.params:
            requestData["params"] = ExternalApiMixin.replace_placeholders_in_params(
                config.params, validated_data
            )

        requestData["url"] = ExternalApiMixin.replace_placeholders(
            config.url, validated_data
        )
        requestData["method"] = config.method

        try:
            response = requests.request(timeout=config.timeout, **requestData)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.HTTPError:
            if fallback is None:
                logger.exception("External API HTTP error.")
                raise ValidationError(
                    f"External API call failed for field '{data_key}'."
                )
            return fallback
        except requests.exceptions.RequestException:
            if fallback is None:
                logger.exception("External API request failed unexpectedly.")
                raise ValidationError(
                    f"External API call failed for field '{data_key}'."
                )
            return fallback
        except ValueError:
            if fallback is None:
                logger.exception(
                    "External API response could not be parsed to json."
                )
                raise ValidationError(
                    f"External API call failed for field '{data_key}'."
                )
            return fallback

        return result.get(data_key) if data_key else result

    @staticmethod
    cdef inline str replace_placeholders(
            str value,
            dict[str, Any] validated_data
    ):
        """
        Replace all placeholders, marked with '{{ }}' in value
        with the corresponding values from validated_data.

        **Parameters:**

        - **value** (**str**): The string containing placeholders to be replaced.
        - **validated_data** (**dict[str, Any]**): The dictionary containing 
          the values to replace the placeholders with.

        **Returns:**

        - (*str*): The value with all placeholders replaced with
          the corresponding values from validated_data.
        """
        return ExternalApiMixin._PLACEHOLDER_PATTERN.sub(
            lambda match: str(validated_data.get(match.group(1))),
            value,
        )

    @staticmethod
    cdef dict[str, Any] replace_placeholders_in_params(
            dict[str, Any] params, dict[str, Any] validated_data
    ):
        """
        Replace all placeholders in params with the corresponding
        values from validated_data.

        **Parameters:**

        - **params** (*dict[str, Any]*): The params dictionary containing placeholders.
        - **validated_data** (*dict[str, Any]*): The dictionary containing 
          the values to replace the placeholders with.

        **Returns:**

        - (*dict[str, Any]*): The params dictionary with all placeholders replaced
          with the corresponding values from validated_data.
        """
        return {
            key: ExternalApiMixin.replace_placeholders(value, validated_data)
            if isinstance(value, str)
            else value
            for key, value in params.items()
        }
