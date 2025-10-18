import contextvars
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import requests
from .client import LlumoClient

_ctxLogger = contextvars.ContextVar("ctxLogger")
_ctxSessionID = contextvars.ContextVar("ctxSessionID")
_ctxLlumoRun = contextvars.ContextVar("ctxLlumoRun")


def getLogger():
    return _ctxLogger.get()


def getSessionID():
    return _ctxSessionID.get()


def getLlumoRun():
    return _ctxLlumoRun.get()


class LlumoSessionContext(LlumoClient):
    def __init__(self, logger, sessionID: Optional[str] = None):
        super().__init__(api_key=logger.apiKey, playground_id=logger.getPlaygroundID())
        self.sessionID = sessionID or str(uuid.uuid4().hex[:14])
        self.logger = logger
        self.apiKey = logger.apiKey
        self.threadLogger = None
        self.threadSessionID = None
        self.threadLlumoRun = None

    def start(self):
        self.threadLogger = _ctxLogger.set(self.logger)
        self.threadSessionID = _ctxSessionID.set(self.sessionID)

    def end(self):
        if self.threadLogger:
            _ctxLogger.reset(self.threadLogger)
        if self.threadSessionID:
            _ctxSessionID.reset(self.threadSessionID)
        if self.threadLlumoRun:
            _ctxLlumoRun.reset(self.threadLlumoRun)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, excType, excVal, excTb):
        self.end()


    def startLlumoRun(self, runName: str, rowID: str = "", columnID: str = "", runID: str = None):

        if runID is None:
            LlumoRunID = str(uuid.uuid4().hex[:16])
        else:
            LlumoRunID = runID


        # Proceed with using LlumoRunID, rowID, columnID...
        # if  rowID =="":
        #     rowID = str(uuid.uuid4().hex[:16])
        # if columnID == "":
        #     columnID = str(uuid.uuid4().hex[:16])

        currentTime = datetime(2025, 8, 2, 10, 20, 15, tzinfo=timezone.utc)
        createdAt = currentTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        llumoRun = {
            "logID": LlumoRunID,
            "runName": runName,
            "sessionID": self.sessionID,
            "playgroundID": self.logger.getPlaygroundID(),
            "workspaceID": self.logger.getWorkspaceID(),
            "source": "SDK",
            "rowID": rowID,
            "columnID": columnID,
            "email": self.logger.getUserEmailID(),
            "createdAt": createdAt,
            "createdBy": self.logger.getUserEmailID(),
            "status": "SUCCESS",
            "flow": [],
            "latency": 4200,
            "feedback": "",
            "dump": "",
            "steps": [],
        }
        self.threadLlumoRun = _ctxLlumoRun.set(llumoRun)

    def endLlumoRun(self):
        run = getLlumoRun()
        if run is None:
            return

        # STEP 1: Sort steps by timestamp
        steps = run.get("steps", [])
        sorted_steps = sorted(steps, key=lambda s: s.get("timestamp", 0))

        # STEP 2: Remove timestamp from each step before sending
        clean_steps = [
            {k: v for k, v in step.items() if k != "timestamp"} for step in sorted_steps
        ]
        run["steps"] = clean_steps

        # print(run["runName"])  # optional debug log

        # STEP 3: Send the payload
        url = "https://app.llumo.ai/api/create-debug-log"
        headers = {
            "Authorization": f"Bearer {self.logger.getWorkspaceID()}",
            "Content-Type": "application/json",
        }

        try:
            print(run)
            response = requests.post(url, headers=headers, json=run, timeout=20)
            response.raise_for_status()
            # print(response.json())
        except requests.exceptions.Timeout:
            # print("Request timed out.")
            pass
        except requests.exceptions.RequestException as e:
            pass

        # Cleanup
        if self.threadLlumoRun:
            _ctxLlumoRun.reset(self.threadLlumoRun)
            self.threadLlumoRun = None

    def endEvalRun(self):
        run = getLlumoRun()
        if run is None:
            return

        # STEP 1: Sort steps by timestamp
        steps = run.get("steps", [])
        # sorted_steps = sorted(steps, key=lambda s: s.get("timestamp", 0))

        # # STEP 2: Remove timestamp from each step before sending
        # clean_steps = [
        #     {k: v for k, v in step.items() if k != "timestamp"} for step in sorted_steps
        # ]
        # run["steps"] = clean_steps

        # print(run["runName"])  # optional debug log

        # STEP 3: Send the payload
        url = "https://backend-api.llumo.ai/api/v1/create-debug-log-for-sdk"
        headers = {
            "Authorization": f"Bearer {self.logger.getWorkspaceID()}",
            "Content-Type": "application/json",
        }
        # print(run)
        try:
            response = requests.post(url, headers=headers, json={"log":run}, timeout=20)
            response.raise_for_status()
            # print(response.json())
        except requests.exceptions.Timeout:
            print("Request timed out.")
        except requests.exceptions.RequestException as e:
            pass

        # Cleanup
        if self.threadLlumoRun:
            _ctxLlumoRun.reset(self.threadLlumoRun)
            self.threadLlumoRun = None

    def logStep(
        self,
        stepType: str,
        stepName: str,
        metadata: Optional[dict] = None,
    ):
        # print(f"logged: {stepType}")
        run = getLlumoRun()
        if run is None:
            raise RuntimeError("No active run to log steps.")

        # add step
        stepData = {
            "stepType": stepType,
            "stepName": stepName,
            "status": metadata.get("status", "SUCCESS"),
            "message": metadata.get("message", ""),
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).timestamp(),  # OPTIONAL
        }
        run["steps"].append(stepData)
        # set to context vars again in llumo run
        self.threadLlumoRun = _ctxLlumoRun.set(run)

    def logLlmStep(
        self,
        stepName: str,
        model: str,
        provider: str,
        inputTokens: int,
        outputTokens: int,
        # temperature: float,
        # promptTruncated: bool,
        latencyMs: int,
        prompt: str,
        output: str,
        status: str,
        # message: str,
    ):
        metadata = {
            "model": model,
            "provider": provider,
            "inputTokens": inputTokens,
            "outputTokens": outputTokens,
            # "temperature": temperature,
            # "promptTruncated": promptTruncated,
            "latencyMs": latencyMs,
            "prompt": prompt,
            "output": output,
            "status": status,
            # "message": message,
        }

        self.logStep("LLM", stepName, metadata)

    def logRetrieverStep(
        self,
        stepName: str,
        retrieverSource: str,
        topK: int,
        chunkSize,
        context : str,
        searchQuery: str,
        latencyMs: int,
        status: str
    ):
        metadata = {
            "retrieverSource": retrieverSource,
            "topK": topK,
            "chunkSize":chunkSize,
            "context": context,
            "searchQuery": searchQuery,
            "latencyMs": latencyMs,
            "status": status,
            # "message": message,
        }

        self.logStep("RETRIEVER", stepName, metadata)

    def logAgentStep(
        self,
        stepName: str,
        agentType: str,
        agentName: str,
        numStepsTaken: int,
        tools: List[str],
        query: str,
        status: str,
        # message: str,
    ):
        metadata = {
            "agentType": agentType,
            "agentName": agentName,
            "numStepsTaken": numStepsTaken,
            "tools": tools,
            "query": query,
            "status": status,
        #     "message": message,
         }
        self.logStep("AGENT", stepName, metadata)

    def logToolSelectorStep(
        self,
        stepName: str,
        selectorType: str,
        toolsRanked: List[Dict[str, Any]],
        selectedTool: str,
        reasoning: str,
        status: str,
        # message: str,
    ):
        metadata = {
            "selectorType": selectorType,
            "toolsRanked": toolsRanked,
            "selectedTool": selectedTool,
            "reasoning": reasoning,
            "status": status,
            # "message": message,
        }
        self.logStep("TOOL_SELECTOR", stepName, metadata)

    def logToolStep(
        self,
        stepName: str,
        toolName: str,
        description: str,
        input: Dict[str, Any],
        output: str,
        latencyMs: int,
        status: str,
        # message: str,
    ):
        metadata = {
            "toolName": toolName,
            "description":description,
            "input": input,
            "output": output,
            "latencyMs": latencyMs,
            "status": status,
            # "message": message,
        }
        self.logStep("TOOL", stepName, metadata)

    def logEvalStep(
        self,
        stepName: str,
        output: str,
        context: str,
        query: str,
        # total 7 keys add 4 more
        messageHistory: str,
        tools: str,
        intermediateSteps: str,
        groundTruth: str,
        analyticsScore: Dict[str, float],
        reasoning: Dict[str, str],
        classification: Dict[str, str],
        evalLabel: Dict[str, str],
        latencyMs: int,
        status: str,
        message: str,
    ):
        metadata = {
            "output": output,
            "context": context,
            "query": query,
            "messageHistory": messageHistory,
            "tools": tools,
            "intermediateSteps": intermediateSteps,
            "groundTruth": groundTruth,
            "analyticsScore": analyticsScore,
            "reasoning": reasoning,
            "classification": classification,
            "evalLabel": evalLabel,
            "latencyMs": latencyMs,
            "status": status,
            "message": message,
        }
        self.logStep("EVAL", stepName, metadata)

    def logFunctionCallStep(
        self,
        stepName: str,
        functionName: str,
        argsPassed: Dict[str, Any],
        output: Dict[str, Any],
        callMode: str,
        latencyMs: int,
        status: str,
        message: str,
    ):
        metadata = {
            "functionName": functionName,
            "argsPassed": argsPassed,
            "output": output,
            "callMode": callMode,
            "latencyMs": latencyMs,
            "status": status,
            "message": message,
        }
        self.logStep("FUNCTION_CALL", stepName, metadata)

    def logCompressionStep(
        self,
        stepName: str,
        prompt: str,
        promptTemplate: str,
        inputs: Dict[str, Any],
        compressedPrompt: str,
        inputToken: int,
        compressedToken: int,
        outputToken: int,
        output: str,
        compressedOutput: str,
        latencyMs: int,
        status: str,
        message: str,
    ):
        metadata = {
            "prompt": prompt,
            "promptTemplate": promptTemplate,
            "inputs": inputs,
            "compressedPrompt": compressedPrompt,
            "inputToken": inputToken,
            "compressedToken": compressedToken,
            "outputToken": outputToken,
            "output": output,
            "compressedOutput": compressedOutput,
            "latencyMs": latencyMs,
            "status": status,
            "message": message,
        }
        self.logStep("COMPRESSION", stepName, metadata)

    def logCustomScriptStep(
        self,
        stepName: str,
        inputs: Dict[str, Any],
        script: str,
        output: str,
        latencyMs: int,
        status: str,
        message: str,
    ):
        metadata = {
            "inputs": inputs,
            "script": script,
            "output": output,
            "latencyMs": latencyMs,
            "status": status,
            "message": message,
        }
        self.logStep("CUSTOM_SCRIPT", stepName, metadata)


    def logQueryStep(self,stepName,model,provider,inputTokens,query,status):
        metadata = {
            "model": model,
            "provider": provider,
            "inputTokens": inputTokens,
            "query": query,
            "status":status
        }
        self.logStep("QUERY", stepName, metadata)


