import asyncio
from imandra.u.agents.code_logician.command import (
    EditStateElementCommand,
    EmbedCommand,
    InitStateCommand,
)

from imandra.u.agents.code_logician.graph import GraphState
from imandra.u.agents import create_thread_sync, get_remote_graph


from strategy.model import Embedding

src_code = """
def f(a, b):
    return a + b
"""

iml_code = """
let f a b = a + b
"""

graph = get_remote_graph("code_logician", api_key="29U5z4uV1E1Jbg6bOzdT4kpJUoqSKgaoaVzlGyt1zQfNXjFd")
create_thread_sync(graph)
gs = GraphState()
gs = gs.add_commands( [
    InitStateCommand(src_code=src_code, src_lang="python"),
    EmbedCommand(),
    ])

gs1, _ = asyncio.run(gs.run(graph))

res = gs1.steps[-1].message
assert res is not None

embedding_metadata = res["metadata"]
src_embedding = res["src_embeddings"]

for e in res["embedding"]:
    ee = Embedding (
        
    )

print (res['metadata'])
print (src_embedding)

# 3072
print ()
print ()
print (f"length is {len(src_embedding[0]['embedding'])}")
print ()
print ()