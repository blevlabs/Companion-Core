import uuid
import traceback
import openai
import requests
import weaviate
import sys
sys.path.append("/home/blabs/Companion-Core/dynamic-system/core/resources/")
from database_manager import DatabaseManager

database_manager = DatabaseManager()


class ASA:
    def __init__(self, weaviate_server="http://192.168.1.110:8080", modeltype="codex"):
        """
        asa_type: dict
        asa_type FORMAT: {"asa_class_type": "generation|analysis|breakdown","context":"OPTIONAL","code":"OPTIONAL",file:"OPTIONAL",repair_mode:"OPTIONAL"}
        """
        self.weaviate_client = weaviate.Client(weaviate_server)
        self.modeltype = modeltype
        self.codet5_server = "http://192.168.1.110:5090/codet5"

    def init_params(self, **kwargs):
        self.base_call = {"file": None, "context": None, "code": None, "repair_mode": None, "asa_class_type": None}
        # update base call with kwargs
        self.base_call.update(self.asa_type)
        self.file = self.base_call["file"]
        self.context = self.base_call["context"]
        self.code = self.base_call["code"]
        self.repair_mode = self.base_call["repair_mode"]
        self.asa_class_type = self.base_call["asa_class_type"]
        return self.base_call

    def call_asa(self, asa_type):
        self.asa_type = asa_type
        self.init_params()
        self.response = getattr(self, self.asa_type["asa_class_type"])(**asa_type)
        if "file" in self.asa_type and "repair_mode" in self.asa_type:
            print("Repairing file", self.asa_type["file"], "with repair mode", self.asa_type["repair_mode"])
            self.file = self.asa_type["file"]
            self.file_writer(self.file, self.asa_type["code"], self.response)

    def call_codet5(self, code):
        return requests.post(self.codet5_server, json={"code": code}).json()["codet5-response"][0][
            "generated_text"].replace("\n\n", "\n").strip("\n")

    def merge(self, orginal_code, completion):
        strA = orginal_code
        strB = completion
        print("Merging Code...")
        # print(strA, strB)
        merge_code = strA[:strA.index(strB[0])] + strB
        return merge_code

    def weaviate_writer(self, prompt, context, label, output, **kwargs):
        if type(context) != type([]):
            context = [context]
        self.weaviate_client.data_object.create(
            data_object={"prompt": prompt, "context": context, "label": label, "output": output}, class_name="ASA",
            uuid=str(uuid.uuid4()))

    def file_writer(self, file, original_code, new_code, **kwargs):
        with open(file, "r") as f:
            filedata = f.read()
            filedata = filedata.replace(original_code, new_code)
            f.close()
        with open(file, "w") as f:
            f.write(filedata)
            f.close()

    def breakdown(self, context, **kwargs):
        prompt = database_manager.promptSchemaRetrieval("asa-breakdown")["schema"].format(context=context)
        response = openai.Completion.create(
            model="code-davinci-002",
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["###"]
        )
        database_manager.class_data_uploader("breakdown", response["choices"][0]["text"])
        self.weaviate_writer(prompt="Breakdown the traceback errors into a proper format", context=context,
                             label="error_breakdown",
                             output=response["choices"][0]["text"].strip("\n"))
        response = response["choices"][0]["text"].strip("\n").split("\n")
        response = {"file": response[0].replace("File: ", ""), "ErrorType": response[1].replace("ErrorType: ", ""),
                    "line": response[2].replace("Line: ", ""),
                    "code": response[3].replace("Errored Code: ", ""),
                    "Errored Code Line": response[4].replace("Errored Code Line: ", ""),
                    "function": response[5].replace("Function: ", ""), "error": response[6].replace("Error: ", ""),
                    "repair_mode": True}
        if self.file is None:
            self.file = response["file"]
        return response

    def call_codex(self, context, code, **kwargs):
        input_data = "Error Context: " + context + "\nErrored Code:\n" + code
        prompt = database_manager.promptSchemaRetrieval("callCodex")["schema"] + input_data + "\n===\nFixed Code:\n",
        response = openai.Completion.create(
            model="code-davinci-002",
            prompt=prompt,
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        code = response["choices"][0]["text"]
        code = code.strip("\n")
        self.weaviate_writer(
            prompt="Fix the bugs in the code based on the error context provided.",
            context="Error Context:" + context + "\nErrored Code:\n" + code, label="optimization", output=code)
        return code

    def extract_context_window(self, error_line, **kwargs):
        file_data = open(self.file, "r").read()
        error_line = int(error_line)
        # replace literal newlines with a placeholder
        # extract code window with edgecases (check if it is the first or last line)
        context_window_data = file_data.split("\n")
        context_window = "\n".join(context_window_data[max(0, error_line - 5):min(len(context_window_data), error_line + 5)])
        return context_window

    def analysis(self, code, **kwargs):
        assert code != "", "Code must be provided"
        input_data = "Code:\n" + code + "\n===\n" + "Analysis:"
        prompt = database_manager.promptSchemaRetrieval("analysis")["schema"] + input_data
        response = openai.Completion.create(
            model="text-davinci-003",
            temperature=0.7,
            prompt=prompt,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        analysis = response["choices"][0]["text"]
        analysis = analysis.strip("\n")
        self.weaviate_writer(
            prompt="Analyze the code and generate an explanation of the code provided to be used in a docstring.",
            context="Code:\n" + code + "\n===\n" + "Analysis:", label="analysis", output=analysis)
        return analysis

    def generation(self, context="", code="", **kwargs):
        assert context != "" or code != "", "Context and Script must be provided"
        if context == "":
            general_context = f"{code}"
        elif code == "":
            general_context = f"# {context}"
        else:
            general_context = f"# {context}\n{code}"
        input_data = "Code: " + general_context + "\n===\n" + "Completion:"
        prompt = database_manager.promptSchemaRetrieval("generation")["schema"] + input_data
        response = openai.Completion.create(
            model="code-davinci-002",
            temperature=0.7,
            prompt=prompt,
            max_tokens=600,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["==="]
        )
        gen_code = response["choices"][0]["text"]
        gen_code = gen_code.strip("\n").strip()
        self.weaviate_writer(prompt=input_data, label="Generation", output=gen_code, context=[context, code])
        if code != "":
            gen_code = self.merge(code, gen_code)
        return gen_code

    def repair(self, file, **kwargs):
        # run file, get tracebacks, send to error breakdown, send to generation, rewrite file
        self.file = file
        # The below loop will continue to run and repair the file until it is error free
        errorCheck = True
        while errorCheck is True:
            try:
                exec(open(file).read())
                errorCheck = False
            except Exception as e:
                errorCheck = True
                # get tracebacks
                tracebacks = traceback.format_exc()
                # send to error breakdown
                breakdown = self.breakdown(tracebacks)
                breakdown["code"] = self.extract_context_window(breakdown["line"])
                print(self.extract_context_window(breakdown["line"]))
                # send to generation
                gen_code = self.generation(context=breakdown["Errored Code Line"], code=breakdown["code"])
                # rewrite file
                self.file_writer(file, breakdown["code"], gen_code)
        return "File repaired"