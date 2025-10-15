from imandra.u.agents.code_logician.base.region_decomp import (
    DecomposeReqData,
    DecomposeRes,
    RegionDecomp,
    RawDecomposeReq,
    RegionStr
 
)


RawDecomposeReq ()

# RegionDecomp is container
# RawDecomposeRequest -> intermediate representation for constructing ImandraX commands, but this is created by LLMs from analyzing source code
# DecomposeReqData -> request that is sent to ImandraX (as supported by the ImandraX API) -> sent via Python lib
# DecomposeRes -> what gets returned from ImandraX 

# DecomposeRes => returned from ImandraX API
# - Artifact -> binary format that ImandraX uses (twine format) -> 
# - err:Empty -> (when error is Empty, then there's an error and we should )
# - errors: list[str]
# - task -> internal imandraX stuff
# - region_str -> 

# RegionStr
# -> constraints_str -> list of constraints
# -> invariant_str -> actual invariant
# -> model_str -> set of inputs for the test case 
# -> model_eval_str -> result of running test case 

RegionStr()


# VG -> 
# raw:RawVerifyReq -> produced by LLM when processing the source code file
# data:VerifyReqData -> gets sent to IMnadraX
# res:VerifyRes -> returned from ImandraX 


# VerifyRes -> one of the following will be set (unknown, err, proved, refuted, verified_upto)
# unknown-> 


#VerifyReqData 
# predicate -> the actual verification goal in IML
# kind -> verify/instance


#


from imandra.u.agents.code_logician.base.vg import (
    VG,
    VerifyReqData,
    RawVerifyReq,
    VerifyRes
)

from imandra.u.agents.code_logician.imandrax import Proved, Refuted, Model, ModelType


Refuted()
r1 = VerifyRes (proved=Proved(proof_pp="the proof"))
r2 = VerifyRes (refuted=Refuted(model=Model(m_type=ModelType(value="ibe"))))

VerifyRes()
Model("")
ModelType()
RawVerifyReq()
VerifyReqData()

VG(res=VerifyRes.model_validate( {"proved": {"proved_pp": "dummy"}} ),
    raw=RawVerifyReq.model_validate({"src_func_names": [], "iml_func_names": [], "description": "dummy", "logical_statement": "dummy"}))

VG( res=VerifyRes.model_validate( {"refuted": {"model": {"m_type": "Counter_example", "src":"dummy counterexample"}}}),
    data=VerifyReqData.model_validate ( {"predicate": "1 > 2", "kind": "verify"})
)

raw=RawVerifyReq.model_validate({"src_func_names": [], "iml_func_names": [], "description": "dummy", "logical_statement": "dummy"}))


dReq = DecomposeReqData(
    name="hello",

)

result = DecomposeRes(

)

regionD = RegionDecomp(raw=None, data=data, res=result)