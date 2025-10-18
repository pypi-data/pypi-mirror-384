import requests


import time
import re
import json
import uuid
import warnings
import os
import itertools
import pandas as pd
from typing import List, Dict
from .models import AVAILABLEMODELS, getProviderFromModel, Provider
from .execution import ModelExecutor
from .exceptions import LlumoAIError
from .helpingFuntions import *
from .sockets import LlumoSocketClient
from .functionCalling import LlumoAgentExecutor
from .chains import LlumoDataFrameResults, LlumoDictResults
import threading
from tqdm import tqdm

pd.set_option("future.no_silent_downcasting", True)

postUrl = "https://redskull.llumo.ai/api/process-playground"

# postUrl = "http://localhost:4747/api/process-playground"
fetchUrl = "https://redskull.llumo.ai/api/get-cells-data"

# fetchUrl = "http://localhost:4747/api/get-cells-data"
fetchMissingEvalUrl = "https://redskull.llumo.ai/api/get-missing-keys"
socketDataUrl = "https://redskull.llumo.ai/api/eval/get-awaited"

validateUrl = "https://app.llumo.ai/api/workspace-details"
socketUrl = "https://redskull.llumo.ai/"
# socketUrl = "http://localhost:4747/"
createEvalUrl = "https://backend-api.llumo.ai/api/v1/create-debug-log-for-sdk"
# createEvalUrl = "http://localhost:4545/api/v1/create-debug-log-for-sdk"


