import os

import imandrax_api
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from imandrax_api import Client
from rich import print

# from utils.imandra.imandrax.proto_models import (
import imandrax_api
from imandrax_api import Client
from imandra.u.agents.code_logician.base.imandrax import DecomposeRes, EvalRes, PO_Res, ErrorMessage

from imandra.core import Client, DecomposeRes, EvalRes, PO_Res, ErrorMessage


def proto_to_dict(proto_obj: Message) -> dict:
    """imandrax-api returns protobuf messages, this function converts them to
    dictionaries"""
    return MessageToDict(
        proto_obj,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )


#IMANDRAX_URL="https://api.imandra.ai/v1beta1”
#IMANDRAX_API_KEY="29U5z4uV1E1Jbg6bOzdT4kpJUoqSKgaoaVzlGyt1zQfNXjFd"


def get_client():
    url = imandrax_api.url_prod
    if not url:
        raise ValueError("IMANDRAX_URL is not set")
    return Client(
        url=url,
        #auth_token=os.getenv("IMANDRAX_API_KEY"),
        auth_token="29U5z4uV1E1Jbg6bOzdT4kpJUoqSKgaoaVzlGyt1zQfNXjFd"
    )

iml_code = """
let f x = x + 2

let g x = if x < 0 then (- x) else (x + 5)
[@@decomp top ()]

verify (fun x -> g x > 0)
"""


def main():
    c = get_client()
    eval_res_data = c.eval_src(src="let = 123+kkkk$$$")
  
    # Convert proto messages to dictionaries
    eval_res_data = proto_to_dict(eval_res_data)

    #print(eval_res_data)

    # Parse proto messages to pydantic.BaseModel instances
    # EvalRes.success is a boolean indicating formalization status
    eval_res = EvalRes.model_validate(eval_res_data)

    print(eval_res)

#    verify_res: PO_Res = eval_res.po_results[0]
#    print(verify_res)

#    decomp_res: DecomposeRes = eval_res.decomp_results[0]
#    print(decomp_res)


if __name__ == "__main__":
    main()

    #c = get_client()

    #c.eval_src ('let f x = if x > 0 then if x * x < 0 then x else x + 1 else x')


    #print (c.decompose('f'))