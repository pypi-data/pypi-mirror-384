import traceback
import boto3
import streamlit as st
import datetime
from datetime import UTC
import json
import math
import asyncio
import os
import dotenv
import copy
import uuid
from io import BytesIO

from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from typing import Dict, Union
from InlineAgent.agent.process_roc import ProcessROC
from InlineAgent.observability import Trace
import fsspec

def initialize_mcp_config(mcp_config_file:Union[None,str]=None):
    """Read MCP configuration from environment variable or default file."""
    # Check if MCP_CONFIG_URI is set in environment variables
    if mcp_config_file is not None:
        mcp_config_file = mcp_config_file
    elif 'MCP_CONFIG_URI' in os.environ:
        mcp_config_file = os.environ['MCP_CONFIG_URI']
    else:
        mcp_config_file = os.path.join(os.path.dirname(__file__), 'mcp.json')
    # Use fsspec to automatically detect and open the file from any supported filesystem
    with fsspec.open(mcp_config_file, 'r') as f:
        mcp_configs = json.load(f)['servers']
    servers_params = []

    for mcp_name, mcp_config in mcp_configs.items():
        # Step 1: Define MCP stdio parameters
        server_params = StdioServerParameters(
            command=mcp_config['command'],
            args=mcp_config['args'],
            env=dotenv.dotenv_values(mcp_config['envFile']) if 'envFile' in mcp_config else None,
        )
        servers_params.append(server_params)
        st.session_state['mcp_config'] = servers_params

@st.fragment
def download_section(files):
    """Fragment that updates only the download button without reloading the full page."""
    for file_strct in files:
        st.download_button(
            label=f"Download {file_strct['name']}",
            data=file_strct['bytes'],
            file_name=file_strct['name'],
        )
            
def make_full_prompt(tasks, additional_instructions, processing_type="sequential"):
    """Build a full prompt from tasks and instructions."""
    prompt = ''
    if processing_type == 'sequential':
        prompt += """
Please perform the following tasks sequentially. Be sure you do not 
perform any of the tasks in parallel. If a task will require information produced from a prior task, 
be sure to include the full text details as comprehensive input to the task.\n\n"""
    elif processing_type == "allow_parallel":
        prompt += """
Please perform as many of the following tasks in parallel where possible.
When a dependency between tasks is clear, execute those tasks in sequential order. 
If a task will require information produced from a prior task,
be sure to include the comprehensive text details as input to the task.\n\n"""

    for task_num, task in enumerate(tasks, 1):
        prompt += f"Task {task_num}. {task}\n"

    prompt += "\nBefore returning the final answer, review whether you have achieved the expected output for each task."

    if additional_instructions:
        prompt += f"\n{additional_instructions}"

    return prompt

def process_routing_trace(event, step, _sub_agent_name, _time_before_routing=None):
    """Process routing classifier trace events."""
   
    _route = event['trace']['trace']['orchestrationTrace']
    
    if 'invocationInput' in _route:
        #print("Processing modelInvocationInput")
        container = st.container(border=True)                            
        container.markdown(f"""**Choosing a collaborator for this request...**""")
        return datetime.datetime.now(), step, _sub_agent_name, None, None
        
    if 'modelInvocationOutput' in _route and _time_before_routing:
        #print("Processing modelInvocationOutput")
        _llm_usage = _route['modelInvocationOutput']['metadata']['usage']
        inputTokens = _llm_usage['inputTokens']
        outputTokens = _llm_usage['outputTokens']
        
        _route_duration = datetime.datetime.now() - _time_before_routing

        _raw_resp_str = _route['modelInvocationOutput']['rawResponse']['content']
        _raw_resp = json.loads(_raw_resp_str)
        _classification = _raw_resp['content'][0]['text'].replace('<a>', '').replace('</a>', '')

        if _classification == "undecidable":
            text = f"No matching collaborator. Revert to 'SUPERVISOR' mode for this request."
        elif _classification in (_sub_agent_name, 'keep_previous_agent'):
            step = math.floor(step + 1)
            text = f"Continue conversation with previous collaborator"
        else:
            _sub_agent_name = _classification
            step = math.floor(step + 1)
            text = f"Use collaborator: '{_sub_agent_name}'"

        time_text = f"Intent classifier took {_route_duration.total_seconds():,.1f}s"
        container = st.container(border=True)                            
        container.write(text)
        container.write(time_text)
        
        return step, _sub_agent_name, inputTokens, outputTokens

