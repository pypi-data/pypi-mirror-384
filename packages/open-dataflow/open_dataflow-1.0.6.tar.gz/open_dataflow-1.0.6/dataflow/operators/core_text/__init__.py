from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .generate.prompted_generator import PromptedGenerator
    from .generate.paired_prompted_generator import PairedPromptedGenerator
    from .generate.random_domain_knowledge_row_generator import RandomDomainKnowledgeRowGenerator   
    from .generate.text2qa_generator import Text2QAGenerator
    from .generate.text2multihopqa_generator import Text2MultiHopQAGenerator
    from .generate.embedding_generator import EmbeddingGenerator
    from .eval.bench_dataset_evaluator import BenchDatasetEvaluator
    from .eval.text2qa_sample_evaluator import Text2QASampleEvaluator
    from .eval.prompted_eval import PromptedEvaluator
    from .filter.prompted_filter import PromptedFilter
    from .filter.kcentergreedy_filter import KCenterGreedyFilter    
    from .filter.general_filter import GeneralFilter
    from .refine.prompted_refiner import PromptedRefiner
    from .refine.pandas_operator import PandasOperator
else:
    import sys
    from dataflow.utils.registry import LazyLoader, generate_import_structure_from_type_checking

    cur_path = "dataflow/operators/core_text/"

    _import_structure = generate_import_structure_from_type_checking(__file__, cur_path)
    sys.modules[__name__] = LazyLoader(__name__, "dataflow/operators/core_text/", _import_structure)
