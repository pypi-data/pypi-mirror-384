import pandas as pd
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow import get_logger

from dataflow.utils.storage import DataFlowStorage
from dataflow.core import OperatorABC
from dataflow.core import LLMServingABC
from dataflow.core.prompt import prompt_restrict
import ast
import json

from dataflow.prompts.text2qa import Text2QASeedQuestionGeneratorPrompt,Text2QAAutoPromptGeneratorPrompt

@prompt_restrict(
    Text2QAAutoPromptGeneratorPrompt,
    Text2QASeedQuestionGeneratorPrompt
)
@OPERATOR_REGISTRY.register()
class Text2QAGenerator:
    '''
    SeedQAGenerator is a class that uses LLMs to generate QA pairs based on seed input.
    '''

    def __init__(self,
                 llm_serving: LLMServingABC,
                #  prompt_template = None # prompt is fix
                 ):
        self.logger = get_logger()
        self.llm_serving = llm_serving
        self.prompt_template = Text2QAAutoPromptGeneratorPrompt()
    
    @staticmethod
    def get_desc(lang: str = "zh"):
        if lang == "zh":
            return (
                "该算子用于为给定的文档片段生成种子QA对。\n\n"
                "输入参数：\n"
                "- input_key: 包含文档片段的字段名\n"
                "- prompt_key: 包含提示词的字段名\n"
                "- output_quesion_key: 包含生成问题的字段名\n"
                "- output_answer_key: 包含生成答案的字段名\n"
            )
        elif lang == "en":
            return (
                "This operator generates seed QA pairs for given document fragments.\n\n"
                "Input Parameters:\n"
                "- input_key: Field name containing the content\n"
                "- prompt_key: Field name containing the generated prompt\n"
                "- output_quesion_key: Field name containing the generated question\n"
                "- output_answer_key: Field name containing the generated answer\n"
            )
        else:
            return "QAGenerator generates QA pairs for given document fragments."

    def _validate_dataframe(self, dataframe: pd.DataFrame):
        required_keys = [self.input_key]
        forbidden_keys = [self.output_question_key, self.output_answer_key]

        missing = [k for k in required_keys if k not in dataframe.columns]
        conflict = [k for k in forbidden_keys if k in dataframe.columns]

        if missing:
            raise ValueError(f"Missing required column(s): {missing}")
        if conflict:
            raise ValueError(f"The following column(s) already exist and would be overwritten: {conflict}")

    def _build_prompt(self, df, types):
        if types == "prompt":
            self.prompt_template = Text2QAAutoPromptGeneratorPrompt()
            texts = df[self.input_key].tolist()
            output = [self.prompt_template.build_prompt(text) for text in texts]
        elif types == "qa":
            self.prompt_template = Text2QASeedQuestionGeneratorPrompt()
            output = []
            for index, row in df.iterrows():
                output.append(row[self.output_prompt_key] + self.prompt_template.build_prompt() + row[self.input_key])
        return output

    def _parse_qa(self, response: str) -> tuple:
        lines = response.strip().split('\n')
        q = next((line[2:].strip() for line in lines if line.lower().startswith("q:")), "")
        a = next((line[2:].strip() for line in lines if line.lower().startswith("a:")), "")
        return q, a

    def parse_list_string(self, s: str) -> list:
        # 去掉前后的 [ ]
        s = s.strip()[1:-1]
        # 去掉多余逗号并按 , 切分
        items = [item.strip() for item in s.split(",") if item.strip()]
        return items

    def run(
        self, 
        storage: DataFlowStorage, 
        input_key:str = "text", 
        input_question_num:int = 1,
        output_prompt_key:str = "generated_prompt",
        output_quesion_key:str = "generated_question",
        output_answer_key:str = "generated_answer"
        ):
        '''
        Runs the QA generation process, reading from the input file and saving results to output.
        '''

        self.input_key, self.input_question_num, self.output_prompt_key, self.output_question_key, self.output_answer_key = input_key, input_question_num, output_prompt_key, output_quesion_key, output_answer_key

        dataframe = storage.read("dataframe")
        self._validate_dataframe(dataframe)
        formatted_prompts = self._build_prompt(dataframe, "prompt")
        prompts = self.llm_serving.generate_from_input(user_inputs=formatted_prompts, system_prompt="")
        prompts = [json.loads(p) for p in prompts]

        expanded_rows = []
        expanded_prompts = []

        for idx, prompt_list in enumerate(prompts):
            for p in prompt_list[:min(self.input_question_num,len(prompt_list))]:
                expanded_rows.append(dataframe.iloc[idx].to_dict())  # 复制该行
                expanded_prompts.append(p)  # 对应的 prompt

        dataframe = pd.DataFrame(expanded_rows)
        dataframe[self.output_prompt_key] = expanded_prompts

        formatted_prompts = self._build_prompt(dataframe, "qa")
        responses = self.llm_serving.generate_from_input(user_inputs=formatted_prompts, system_prompt="")

        questions, answers = zip(*[self._parse_qa(r) for r in responses])

        dataframe[self.output_question_key] = questions
        dataframe[self.output_answer_key] = answers

        output_file = storage.write(dataframe)
        self.logger.info(f"Results saved to {output_file}")


        return [self.output_question_key, self.output_answer_key]