def process_orchestration_trace(event, agentClient, step):
    """Process orchestration trace events."""
    _orch = event['trace']['trace']['orchestrationTrace']
    inputTokens = 0
    outputTokens = 0
    
    if "invocationInput" in _orch:
        _input = _orch['invocationInput']
        
        if 'knowledgeBaseLookupInput' in _input:
            with st.expander("Using knowledge base", False, icon=":material/plumbing:"):
                st.write("knowledge base id: " + _input["knowledgeBaseLookupInput"]["knowledgeBaseId"])
                st.write("query: " + _input["knowledgeBaseLookupInput"]["text"])
                
        if "actionGroupInvocationInput" in _input:
            function = _input["actionGroupInvocationInput"]["function"]
            with st.expander(f"Invoking Tool - {function}", False, icon=":material/plumbing:"):
                st.write("function : " + function)
                st.write("type: " + _input["actionGroupInvocationInput"]["executionType"])
                if 'parameters' in _input["actionGroupInvocationInput"]:
                    st.write("*Parameters*")
                    params = _input["actionGroupInvocationInput"]["parameters"]
                    st.table({
                        'Parameter Name': [p["name"] for p in params],
                        'Parameter Value': [p["value"] for p in params]
                    })

        if 'codeInterpreterInvocationInput' in _input:
            with st.expander("Code interpreter tool usage", False, icon=":material/psychology:"):
                gen_code = _input['codeInterpreterInvocationInput']['code']
                st.code(gen_code, language="python")
                    
    if "modelInvocationOutput" in _orch:
        if "usage" in _orch["modelInvocationOutput"]["metadata"]:
            inputTokens = _orch["modelInvocationOutput"]["metadata"]["usage"]["inputTokens"]
            outputTokens = _orch["modelInvocationOutput"]["metadata"]["usage"]["outputTokens"]
                    
    if "rationale" in _orch:
        if "agentId" in event["trace"]:
            agentData = agentClient.get_agent(agentId=event["trace"]["agentId"])
            agentName = agentData["agent"]["agentName"]
            chain = event["trace"]["callerChain"]
            
            container = st.container(border=True)
            
            if len(chain) <= 1:
                step = math.floor(step + 1)
                container.markdown(f"""#### Step  :blue[{round(step,2)}]""")
            else:
                step = step + 0.1
                container.markdown(f"""###### Step {round(step,2)} Sub-Agent  :red[{agentName}]""")
            
            container.write(_orch["rationale"]["text"])

    if "observation" in _orch:
        _obs = _orch['observation']
        
        if 'knowledgeBaseLookupOutput' in _obs:
            with st.expander("Knowledge Base Response", False, icon=":material/psychology:"):
                _refs = _obs['knowledgeBaseLookupOutput']['retrievedReferences']
                _ref_count = len(_refs)
                st.write(f"{_ref_count} references")
                for i, _ref in enumerate(_refs, 1):
                    st.write(f"  ({i}) {_ref['content']['text'][0:200]}...")

        if 'actionGroupInvocationOutput' in _obs:
            with st.expander("Tool Response", False, icon=":material/psychology:"):
                st.write(_obs['actionGroupInvocationOutput']['text'])

        if 'codeInterpreterInvocationOutput' in _obs:
            with st.expander("Code interpreter tool usage", False, icon=":material/psychology:"):
                if 'executionOutput' in _obs['codeInterpreterInvocationOutput']:
                    raw_output = _obs['codeInterpreterInvocationOutput']['executionOutput']
                    st.code(raw_output)

                if 'executionError' in _obs['codeInterpreterInvocationOutput']:
                    error_text = _obs['codeInterpreterInvocationOutput']['executionError']
                    st.write(f"Code interpretation error: {error_text}")

                if 'files' in _obs['codeInterpreterInvocationOutput']:
                    files_generated = _obs['codeInterpreterInvocationOutput']['files']
                    st.write(f"Code interpretation files generated:\n{files_generated}")

        if 'finalResponse' in _obs:
            with st.expander("Agent Response", False, icon=":material/psychology:"):
                st.write(_obs['finalResponse']['text'])
            
    return step, inputTokens, outputTokens

