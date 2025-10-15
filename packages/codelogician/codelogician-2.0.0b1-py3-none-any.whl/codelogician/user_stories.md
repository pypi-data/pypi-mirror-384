# 
# CodeLogician Server 
# 

CodeLogician Version 2.0 now contains a server for running formalization strategies for entire directories, interacting with CodeLogician Agent (and soon, other agents) in order to formalize the code, and do other things. 

### 1. Strategy:
Description:
- Strategy is both a worker thread and a algorithm for reasoning about source code directory with a specific reasoner/agent (our initial one is CodeLogician Agent, which converts code into Imandra Modeling Language/IML models).
- The Strategy may be started from "fresh" for a new directory, or using the existing cache file (we use `.cl_cache` file in the target directory). 

Information available:
    -
    -

Actions:
- Create a new strategy
  - API:
  - UI: `Overview`
- Delete strategy (from the server) - this will stop the strategy 
-

Formalizing a repo/directory
- Creating a new metamodel
- Doing something else  

### 2. MetaModel

Description:
- MetaModel is a data structure containing the underlying source code files for the target directory, along with their dependency graphs and formalizations (including statuses, etc). 
- It also contains a number of methods for searching the 

Data available:
- See summary broken down by 
- See the full "tree view" of 
- See if there's a way to 

### 3. Model

Data available:
- The original source code 
- Status (formalization status, etc.?)
- Results of running the CodeLogician Agent

Actions:
- Edit original source code
- Edit IML model (on disk)
- Change will be reflected onto the thing itself... 
    -- modify 
    -- do something else
    -- and elsewhere

### 4. Sketch:
Description:
- Sketches API is the mechanism by which AI coding assistants plan on making changes to the source code
- A Sketch is a consolidated IML model created by the user by specifying an "anchor" model. It's useful because when the algorithm wants to make a change, it searches the MetaModel for 
 
- Search for relevant "anchor model" - via embeddings, etc...
- Create a sketch from an anchor model:
    - Topologically sort 

Apply sketch changes back to the base models
- See what the changes would be before they're applied
- Apply them
- Get suggested changes to the original source code


