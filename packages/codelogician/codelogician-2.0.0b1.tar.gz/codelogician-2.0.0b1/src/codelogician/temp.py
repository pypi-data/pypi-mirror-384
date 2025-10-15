import os

import dotenv
import imandrax_api
from imandra.u.agents.code_logician.base.region_decomp import (
    DecomposeReqData,
    RegionDecomp,
)

from imandra.u.agents.code_logician.base.vg import (
    VG,
    VerifyReqData,
)

from imandra.u.agents.code_logician.imandrax import (
    DecomposeRes,
    VerifyRes,
)

from typing import Any

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
def proto_to_dict(proto_obj: Message) -> dict[Any, Any]:
    return MessageToDict(
        proto_obj,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )

from iml_query.query import (
    extract_decomp_req,
    extract_instance_req,
    extract_verify_req,
    iml_outline,
)
from rich import print
dotenv.load_dotenv(".env")

iml = """
let add_one (x: int) : int = x + 1
[@@decomp top ~prune:true ()]

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2

let decomp_double = double
[@@decomp top ~assuming: [%id is_positive] ~prune: true ()]

let square : int -> int = ()
[@@opaque]

let cube : int -> int = ()
[@@opaque]

axiom positive_addition x =
  x >= 0 ==> add_one x > x

theorem double_add_one x =
  double (add_one x) = add_one (add_one x) + x
[@@by auto]

verify (fun x -> x > 0 ==> double x > x)

let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify double_non_negative_is_increasing

instance (fun x -> x >= 0 ==> not (double x > x))


let two_x = (let x = 1 in double x)

eval (double 2)
"""


async def main():
    print(iml_outline(iml))

    verify_reqs = extract_verify_req(iml)
    instance_reqs = extract_instance_req(iml)
    decomp_reqs = extract_decomp_req(iml)

    async with imandrax_api.AsyncClient(
        url=imandrax_api.url_prod,
        auth_token="29U5z4uV1E1Jbg6bOzdT4kpJUoqSKgaoaVzlGyt1zQfNXjFd" #os.environ["IMANDRAX_API_KEY"],
    ) as c:
        eval_res = await c.eval_src(iml)

        decomp_results = [
            await c.decompose(**decomp_req) for decomp_req in decomp_reqs
        ]
        verify_results = [
            await c.verify_src(**verify_req) for verify_req in verify_reqs
        ]

    # Fill region decomps
    region_decomps = []
    for decomp_req, decomp_res in zip(decomp_reqs, decomp_results, strict=True):
        decomp_req_data_model = DecomposeReqData(**decomp_req)
        decomp_res_model = DecomposeRes.model_validate(
            proto_to_dict(decomp_res)
        )
        region_decomps.append(
            RegionDecomp(
                data=decomp_req_data_model,
                res=decomp_res_model,
            )
        )

    # Fill vgs
    vgs = []
    for verify_req, verify_res in zip(verify_reqs, verify_results, strict=True):
        verify_req_data_model = VerifyReqData(
            predicate=verify_req["src"], kind="verify"
        )
        verify_res_model = VerifyRes.model_validate(proto_to_dict(verify_res))
        vgs.append(
            VG(
                data=verify_req_data_model,
                res=verify_res_model,
            )
        )

    return region_decomps, vgs


if __name__ == "__main__":
    import asyncio

    region_decomps, vgs = asyncio.run(main())

    for i in region_decomps:
        print(i)
    for i in vgs:
        print(i)