class InlineAgentUI(InlineAgent):
    def __init__(self, agent_client, **kwargs):
        super().__init__(**kwargs)
        self.agent_client = agent_client

    async def invoke(
        self,
        input_text: str,
        enable_trace: bool = True,
        session_id: str = str(uuid.uuid4()),
        end_session: bool = False,
        session_state: Dict = None,
        add_citation: bool = False,
        process_response: bool = True,
        truncate_response: int = None,
        streaming_configurations: Dict = {"streamFinalResponse": False},
        bedrock_model_configurations: Dict = {
            "performanceConfig": {"latency": "standard"}
        },
    ):
        if session_state is None:
                session_state = {}
        agent_answer = ""

        print(f"SessionId: {session_id}")
        if "returnControlInvocationResults" in session_state:
            raise ValueError(
                "returnControlInvocationResults key is not supported in inlineSessionState"
            )

        if "invocationId" in session_state:
            raise ValueError("invocationId key is not supported in inlineSessionState")


        bedrock_agent_runtime = boto3.Session(profile_name=self.profile).client(
            "bedrock-agent-runtime"
        )

        inlineSessionState = copy.deepcopy(session_state)
        
        while not agent_answer:
            # print(self.get_invoke_params())
            if inlineSessionState:
                response = bedrock_agent_runtime.invoke_inline_agent(
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                    endSession=end_session,
                    inlineSessionState=inlineSessionState,
                    streamingConfigurations=streaming_configurations,
                    bedrockModelConfigurations=bedrock_model_configurations,
                    **self.get_invoke_params(),
                )
            else:
                response = bedrock_agent_runtime.invoke_inline_agent(
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                    endSession=end_session,
                    streamingConfigurations=streaming_configurations,
                    bedrockModelConfigurations=bedrock_model_configurations,
                    **self.get_invoke_params(),
                )

            inlineSessionState = copy.deepcopy(session_state)

            # Process response
            step = 0.0
            _sub_agent_name = " "
            _time_before_routing = None
            inputTokens = 0
            outputTokens = 0
            _total_llm_calls = 0
            
            with st.spinner("Processing ....."):
                for event in response.get("completion"):
                    if "returnControl" in event:
                        inlineSessionState = await ProcessROC.process_roc(
                            inlineSessionState=inlineSessionState,
                            roc_event=event["returnControl"],
                            tool_map=self.tool_map,
                        )
                    if "trace" in event:
                        if 'orchestrationTrace' in event['trace']['trace']:
                            #print("Processing routing trace...")
                            result = process_routing_trace(event, step, _sub_agent_name, _time_before_routing)
                            if result:
                                if len(result) == 5:  # Initial invocation
                                    #print("Initial routing invocation")
                                    _time_before_routing, step, _sub_agent_name, in_tokens, out_tokens = result
                                    if in_tokens and out_tokens:
                                        inputTokens += in_tokens
                                        outputTokens += out_tokens
                                        _total_llm_calls += 1
                                else:  # Subsequent invocation
                                    #print("Subsequent routing invocation")
                                    step, _sub_agent_name, in_tokens, out_tokens = result
                                    if in_tokens and out_tokens:
                                        inputTokens += in_tokens
                                        outputTokens += out_tokens
                                        _total_llm_calls += 1

                                
                        if "orchestrationTrace" in event["trace"]["trace"]:
                            result = process_orchestration_trace(event, self.agent_client, step)
                            if result:
                                step, in_tokens, out_tokens = result
                                if in_tokens and out_tokens:
                                    inputTokens += in_tokens
                                    outputTokens += out_tokens
                                    _total_llm_calls += 1

                    # Get Final Answer
                    if "chunk" in event:
                        data = event["chunk"]["bytes"]
                        agent_answer += data.decode("utf8")

                    if "files" in event:
                        download_section(event["files"]['files'])
                        for file in event["files"]['files']:
                            if file['type'].startswith('image/'):
                                st.image(BytesIO(file['bytes']), caption=file['name'])
                # Display token usage at the end
                container = st.container(border=True)
                container.markdown("Total Input Tokens : **" + str(inputTokens) + "**")
                container.markdown("Total Output Tokens : **" + str(outputTokens) + "**")
                container.markdown("Total LLM Calls : **" + str(_total_llm_calls) + "**")
        
        return agent_answer

async def invoke_agent(input_text, session_id):
    """Main agent invocation and response processing."""
    # Process tasks if any
    _tasks = []
    _bot_config = st.session_state['bot_config']
    # for _task_name in task_yaml_content.keys():
    #     _curr_task = Task(_task_name, task_yaml_content, _bot_config['inputs'])
    #     _tasks.append(_curr_task)
        
    if len(_tasks) > 0:
        additional_instructions = _bot_config.get('additional_instructions')
        messagesStr = make_full_prompt(_tasks, additional_instructions)
    else:
        messagesStr = input_text

    # Invoke agent
    try:
        agents_client = []
        for server_params in st.session_state['mcp_config']:
            agent_client = MCPStdio.create(server_params=server_params)
            agents_client.append(agent_client)
        agents_client = await asyncio.gather(*agents_client)

        action_group = ActionGroup(
                    name="ActionGroup",
                    description="Agent that can use mcp",
                    mcp_clients=agents_client,
                )
        response = await InlineAgentUI(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly assistant that can use MCP tools. """,
            # Step 4.3: Provide the agent name and action group
            agent_name=_bot_config['agent_name'],
            action_groups=[
                action_group,
                {
                    "name": "CodeInterpreter",
                    "builtin_tools": {
                        "parentActionGroupSignature": "AMAZON.CodeInterpreter"
                    },
                }
            ],
            agent_client=agent_client
        ).invoke(
            input_text=messagesStr
        )
    except Exception as e:
        print(f"Error invoking agent: {traceback.format_exc()}")
        raise e

    return response

