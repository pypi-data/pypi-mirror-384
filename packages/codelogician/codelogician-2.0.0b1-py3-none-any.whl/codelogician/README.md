# CodeLogician 2.0 (Server) 

CodeLogician v2.0 now contains a server for performing asynchronous formalization strategies for entire directories, interacting with the CodeLogician Agent (and soon, other agents) ito formalize the code, fix issues, generate test cases and perform formally verified modifications. 

**Note: CodeLogician requires `IMANDRA_UNI_KEY` to be set to a valid Imandra Universe API key. Get yours at https://www.imandra.ai**


To run the server for a starting directory:

```shell
codelogician start -d PATH_TO_DIRECTORY 
```

To run server in 'oneshot' mode:
```shell
codelogician oneshot -d PATH_TO_DIRECTORY
```
