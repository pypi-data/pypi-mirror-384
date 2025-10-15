# pyvider/protocols/tfprotov6/adapters/function_adapter.py
import json
from typing import Any

from provide.foundation import logger

# FIX: Import the type encoder from its new, correct location in pyvider.cty
from pyvider.cty.conversion.type_encoder import encode_cty_type_to_wire_json
import pyvider.protocols.tfprotov6.protobuf as pb


def dict_to_proto_function(func_data: dict[str, Any]) -> pb.Function | None:
    """Converts a dictionary representation of a function to a Protobuf Function."""
    func_name = func_data.get("name", "unknown")
    try:
        parameters = []
        for param_data in func_data.get("parameters", []):
            cty_type_obj = param_data.get("cty_type")
            if cty_type_obj is None:
                logger.warning(
                    f"Missing CtyType (key 'cty_type') for parameter '{param_data.get('name')}' in function '{func_name}'. Defaulting to CtyDynamic."
                )
                from pyvider.cty import CtyDynamic

                cty_type_obj = CtyDynamic()

            type_bytes = json.dumps(encode_cty_type_to_wire_json(cty_type_obj)).encode("utf-8")

            parameters.append(
                pb.Function.Parameter(
                    name=param_data.get("name", ""),
                    type=type_bytes,
                    description=param_data.get("description", ""),
                    allow_null_value=param_data.get("allow_null", False),
                    allow_unknown_values=True,
                )
            )

        return_value_obj = None
        if return_data := func_data.get("return"):
            cty_type_obj = return_data.get("cty_type")
            if cty_type_obj is None:
                logger.warning(
                    f"Missing CtyType (key 'cty_type') for return value in function '{func_name}'. Defaulting to CtyDynamic."
                )
                from pyvider.cty import CtyDynamic

                cty_type_obj = CtyDynamic()

            type_bytes = json.dumps(encode_cty_type_to_wire_json(cty_type_obj)).encode("utf-8")
            return_value_obj = pb.Function.Return(type=type_bytes)
        else:
            logger.warning(
                f"No explicit 'return' data or CtyType for function '{func_name}'. Defaulting return to CtyDynamic for Protobuf."
            )
            from pyvider.cty import CtyDynamic

            cty_type_obj = CtyDynamic()
            type_bytes = json.dumps(encode_cty_type_to_wire_json(cty_type_obj)).encode("utf-8")
            return_value_obj = pb.Function.Return(type=type_bytes)

        constructor_kwargs = {
            "parameters": parameters,
            "summary": func_data.get("summary", ""),
            "description": func_data.get("description", ""),
            "deprecation_message": func_data.get("deprecation_message", ""),
        }
        if return_value_obj:
            constructor_kwargs["return"] = return_value_obj

        return pb.Function(**constructor_kwargs)

    except Exception as e:
        logger.error(f"Error converting '{func_name}' to protobuf: {e}", exc_info=True)
        return None
