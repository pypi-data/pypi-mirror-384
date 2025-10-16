from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .generate.func_call_generators import (
        ScenarioExtractGenerator,
        ScenarioExpandGenerator,
        AtomTaskGenerator,
        SequentialTaskGenerator,
        ParaSeqTaskGenerator,
        FunctionGenerator,
        MultiTurnConversationGenerator,
    )
    from .generate.consistent_chat_generator import ConsistentChatGenerator
    
    from .eval.func_call_conversation_sample_evaluator import FuncCallConversationSampleEvaluator
    
    from .filter.composition_task_filter import CompositionTaskFilter

else:
    import sys
    from dataflow.utils.registry import LazyLoader, generate_import_structure_from_type_checking

    cur_path = "dataflow/operators/conversations/"

    # _import_structure = {
    #     "ScenarioExtractor": (cur_path + "func_call_operators.py", "ScenarioExtractor"),
    #     "ScenarioExpander": (cur_path + "func_call_operators.py", "ScenarioExpander"),
    #     "AtomTaskGenerator": (cur_path + "func_call_operators.py", "AtomTaskGenerator"),
    #     "SequentialTaskGenerator": (cur_path + "func_call_operators.py", "SequentialTaskGenerator"),
    #     "ParaSeqTaskGenerator": (cur_path + "func_call_operators.py", "ParaSeqTaskGenerator"),
    #     "CompositionTaskFilter": (cur_path + "func_call_operators.py", "CompositionTaskFilter"),
    #     "FunctionGenerator": (cur_path + "func_call_operators.py", "FunctionGenerator"),
    #     "MultiTurnDialogueGenerator": (cur_path + "func_call_operators.py", "MultiTurnDialogueGenerator"),
    #     "ConsistentChatGenerator": (cur_path + "consistent_chat.py", "ConsistentChatGenerator")
    # }
    _import_structure = generate_import_structure_from_type_checking(__file__, cur_path)
    sys.modules[__name__] = LazyLoader(__name__, "dataflow/operators/conversations/", _import_structure)