class LlumoClient:

    def __init__(self, api_key, playground_id=None):
        self.apiKey = api_key
        self.playgroundID = playground_id
        self.evalData = []
        self.evals = []
        self.processMapping = {}
        self.definationMapping = {}

    def validateApiKey(self, evalName="Input Bias"):
        headers = {
            "Authorization": f"Bearer {self.apiKey}",
            "Content-Type": "application/json",
        }
        reqBody = {"analytics": [evalName]}

        try:

            response = requests.post(url=validateUrl, json=reqBody, headers=headers)

        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            raise LlumoAIError.RequestFailed(detail=str(e))

        if response.status_code == 401:
            raise LlumoAIError.InvalidApiKey()

        # Handle other common status codes
        if response.status_code == 404:
            raise LlumoAIError.RequestFailed(
                detail=f"Endpoint not found (404): {validateUrl}"
            )

        if response.status_code != 200:
            raise LlumoAIError.RequestFailed(
                detail=f"Unexpected status code: {response.status_code}"
            )

        # Try to parse JSON
        try:
            data = response.json()
            # print(data)
        except ValueError as e:
            print(f"JSON parsing error: {str(e)}")
            # print(f"Response content that could not be parsed: {response.text[:1000]}...")
            raise LlumoAIError.InvalidJsonResponse()

        if "data" not in data or not data["data"]:
            # print(f"Invalid API response structure: {data}")
            raise LlumoAIError.InvalidApiResponse()

        try:
            self.hitsAvailable = data["data"]["data"].get("remainingHits", 0)
            self.workspaceID = data["data"]["data"].get("workspaceID")
            self.evalDefinition = data["data"]["data"]["analyticsMapping"]
            self.socketToken = data["data"]["data"].get("token")
            # print(self.socketToken)
            self.hasSubscribed = data["data"]["data"].get("hasSubscr"
                                                          "ibed", False)
            self.trialEndDate = data["data"]["data"].get("trialEndDate", None)
            self.subscriptionEndDate = data["data"]["data"].get(
                "subscriptionEndDate", None
            )
            self.email = data["data"]["data"].get("email", None)

            self.definationMapping[evalName] = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
            )
            self.categories = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("categories", {})
            )
            self.evaluationStrictness = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("evaluationStrictness", {})
            )
            self.grammarCheckOutput = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("grammarCheckOutput", {})
            )
            self.insightsLength = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("insightsLength", {})
            )
            self.insightsLevel = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("insightsLevel", {})
            )
            self.executionDependency = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("executionDependency", {})
            )
            self.sampleData = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("sampleData", {})
            )
            self.numJudges = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("numJudges", {})
            )
            self.penaltyBonusInstructions = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("penaltyBonusInstructions", [])
            )
            self.probableEdgeCases = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("probableEdgeCases", [])
            )
            self.fieldMapping = (
                data.get("data", {})
                .get("data", {})
                .get("analyticsMapping", {})
                .get(evalName, "")
                .get("fieldMapping", [])
            )

        except Exception as e:
            # print(f"Error extracting data from response: {str(e)}")
            raise LlumoAIError.UnexpectedError(detail=evalName)

    def postBatch(self, batch, workspaceID):
        payload = {
            "batch": json.dumps(batch),
            "runType": "FULL_EVAL_RUN",
            "workspaceID": workspaceID,
        }
        # socketToken here if the "JWD" token
        headers = {
            "Authorization": f"Bearer {self.socketToken}",
            "Content-Type": "application/json",
        }
        try:
            print(postUrl)
            response = requests.post(postUrl, json=payload, headers=headers)
            print(f"Post API Status Code: {response.status_code}")
            print(response.text)
            # print(response.status_code)

        except Exception as e:
            print(f"Error in posting batch: {e}")

    
    def fetchDataForMissingKeys(self, workspaceID, missingKeys: list):
    # Define the URL and prepare the payload
       
        payload = {
            "workspaceID": workspaceID,
            "missingKeys": missingKeys
        }

        headers = {
            "Authorization": f"Bearer {self.socketToken}",
            "Content-Type": "application/json",
        }
        
        try:
            # Send a POST request to the API
            response = requests.post(fetchMissingEvalUrl, json=payload, headers=headers)
            
            # Check if the response is successful
            if response.status_code == 200:
                # Parse the JSON data from the response
                data = response.json().get("data", {})
                
                
                # Prepare the list of all data values in the desired format
                result_list = []
                for key, value in data.items():
                    # Create a dictionary for each item in the response data
                    result_list.append({
                        key: {
                            "value": value.get("value"),
                            "fullEval": value.get("fullEval", {}),
                            "runLog": value.get("runLog", {}),
                            "evallist": value.get("evallist", [])
                        }
                    })
                
                print("Fetched data for missing keys:", result_list)
                return result_list
            else:
                print(f"Failed to fetch data. Status Code: {response.status_code}")
                return []

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    
    def createRunForEvalMultiple(self, smartLog):
        payload = {
            "log": smartLog
        }
        # socketToken here if the "JWD" token
        headers = {
            # "Authorization": f"Bearer {self.socketToken}",
            "Content-Type": "application/json",
        }
        try:
            # print(postUrl)
            print(createEvalUrl)
            print(payload)
            print(headers)
            response = requests.post(createEvalUrl, json=payload, headers=headers)

            print(f"Post API Status Code: {response.status_code}")
            print(response.text)
            # print(response.status_code)

        except Exception as e:
            print(f"Error in posting batch: {e}")


    def postDataStream(self, batch, workspaceID):
        payload = {
            "batch": json.dumps(batch),
            "runType": "DATA_STREAM",
            "workspaceID": workspaceID,
        }
        # socketToken here if the "JWD" token
        headers = {
            "Authorization": f"Bearer {self.socketToken}",
            "Content-Type": "application/json",
        }
        try:
            # print(postUrl)
            response = requests.post(postUrl, json=payload, headers=headers)
            # print(f"Post API Status Code: {response.status_code}")
            # print(response.text)

        except Exception as e:
            print(f"Error in posting batch: {e}")

    def AllProcessMapping(self):
        for batch in self.allBatches:
            for record in batch:
                rowId = record["rowID"]
                colId = record["columnID"]
                pid = f"{rowId}-{colId}-{colId}"
                self.processMapping[pid] = record

    def finalResp(self, results):
        seen = set()
        uniqueResults = []

        for item in results:
            for rowID in item:  # Each item has only one key
                # for rowID in item["data"]:
                if rowID not in seen:
                    seen.add(rowID)
                    uniqueResults.append(item)

        return uniqueResults

    # this function allows the users to run exactl one eval at a time
    def evaluate(
        self,
        data,
        eval="Response Completeness",
        prompt_template="",
        outputColName="output",
        createExperiment: bool = False,
        _tocheck=True,
    ):

        # converting it into a pandas dataframe object
        dataframe = pd.DataFrame(data)

        # check for dependencies for the selected eval metric
        metricDependencies = checkDependency(
            eval, columns=list(dataframe.columns), tocheck=_tocheck
        )
        if metricDependencies["status"] == False:
            raise LlumoAIError.dependencyError(metricDependencies["message"])

        results = {}
        try:
            socketID = self.socket.connect(timeout=150)

            # Ensure full connection before proceeding
            max_wait_secs = 20
            waited_secs = 0
            while not self.socket._connection_established.is_set():
                time.sleep(0.1)
                waited_secs += 0.1
                if waited_secs >= max_wait_secs:
                    raise RuntimeError(
                        "Timeout waiting for server 'connection-established' event."
                    )

            rowIdMapping = {}

            print(f"\n======= Running evaluation for: {eval} =======")

            try:
                self.validateApiKey(evalName=eval)
            except Exception as e:
                if hasattr(e, "response") and getattr(e, "response", None) is not None:
                    pass
                raise
            userHits = checkUserHits(
                self.workspaceID,
                self.hasSubscribed,
                self.trialEndDate,
                self.subscriptionEndDate,
                self.hitsAvailable,
                len(dataframe),
            )

            if not userHits["success"]:
                raise LlumoAIError.InsufficientCredits(userHits["message"])

            # if self.hitsAvailable == 0 or len(dataframe) > self.hitsAvailable:
            #     raise LlumoAIError.InsufficientCredits()

            evalDefinition = self.evalDefinition[eval].get("definition")
            model = "GPT_4"
            provider = "OPENAI"
            evalType = "LLM"
            workspaceID = self.workspaceID
            email = self.email

            self.allBatches = []
            currentBatch = []

            for index, row in dataframe.iterrows():
                tools = [row["tools"]] if "tools" in dataframe.columns else []
                groundTruth = (
                    row["groundTruth"] if "groundTruth" in dataframe.columns else ""
                )
                messageHistory = (
                    [row["messageHistory"]]
                    if "messageHistory" in dataframe.columns
                    else []
                )
                promptTemplate = prompt_template

                keys = re.findall(r"{{(.*?)}}", promptTemplate)

                if not all([ky in dataframe.columns for ky in keys]):
                    raise LlumoAIError.InvalidPromptTemplate()

                inputDict = {key: row[key] for key in keys if key in row}
                output = (
                    row[outputColName] if outputColName in dataframe.columns else ""
                )

                activePlayground = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace(
                    "-", ""
                )
                rowID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
                columnID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")

                # storing the generated rowID and the row index (dataframe) for later lookkup
                rowIdMapping[rowID] = index

                templateData = {
                    "processID": getProcessID(),
                    "socketID": socketID,
                    "source": "SDK",
                    "processData": {
                        "executionDependency": {
                            "query": "",
                            "context": "",
                            "output": output,
                            "tools": tools,
                            "groundTruth": groundTruth,
                            "messageHistory": messageHistory,
                        },
                        "definition": evalDefinition,
                        "model": model,
                        "provider": provider,
                        "analytics": eval,
                    },
                    "workspaceID": workspaceID,
                    "type": "EVAL",
                    "evalType": evalType,
                    "kpi": eval,
                    "columnID": columnID,
                    "rowID": rowID,
                    "playgroundID": activePlayground,
                    "processType": "EVAL",
                    "email": email,
                }

                query = ""
                context = ""
                for key, value in inputDict.items():
                    if isinstance(value, str):
                        length = len(value.split()) * 1.5
                        if length > 50:
                            context += f" {key}: {value}, "
                        else:
                            if promptTemplate:
                                tempObj = {key: value}
                                promptTemplate = getInputPopulatedPrompt(
                                    promptTemplate, tempObj
                                )
                            else:
                                query += f" {key}: {value}, "

                if not context.strip():
                    for key, value in inputDict.items():
                        context += f" {key}: {value}, "

                templateData["processData"]["executionDependency"][
                    "context"
                ] = context.strip()
                templateData["processData"]["executionDependency"][
                    "query"
                ] = query.strip()

                if promptTemplate and not query.strip():
                    templateData["processData"]["executionDependency"][
                        "query"
                    ] = promptTemplate

                currentBatch.append(templateData)

                if len(currentBatch) == 10 or index == len(dataframe) - 1:
                    self.allBatches.append(currentBatch)
                    currentBatch = []

            totalItems = sum(len(batch) for batch in self.allBatches)

            for cnt, batch in enumerate(self.allBatches):
                try:

                    self.postBatch(batch=batch, workspaceID=workspaceID)
                    print("Betch Posted with item len: ", len(batch))
                except Exception as e:
                    continue

                # time.sleep(3)

            timeout = max(50, min(600, totalItems * 10))

            self.socket.listenForResults(
                min_wait=40,
                max_wait=timeout,
                inactivity_timeout=150,
                expected_results=totalItems,
            )

            eval_results = self.socket.getReceivedData()
            results[eval] = self.finalResp(eval_results)

        except Exception as e:
            raise
        finally:
            try:
                self.socket.disconnect()
            except Exception as e:
                pass

        for evalName, records in results.items():
            dataframe[evalName] = None
            for item in records:
                for compound_key, value in item.items():
                    # for compound_key, value in item['data'].items():

                    rowID = compound_key.split("-")[0]
                    # looking for the index of each rowID , in the original dataframe
                    if rowID in rowIdMapping:
                        index = rowIdMapping[rowID]
                        # dataframe.at[index, evalName] = value
                        dataframe.at[index, evalName] = value["value"]
                        dataframe.at[index, f"{evalName} Reason"] = value["reasoning"]

                    else:
                        pass
                        # print(f"⚠️ Warning: Could not find rowID {rowID} in mapping")
        if createExperiment:
            pd.set_option("future.no_silent_downcasting", True)
            df = dataframe.fillna("Some error occured").astype(object)

            if createPlayground(
                email,
                workspaceID,
                df,
                promptText=prompt_template,
                definationMapping=self.definationMapping,
                outputColName=outputColName,
            ):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results.Please rerun the experiment to see the results on playground."
                )
        else:
            return dataframe

    # this function allows the users to run multiple evals at once

    def compressor(self, data, prompt_template):
        results = []
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        dataframe = pd.DataFrame(data)

        try:
            self.socket = LlumoSocketClient(socketUrl)
            dataframe = pd.DataFrame(data).astype(str)
            socketID = self.socket.connect(timeout=250)

            # Wait for socket connection
            max_wait_secs = 20
            waited_secs = 0
            while not self.socket._connection_established.is_set():
                time.sleep(0.1)
                waited_secs += 0.1
                if waited_secs >= max_wait_secs:
                    raise RuntimeError("Timeout waiting for server connection")

            # Start listener thread
            expectedResults = len(dataframe)
            # print("expected result" ,expectedResults)
            timeout = max(100, min(150, expectedResults * 10))
            listener_thread = threading.Thread(
                target=self.socket.listenForResults,
                kwargs={
                    "min_wait": 40,
                    "max_wait": timeout,
                    "inactivity_timeout": 10,
                    "expected_results": expectedResults,
                },
                daemon=True,
            )
            listener_thread.start()

            try:
                self.validateApiKey()
            except Exception as e:
                print(f"Error during API key validation: {str(e)}")
                if hasattr(e, "response") and getattr(e, "response", None) is not None:
                    print(f"Status code: {e.response.status_code}")
                    print(f"Response content: {e.response.text[:500]}...")
                raise

            userHits = checkUserHits(
                self.workspaceID,
                self.hasSubscribed,
                self.trialEndDate,
                self.subscriptionEndDate,
                self.hitsAvailable,
                len(dataframe),
            )

            if not userHits["success"]:
                raise LlumoAIError.InsufficientCredits(userHits["message"])

            model = "GPT_4"
            provider = "OPENAI"
            evalType = "LLUMO"
            workspaceID = self.workspaceID
            email = self.email
            self.allBatches = []
            currentBatch = []
            rowIdMapping = {}
            for index, row in dataframe.iterrows():
                promptTemplate = prompt_template
                keys = re.findall(r"{{(.*?)}}", promptTemplate)
                inputDict = {key: row[key] for key in keys if key in row}

                if not all([ky in dataframe.columns for ky in keys]):
                    raise LlumoAIError.InvalidPromptTemplate()

                activePlayground = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace(
                    "-", ""
                )
                rowID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
                columnID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")

                compressed_prompt_id = (
                    f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
                )
                compressed_prompt_output_id = (
                    f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
                )
                cost_id = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
                cost_saving_id = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace(
                    "-", ""
                )

                rowDataDict = {}
                for col in dataframe.columns:
                    val = row[col]
                    rowDataDict[col] = {"type": "VARIABLE", "value": str(val)}

                templateData = {
                    "processID": getProcessID(),
                    "socketID": socketID,
                    "source": "SDK",
                    "rowID": rowID,
                    "columnID": columnID,
                    "processType": "COST_SAVING",
                    "evalType": evalType,
                    "dependency": list(inputDict.keys()),
                    "costColumnMapping": {
                        "compressed_prompt": compressed_prompt_id,
                        "compressed_prompt_output": compressed_prompt_output_id,
                        "cost": cost_id,
                        "cost_saving": cost_saving_id,
                    },
                    "processData": {
                        "rowData": rowDataDict,
                        "dependency": list(inputDict.keys()),
                        "dependencyMapping": {ky: ky for ky in list(inputDict.keys())},
                        "provider": provider,
                        "model": model,
                        "promptText": promptTemplate,
                        "costColumnMapping": {
                            "compressed_prompt": compressed_prompt_id,
                            "compressed_prompt_output": compressed_prompt_output_id,
                            "cost": cost_id,
                            "cost_saving": cost_saving_id,
                        },
                    },
                    "workspaceID": workspaceID,
                    "email": email,
                    "playgroundID": activePlayground,
                }

                rowIdMapping[f"{rowID}-{columnID}-{columnID}"] = index
                # print("__________________________TEMPLATE__________________________________")
                # print(templateData)

                currentBatch.append(templateData)

                if len(currentBatch) == 10 or index == len(dataframe) - 1:
                    self.allBatches.append(currentBatch)
                    currentBatch = []

            total_items = sum(len(batch) for batch in self.allBatches)

            for cnt, batch in enumerate(self.allBatches):
                try:
                    self.postBatch(batch=batch, workspaceID=workspaceID)
                except Exception as e:
                    print(f"Error posting batch {cnt + 1}: {str(e)}")
                    continue
                time.sleep(1)

            self.AllProcessMapping()
            timeout = max(60, min(600, total_items * 10))
            self.socket.listenForResults(
                min_wait=20,
                max_wait=timeout,
                inactivity_timeout=50,
                expected_results=None,
            )

            rawResults = self.socket.getReceivedData()
            receivedRowIDs = {key for item in rawResults for key in item.keys()}
            expectedRowIDs = set(rowIdMapping.keys())
            missingRowIDs = expectedRowIDs - receivedRowIDs
            # print("All expected keys:", expected_rowIDs)
            # print("All received keys:", received_rowIDs)
            # print("Missing keys:", len(missingRowIDs))
            missingRowIDs = list(missingRowIDs)

            if len(missingRowIDs) > 0:
                dataFromDb = fetchData(workspaceID, activePlayground, missingRowIDs)
                rawResults.extend(dataFromDb)

            # results = self.finalResp(eval_results)
            # print(f"======= Completed evaluation: {eval} =======\n")

        except Exception as e:
            print(f"Error during evaluation: {e}")
            raise
        finally:
            try:
                self.socket.disconnect()
            except Exception as e:
                print(f"Error disconnecting socket: {e}")

        dataframe["Compressed Input"] = None
        for records in rawResults:
            for compound_key, value in records.items():
                # for compound_key, value in item['data'].items():
                rowID = compound_key
                # looking for the index of each rowID , in the original dataframe
                if rowID in rowIdMapping:
                    index = rowIdMapping[rowID]

                    dataframe.at[index, "Compressed Input"] = value["value"]

                else:
                    pass
                    # print(f"⚠️ Warning: Could not find rowID {rowID} in mapping")

        # compressed_prompt, compressed_prompt_output, cost, cost_saving = costColumnMapping(results, self.processMapping)
        # dataframe["compressed_prompt"] = compressed_prompt
        # dataframe["compressed_prompt_output"] = compressed_prompt_output
        # dataframe["cost"] = cost
        # dataframe["cost_saving"] = cost_saving

        return dataframe

    def evaluateMultiple(
        self,
        data,
        evals: list = [],
        # prompt_template="Give answer to the given query: {{query}} using the given context: {{context}}.",
        prompt_template="",
        getDataFrame: bool = False,
        _tocheck=True,
    ):
        # if hasattr(self, "startLlumoRun"):
        #     self.startLlumoRun(runName="evaluateMultiple")
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        self.socket = LlumoSocketClient(socketUrl)
        dataframe = pd.DataFrame(data).astype(str)
        workspaceID = None
        email = None
        try:
            socketID = self.socket.connect(timeout=250)
            print("Socket connected with ID:", socketID)
        except Exception as e:
            socketID = "DummySocketID"
            print(f"Socket connection failed, using dummy ID. Error: {str(e)}")

        self.evalData = []
        self.evals = evals
        self.allBatches = []
        rowIdMapping = {}  # (rowID-columnID-columnID -> (index, evalName))

        # Wait for socket connection
        # max_wait_secs = 20
        # waited_secs = 0
        # while not self.socket._connection_established.is_set():
        #     time.sleep(0.1)
        #     waited_secs += 0.1
        #     if waited_secs >= max_wait_secs:
        #         raise RuntimeError("Timeout waiting for server connection")

        # Start listener thread
        # expectedResults = len(dataframe) * len(evals)
        expectedResults = len(dataframe)
        # print("expected result" ,expectedResults)
        timeout = max(100, min(250, expectedResults * 60))
        listener_thread = threading.Thread(
            target=self.socket.listenForResults,
            kwargs={
                "min_wait": 20,
                "max_wait": timeout,
                "inactivity_timeout": timeout,
                "expected_results": expectedResults,
            },
            daemon=True,
        )
        listener_thread.start()
        # commenting validate api key as we don't need it logger does it for us. uncommented but we need different
        # api for this which don't spend time on eval defintiion fetches and just bring hits
        self.validateApiKey()
        activePlayground = self.playgroundID
        # print(f"\n======= Running evaluation for: {evalName} =======")

        # Validate API and dependencies
        # self.validateApiKey(evalName=evals[0])

        # why we need custom analytics here? there is no such usage below
        # customAnalytics = getCustomAnalytics(self.workspaceID)

        # metricDependencies = checkDependency(
        #     evalName,
        #     list(dataframe.columns),
        #     tocheck=_tocheck,
        #     customevals=customAnalytics,
        # )
        # if not metricDependencies["status"]:
        #     raise LlumoAIError.dependencyError(metricDependencies["message"])

        # evalDefinition = self.evalDefinition[evalName]["definition"]
        model = "GPT_4"
        provider = "OPENAI"
        evalType = "LLM"
        workspaceID = self.workspaceID
        email = self.email
        # categories = self.categories
        # evaluationStrictness = self.evaluationStrictness
        # grammarCheckOutput = self.grammarCheckOutput
        # insightLength = self.insightsLength
        # numJudges = self.numJudges
        # penaltyBonusInstructions = self.penaltyBonusInstructions
        # probableEdgeCases = self.probableEdgeCases
        # fieldMapping = self.fieldMapping

        userHits = checkUserHits(
            self.workspaceID,
            self.hasSubscribed,
            self.trialEndDate,
            self.subscriptionEndDate,
            self.hitsAvailable,
            len(dataframe),
        )

        #where does this remaining hit comes from?

        
        if not userHits["success"]:
            raise LlumoAIError.InsufficientCredits(userHits["message"])

        currentBatch = []
        

        for index, row in dataframe.iterrows():
            # Extract required fields
            tools = row.get("tools", "")
            groundTruth = row.get("groundTruth", "")
            messageHistory = row.get("messageHistory", "")
            intermediateSteps = row.get("intermediateSteps", "")
            output = row.get("output", "")
            
            # Initialize query and context
            query = ""
            context = ""
            
            # Process prompt template if provided
            if prompt_template:
                # Extract template variables
                keys = re.findall(r"{{(.*?)}}", prompt_template)
                
                if not all([key in dataframe.columns for key in keys]):
                    raise LlumoAIError.InvalidPromptTemplate()
                
                # Populate template and separate query/context
                populated_template = prompt_template
                for key in keys:
                    value = row.get(key, "")
                    if isinstance(value, str):
                        length = len(value.split()) * 1.5
                        if length <= 50:
                            # Short value - include in query via template
                            temp_obj = {key: value}
                            populated_template = getInputPopulatedPrompt(populated_template, temp_obj)
                        else:
                            # Long value - add to context
                            context += f" {key}: {value}, "
                
                query = populated_template.strip()
                
                # Add any remaining context from other fields
                if not context.strip():
                    for key, value in row.items():
                        if key not in keys and isinstance(value, str) and value.strip():
                            context += f" {key}: {value}, "
            else:
                # No prompt template - use direct query and context fields
                query = row.get("query", "")
                context = row.get("context", "")
            
            # Generate unique IDs
            rowID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
            columnID = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
            
            compoundKey = f"{rowID}-{columnID}-{columnID}"
            rowIdMapping[compoundKey] = {"index": index}
            print("rowIdMapping:", rowIdMapping)

            # Create evaluation payload
            print("socketID in before templateData: ", socketID)
            templateData = {
                "processID": getProcessID(),
                "socketID": socketID,
                "rowID": rowID,
                "columnID": columnID,
                "processType": "FULL_EVAL_RUN",
                "evalType": "LLM",
                "workspaceID": workspaceID,
                "email": email,
                "playgroundID": activePlayground,
                "source": "SDK",
                "processData": {
                    "executionDependency": {
                        "query": query,
                        "context": context.strip(),
                        "output": output,
                        "tools": tools,
                        "groundTruth": groundTruth,
                        "messageHistory": messageHistory,
                        "intermediateSteps": intermediateSteps,
                    },
                    "evallist": evals,
                    "sessionID": self.sessionID
                },
                "type": "FULL_EVAL_RUN",
            }

            # Add to batch
            currentBatch.append(templateData)
            if len(currentBatch) == 10:
                self.allBatches.append(currentBatch)
                currentBatch = []

        if currentBatch:
            self.allBatches.append(currentBatch)

        for batch in tqdm(
            self.allBatches,
            desc="Processing Batches",
            unit="batch",
            colour="magenta",
            ascii=False,
        ):
            try:
                self.postBatch(batch=batch, workspaceID=workspaceID)
                time.sleep(2)
                # print(batch)
            except Exception as e:
                print(f"Error posting batch: {e}")
                raise

        # Wait for results
        time.sleep(3)
        listener_thread.join()

        rawResults = self.socket.getReceivedData()

        print(f"Total results received: {len(rawResults)}")
        # print("Raw results:", rawResults)

        # print("data from db #####################",dataFromDb)
        # Fix here: keep full keys, do not split keys
        receivedRowIDs = {key for item in rawResults for key in item.keys()}
        print("Received Row IDs:", receivedRowIDs)
        expectedRowIDs = set(rowIdMapping.keys())
        missingRowIDs = expectedRowIDs - receivedRowIDs
        # print("All expected keys:", expectedRowIDs)
        # print("All received keys:", receivedRowIDs)
        # print("Missing keys:", len(missingRowIDs))
        missingRowIDs = list(missingRowIDs)

        print("Missing Row IDs:", missingRowIDs)
        print(f"Total results before fetching missing data: {len(rawResults)}")
        if len(missingRowIDs) > 0:
            print('''It's taking longer than expected to get results for some rows. You can close this now. 
                  Please wait for 15 mins while we create the flow graph for you. You can check the graph at app.llumo.ai/debugger''')
        else:
            print('''All results received successfully. You can check flowgraph in 5 mins at app.llumo.ai/debugger''')
        # if len(missingRowIDs) > 0:
        #     dataFromDb = self.fetchDataForMissingKeys(workspaceID, missingRowIDs)
        #     # print("Fetched missing data from DB:", dataFromDb)
        #     rawResults.extend(dataFromDb)
        #     print(f"Total results after fetching missing data: {len(rawResults)}")
        
        self.evalData = rawResults
        # print("RAW RESULTS: ", self.evalData)

        # Initialize dataframe columns for each eval
        for ev_name in evals:
            dataframe[ev_name] = ""
            dataframe[f"{ev_name} Reason"] = ""
            # dataframe[f"{ev_name} EdgeCase"] = None

        # Map results to dataframe rows
        for item in rawResults:
            for compound_key, value in item.items():
                if compound_key not in rowIdMapping:
                    continue
                index = rowIdMapping[compound_key]["index"]
                rowID, columnID, _ = compound_key.split("-", 2)

                # get the dataframe row at this index
                row = dataframe.iloc[index].to_dict()

                if not value:
                    continue


                # ️ Handle fullEval block
                fullEval = value.get("fullEval") if isinstance(value, dict) else None
                if fullEval:
                    if "evalMetrics" in fullEval and isinstance(fullEval["evalMetrics"], list):
                        for evalItem in fullEval["evalMetrics"]:
                            evalName = evalItem.get("evalName") or evalItem.get("kpiName")
                            score = str(evalItem.get("score")) or evalItem.get("value")
                            reasoning = evalItem.get("reasoning")
                            # edgeCase = eval_item.get("edgeCase")

                            if evalName:
                                dataframe.at[index, evalName] = score
                                dataframe.at[index, f"{evalName} Reason"] = reasoning
                                # dataframe.at[index, f"{evalName} EdgeCase"] = edgeCase

                                
                # runLog = value.get("runLog") if isinstance(value, dict) else None
                # if runLog:
                #     try:
                #         self.createRunForEvalMultiple(smartLog=runLog)
                #     except Exception as e:
                #         print(f"Error posting smartlog: {e}")
                        

                
        try:
            self.socket.disconnect()
        except Exception:
            pass

        # if hasattr(self, "endLlumoRun"):
        #     self.endEvalRun()
        #
        return dataframe

    def promptSweep(
        self,
        templates: List[str],
        data,
        model_aliases: List[AVAILABLEMODELS],
        evals=["Response Correctness"],
        toEvaluate: bool = False,
        createExperiment: bool = False,
        getDataFrame=False,
    ) -> pd.DataFrame:
        if isinstance(data, dict):
            data = [data]
        # Check if data is now a list of dictionaries
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            working_df = pd.DataFrame(data).astype(str)
        else:
            raise ValueError("Data must be a dictionary or a list of dictionaries.")
        modelStatus = validateModels(model_aliases=model_aliases)
        if modelStatus["status"] == False:
            raise LlumoAIError.providerError(modelStatus["message"])

        self.validateApiKey()
        workspaceID = self.workspaceID
        email = self.email
        executor = ModelExecutor(self.apiKey)
        prompt_template = templates[0]

        working_df = self._outputForStream(working_df, model_aliases, prompt_template)

        # Optional evaluation
        outputEvalMapping = None
        if toEvaluate:
            for evalName in evals:
                # Validate API and dependencies
                self.validateApiKey(evalName=evalName)
                metricDependencies = checkDependency(
                    evalName, list(working_df.columns), tocheck=False
                )
                if not metricDependencies["status"]:
                    raise LlumoAIError.dependencyError(metricDependencies["message"])

            working_df, outputEvalMapping = self._evaluateForStream(
                working_df, evals, model_aliases, prompt_template, generateOutput=True
            )
        if createExperiment:
            # df = working_df.fillna("Some error occured").astype(object)
            with warnings.catch_warnings():
                warnings.simplefilter(action="ignore", category=FutureWarning)
                df = working_df.fillna("Some error occurred").astype(str)
            if createPlayground(
                email,
                workspaceID,
                df,
                promptText=prompt_template,
                definationMapping=self.definationMapping,
                evalOutputMap=outputEvalMapping,
            ):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )

        else:
            if getDataFrame == True and toEvaluate == True:
                return LlumoDataFrameResults(
                    working_df,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )

            elif getDataFrame == False and toEvaluate == True:
                data = working_df.to_dict(orient="records")
                return LlumoDictResults(
                    data,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )

            elif getDataFrame == True and toEvaluate == False:
                return working_df

            elif getDataFrame == False and toEvaluate == False:
                return working_df.to_dict(orient="records")

    # this function generates an output using llm and tools and evaluate that output
    def evaluateAgents(
        self,
        data,
        model,
        agents,
        model_api_key=None,
        evals=["Final Task Alignment"],
        prompt_template="Give answer for the given query: {{query}}",
        createExperiment: bool = False,
        getDataFrame: bool = False,
    ):
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        if model.lower() not in ["openai", "google"]:
            raise ValueError("Model must be 'openai' or 'google'")

        # converting into pandas dataframe object
        dataframe = pd.DataFrame(data)

        # Run unified agent execution
        toolResponseDf = LlumoAgentExecutor.run(
            dataframe, agents, model=model, model_api_key=model_api_key
        )

        # for eval in evals:
        # Perform evaluation
        # toolResponseDf = self.evaluate(
        #     toolResponseDf.to_dict(orient = "records"),
        #     eval=eval,
        #     prompt_template=prompt_template,
        #     createExperiment=False,
        # )
        toolResponseDf = self.evaluateMultiple(
            toolResponseDf.to_dict(orient="records"),
            evals=evals,
            prompt_template=prompt_template,
            createExperiment=createExperiment,
            getDataFrame=getDataFrame,
        )

        return toolResponseDf
        # if createExperiment:
        #     pd.set_option("future.no_silent_downcasting", True)
        #     df = toolResponseDf.fillna("Some error occured")
        #     if createPlayground(self.email, self.workspaceID, df,promptText=prompt_template,definationMapping=self.definationMapping):
        #         print(
        #             "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
        #         )
        # else:
        #     return toolResponseDf

    # this function evaluate that tools output given by the user
    def evaluateAgentResponses(
        self,
        data,
        evals=["Final Task Alignment"],
        createExperiment: bool = False,
        getDataFrame=False,
        outputColName="output",
    ):
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        dataframe = pd.DataFrame(data)

        try:
            if "query" and "messageHistory" and "tools" not in dataframe.columns:
                raise ValueError(
                    "DataFrame must contain 'query', 'messageHistory','output' ,and 'tools' columns. Make sure the columns names are same as mentioned here."
                )

            toolResponseDf = dataframe.copy()
            # for eval in evals:
            #     # Perform evaluation
            #     toolResponseDf = self.evaluate(
            #         toolResponseDf.to_dict(orient = "records"), eval=eval, prompt_template="Give answer for the given query: {{query}}",outputColName=outputColName
            #     )
            toolResponseDf = self.evaluateMultiple(
                toolResponseDf.to_dict(orient="records"),
                evals=evals,
                prompt_template="Give answer for the given query: {{query}}",
                outputColName=outputColName,
                createExperiment=createExperiment,
                getDataFrame=getDataFrame,
            )
            if createExperiment:
                pass
            else:
                return toolResponseDf

        except Exception as e:
            raise e

    def ragSweep(
        self,
        data,
        streamName: str,
        queryColName: str = "query",
        createExperiment: bool = False,
        modelAliases=[],
        prompt_template="Give answer to the given: {{query}} using the context:{{context}}",
        evals=["Context Utilization"],
        toEvaluate=False,
        generateOutput=True,
        getDataFrame=False,
    ):
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        # Validate required parameters
        if generateOutput:
            if not modelAliases:
                raise ValueError(
                    "Model aliases must be provided when generateOutput is True."
                )
            if (
                not self.apiKey
                or not isinstance(self.apiKey, str)
                or self.apiKey.strip() == ""
            ):
                raise ValueError(
                    "Valid API key must be provided when generateOutput is True."
                )

        modelStatus = validateModels(model_aliases=modelAliases)
        if modelStatus["status"] == False:
            if len(modelAliases) == 0:
                raise LlumoAIError.providerError("No model selected.")
            else:
                raise LlumoAIError.providerError(modelStatus["message"])

        # Copy the original dataframe
        original_df = pd.DataFrame(data)
        working_df = original_df.copy()

        # Connect to socket
        self.socket = LlumoSocketClient(socketUrl)
        try:
            socketID = self.socket.connect(timeout=150)
        except Exception as e:
            socketID = "DummySocketID"
        # waited_secs = 0
        # while not self.socket._connection_established.is_set():
        #     time.sleep(0.1)
        #     waited_secs += 0.1
        #     if waited_secs >= 20:
        #         raise RuntimeError("Timeout waiting for server 'connection-established' event.")

        self.validateApiKey()

        # Check user credits
        userHits = checkUserHits(
            self.workspaceID,
            self.hasSubscribed,
            self.trialEndDate,
            self.subscriptionEndDate,
            self.hitsAvailable,
            len(working_df),
        )
        if not userHits["success"]:
            raise LlumoAIError.InsufficientCredits(userHits["message"])

        print("====🚀Sit back while we fetch data from the stream 🚀====")
        workspaceID, email = self.workspaceID, self.email
        activePlayground = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
        streamId = getStreamId(workspaceID, self.apiKey, streamName)

        # Prepare batches
        rowIdMapping = {}
        self.allBatches = []
        currentBatch = []

        expectedResults = len(working_df)
        timeout = max(100, min(150, expectedResults * 10))

        listener_thread = threading.Thread(
            target=self.socket.listenForResults,
            kwargs={
                "min_wait": 40,
                "max_wait": timeout,
                "inactivity_timeout": 10,
                "expected_results": expectedResults,
            },
            daemon=True,
        )
        listener_thread.start()

        for index, row in working_df.iterrows():
            rowID, columnID = uuid.uuid4().hex, uuid.uuid4().hex
            compoundKey = f"{rowID}-{columnID}-{columnID}"
            rowIdMapping[compoundKey] = {"index": index}
            templateData = {
                "processID": getProcessID(),
                "socketID": socketID,
                "processData": {
                    "executionDependency": {"query": row[queryColName]},
                    "dataStreamID": streamId,
                },
                "workspaceID": workspaceID,
                "email": email,
                "type": "DATA_STREAM",
                "playgroundID": activePlayground,
                "processType": "DATA_STREAM",
                "rowID": rowID,
                "columnID": columnID,
                "source": "SDK",
            }
            currentBatch.append(templateData)
            if len(currentBatch) == 10 or index == len(working_df) - 1:
                self.allBatches.append(currentBatch)
                currentBatch = []

        for batch in tqdm(
            self.allBatches,
            desc="Processing Batches",
            unit="batch",
            colour="magenta",
            ncols=80,
        ):
            try:
                self.postDataStream(batch=batch, workspaceID=workspaceID)
                time.sleep(3)
            except Exception as e:
                print(f"Error posting batch: {e}")
                raise

        time.sleep(3)
        listener_thread.join()

        rawResults = self.socket.getReceivedData()
        expectedRowIDs = set(rowIdMapping.keys())
        receivedRowIDs = {key for item in rawResults for key in item.keys()}
        missingRowIDs = list(expectedRowIDs - receivedRowIDs)

        if missingRowIDs:
            dataFromDb = fetchData(workspaceID, activePlayground, missingRowIDs)
            rawResults.extend(dataFromDb)

        working_df["context"] = None
        for item in rawResults:
            for compound_key, value in item.items():
                if compound_key in rowIdMapping:
                    idx = rowIdMapping[compound_key]["index"]
                    working_df.at[idx, "context"] = value.get("value")

        # Output generation
        if generateOutput == True:
            working_df = self._outputForStream(
                working_df, modelAliases, prompt_template
            )

        # Optional evaluation
        outputEvalMapping = None
        if toEvaluate:
            for evalName in evals:
                # Validate API and dependencies
                self.validateApiKey(evalName=evalName)
                metricDependencies = checkDependency(
                    evalName, list(working_df.columns), tocheck=False
                )
                if not metricDependencies["status"]:
                    raise LlumoAIError.dependencyError(metricDependencies["message"])

            working_df, outputEvalMapping = self._evaluateForStream(
                working_df, evals, modelAliases, prompt_template, generateOutput
            )

        self.socket.disconnect()
        # Create experiment if required
        if createExperiment:
            # df = working_df.fillna("Some error occured").astype(object)
            with warnings.catch_warnings():
                warnings.simplefilter(action="ignore", category=FutureWarning)
                df = working_df.fillna("Some error occurred").astype(str)
            if createPlayground(
                email,
                workspaceID,
                df,
                queryColName=queryColName,
                dataStreamName=streamId,
                promptText=prompt_template,
                definationMapping=self.definationMapping,
                evalOutputMap=outputEvalMapping,
            ):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )
                if getDataFrame == True and toEvaluate == True:
                    return LlumoDataFrameResults(
                        working_df,
                        evals=self.evals,
                        evalData=self.evalData,
                        definationMapping=self.definationMapping,
                    )

                elif getDataFrame == False and toEvaluate == True:
                    data = working_df.to_dict(orient="records")
                    return LlumoDictResults(
                        data,
                        evals=self.evals,
                        evalData=self.evalData,
                        definationMapping=self.definationMapping,
                    )

                elif getDataFrame == True and toEvaluate == False:
                    return working_df

                elif getDataFrame == False and toEvaluate == False:
                    return working_df.to_dict(orient="records")
        else:
            if getDataFrame == True and toEvaluate == True:
                return LlumoDataFrameResults(
                    working_df,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )

            elif getDataFrame == False and toEvaluate == True:
                data = working_df.to_dict(orient="records")
                return LlumoDictResults(
                    data,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )

            elif getDataFrame == True and toEvaluate == False:
                return working_df

            elif getDataFrame == False and toEvaluate == False:
                return working_df.to_dict(orient="records")

    def _outputForStream(self, df, modelAliases, prompt_template):
        executor = ModelExecutor(self.apiKey)

        for indx, row in df.iterrows():
            inputVariables = re.findall(r"{{(.*?)}}", prompt_template)
            if not all([k in df.columns for k in inputVariables]):
                raise LlumoAIError.InvalidPromptTemplate()

            inputDict = {key: row[key] for key in inputVariables}
            for i, model in enumerate(modelAliases, 1):
                try:

                    provider = getProviderFromModel(model)
                    if provider == Provider.OPENAI:
                        validateOpenaiKey(self.apiKey)
                    elif provider == Provider.GOOGLE:
                        validateGoogleKey(self.apiKey)

                    filled_template = getInputPopulatedPrompt(
                        prompt_template, inputDict
                    )
                    response = executor.execute(provider, model.value, filled_template)
                    df.at[indx, f"output_{i}"] = response

                except Exception as e:
                    # df.at[indx, f"output_{i}"] = str(e)
                    raise e

        return df

    def _evaluateForStream(
        self, df, evals, modelAliases, prompt_template, generateOutput
    ):
        dfWithEvals = df.copy()
        outputColMapping = {}

        if generateOutput:
            # Evaluate per model output
            for i, model in enumerate(modelAliases, 1):
                outputColName = f"output_{i}"
                try:
                    res = self.evaluateMultiple(
                        dfWithEvals.to_dict("records"),
                        evals=evals,
                        prompt_template=prompt_template,
                        outputColName=outputColName,
                        _tocheck=False,
                        getDataFrame=True,
                        createExperiment=False,
                    )

                    for evalMetric in evals:
                        scoreCol = f"{evalMetric}"
                        reasonCol = f"{evalMetric} Reason"
                        if scoreCol in res.columns:
                            res = res.rename(columns={scoreCol: f"{scoreCol}_{i}"})
                        if reasonCol in res.columns:
                            res = res.rename(
                                columns={reasonCol: f"{evalMetric}_{i} Reason"}
                            )

                        outputColMapping[f"{scoreCol}_{i}"] = outputColName

                    newCols = [
                        col for col in res.columns if col not in dfWithEvals.columns
                    ]
                    dfWithEvals = pd.concat([dfWithEvals, res[newCols]], axis=1)

                except Exception as e:
                    print(f"Evaluation failed for model {model.value}: {str(e)}")

        else:
            # Evaluate only once on "output" column
            try:
                outputColName = "output"
                res = self.evaluateMultiple(
                    dfWithEvals.to_dict("records"),
                    evals=evals,
                    prompt_template=prompt_template,
                    outputColName=outputColName,
                    _tocheck=False,
                    getDataFrame=True,
                    createExperiment=False,
                )
                for evalMetric in evals:
                    scoreCol = f"{evalMetric}"
                    reasonCol = f"{evalMetric} Reason"
                    outputColMapping[scoreCol] = "output"

                newCols = [col for col in res.columns if col not in dfWithEvals.columns]
                dfWithEvals = pd.concat([dfWithEvals, res[newCols]], axis=1)
            except Exception as e:
                print(f"Evaluation failed: {str(e)}")

        return dfWithEvals, outputColMapping

    def runDataStream(
        self,
        data,
        streamName: str,
        queryColName: str = "query",
        createExperiment: bool = False,
        getDataFrame=False,
    ):

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")

        # Copy the original dataframe
        original_df = pd.DataFrame(data)
        working_df = original_df.copy()

        # Connect to socket
        self.socket = LlumoSocketClient(socketUrl)
        try:
            socketID = self.socket.connect(timeout=150)
        except Exception as e:
            socketID = "DummySocketID"
        # waited_secs = 0
        # while not self.socket._connection_established.is_set():
        #     time.sleep(0.1)
        #     waited_secs += 0.1
        #     if waited_secs >= 20:
        #         raise RuntimeError("Timeout waiting for server 'connection-established' event.")

        self.validateApiKey()

        # Check user credits
        userHits = checkUserHits(
            self.workspaceID,
            self.hasSubscribed,
            self.trialEndDate,
            self.subscriptionEndDate,
            self.hitsAvailable,
            len(working_df),
        )
        if not userHits["success"]:
            raise LlumoAIError.InsufficientCredits(userHits["message"])

        print("====🚀Sit back while we fetch data from the stream 🚀====")
        workspaceID, email = self.workspaceID, self.email
        activePlayground = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace("-", "")
        streamId = getStreamId(workspaceID, self.apiKey, streamName)

        # Prepare batches
        rowIdMapping = {}
        self.allBatches = []
        currentBatch = []

        expectedResults = len(working_df)
        timeout = max(100, min(150, expectedResults * 10))

        listener_thread = threading.Thread(
            target=self.socket.listenForResults,
            kwargs={
                "min_wait": 40,
                "max_wait": timeout,
                "inactivity_timeout": 10,
                "expected_results": expectedResults,
            },
            daemon=True,
        )
        listener_thread.start()

        for index, row in working_df.iterrows():
            rowID, columnID = uuid.uuid4().hex, uuid.uuid4().hex
            compoundKey = f"{rowID}-{columnID}-{columnID}"
            rowIdMapping[compoundKey] = {"index": index}
            templateData = {
                "processID": getProcessID(),
                "socketID": socketID,
                "processData": {
                    "executionDependency": {"query": row[queryColName]},
                    "dataStreamID": streamId,
                },
                "workspaceID": workspaceID,
                "email": email,
                "type": "DATA_STREAM",
                "playgroundID": activePlayground,
                "processType": "DATA_STREAM",
                "rowID": rowID,
                "columnID": columnID,
                "source": "SDK",
            }
            currentBatch.append(templateData)
            if len(currentBatch) == 10 or index == len(working_df) - 1:
                self.allBatches.append(currentBatch)
                currentBatch = []

        for batch in tqdm(
            self.allBatches,
            desc="Processing Batches",
            unit="batch",
            colour="magenta",
            ncols=80,
        ):
            try:
                self.postDataStream(batch=batch, workspaceID=workspaceID)
                time.sleep(3)
            except Exception as e:
                print(f"Error posting batch: {e}")
                raise

        time.sleep(3)
        listener_thread.join()

        rawResults = self.socket.getReceivedData()
        expectedRowIDs = set(rowIdMapping.keys())
        receivedRowIDs = {key for item in rawResults for key in item.keys()}
        missingRowIDs = list(expectedRowIDs - receivedRowIDs)

        if missingRowIDs:
            dataFromDb = fetchData(workspaceID, activePlayground, missingRowIDs)
            rawResults.extend(dataFromDb)

        working_df["context"] = None
        for item in rawResults:
            for compound_key, value in item.items():
                if compound_key in rowIdMapping:
                    idx = rowIdMapping[compound_key]["index"]
                    working_df.at[idx, "context"] = value.get("value")

        self.socket.disconnect()

        # Create experiment if required
        if createExperiment:
            df = working_df.fillna("Some error occured").astype(object)
            if createPlayground(
                email,
                workspaceID,
                df,
                queryColName=queryColName,
                dataStreamName=streamId,
                definationMapping=self.definationMapping,
            ):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )
                if getDataFrame:
                    return working_df

                else:
                    data = working_df.to_dict(orient="records")
                    return data
        else:
            if getDataFrame:
                return working_df

            else:
                data = working_df.to_dict(orient="records")
                return data
            # self.latestDataframe = working_df
            # return working_df

    def createExperiment(self, dataframe):
        try:
            self.validateApiKey()

            flag = createPlayground(self.email, self.workspaceID, dataframe)
            if flag:
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )
        except Exception as e:
            raise "Some error ocuured please check your API key"

    def uploadfile(self, file_path):

        workspaceID = None
        email = None

        try:
            self.validateApiKey()
        except Exception as e:
            if hasattr(e, "response") and getattr(e, "response", None) is not None:
                pass
            raise

        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Supported formats
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            elif ext == ".json":
                df = pd.read_json(file_path, orient="records")
            elif ext == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")

            # If successfully loaded, call createPlayground
            df = df.astype(str)
            if createPlayground(self.email, self.workspaceID, df):

                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )

                return True

        except Exception as e:
            print(f"Error: {e}")

    def upload(self, data):
        try:
            if isinstance(data, dict):
                data = [data]
            # Check if data is now a list of dictionaries
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                dataframe = pd.DataFrame(data).astype(str)
            else:
                raise ValueError("Data must be a dictionary or a list of dictionaries.")
            self.validateApiKey()
            if createPlayground(self.email, self.workspaceID, dataframe):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )
                return True

        except Exception as e:
            print(f"Error: {e}")
            return False

    def createExperimentWithEvals(
        self,
        data,
        evals: list,  # list of eval metric names
        prompt_template="Give answer to the given query: {{query}} using the given context: {{context}}.",
        outputColName="output",
        createExperiment: bool = False,
        getDataFrame: bool = False,
        _tocheck=True,
    ):
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Data should be a dict or a list of dicts.")
        dataframe = pd.DataFrame(data).astype(str)
        workspaceID = None
        email = None
        self.evalData = []
        self.evals = evals
        self.allBatches = []
        rowIdMapping = {}  # (rowID-columnID-columnID -> (index, evalName))
        self.validateApiKey(evalName=evals[0])
        if createExperiment:
            if self.playgroundID:
                activePlayground = self.playgroundID
            else:
                activePlayground = str(
                    createEvalPlayground(email=self.email, workspaceID=self.workspaceID)
                )
        else:
            activePlayground = f"{int(time.time() * 1000)}{uuid.uuid4()}".replace(
                "-", ""
            )
        for evalName in evals:
            self.validateApiKey(evalName=evalName)
        self.evalData = dataframe.to_dict(orient="records")
        if createExperiment:
            print("heading to upload")
            pd.set_option("future.no_silent_downcasting", True)
            # df = dataframe.fillna("Some error occured").astype(object)
            with warnings.catch_warnings():
                warnings.simplefilter(action="ignore", category=FutureWarning)
                df = dataframe.fillna("Some error occurred").astype(str)

            df = dataframe.fillna("Some error occured").infer_objects(copy=False)
            if createPlayground(
                self.email,
                self.workspaceID,
                df,
                promptText=prompt_template,
                definationMapping=self.definationMapping,
                outputColName=outputColName,
                activePlayground=activePlayground,
            ):
                print(
                    "LLUMO’s intuitive UI is ready—start exploring and experimenting with your logs now. Visit https://app.llumo.ai/evallm to see the results."
                )

        else:
            if getDataFrame:
                return LlumoDataFrameResults(
                    dataframe,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )
            else:
                data = dataframe.to_dict(orient="records")
                return LlumoDictResults(
                    data,
                    evals=self.evals,
                    evalData=self.evalData,
                    definationMapping=self.definationMapping,
                )


class SafeDict(dict):
    def __missing__(self, key):
        return ""
