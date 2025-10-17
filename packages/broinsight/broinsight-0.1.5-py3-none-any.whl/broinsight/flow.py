from broflow import Flow, Start, End
from .actions.retrieve import Retrieve
from .actions.chat import Chat
from .actions.generate_sql import GenerateSQL
from .actions.select_metadata import SelectMetadata
from .actions.organize import Organize
from .actions.guide_question import GuideQuestion 
from brollm import BaseLLM
from broprompt import Prompt

def get_flow(model:BaseLLM):
    start_action = Start(message="Welcome to BroInsight!")
    end_action = End(message="Thank you for using BroInsight!")
    
    organize_action = Organize(
        system_prompt=Prompt.from_markdown("broinsight/prompt_hub/organize.md").str,
        model=model
    )
    guide_question_action = GuideQuestion(
        system_prompt=Prompt.from_markdown("broinsight/prompt_hub/guide_question.md").str,
        model=model
    )
    select_metadata_action = SelectMetadata(
        system_prompt=Prompt.from_markdown("broinsight/prompt_hub/select_metadata.md").str,
        model=model
    )
    generate_sql_action = GenerateSQL(
        system_prompt=Prompt.from_markdown("broinsight/prompt_hub/generate_sql.md").str,
        model=model
    )
    retrieve_action = Retrieve()
    chat_action = Chat(
        system_prompt=Prompt.from_markdown("broinsight/prompt_hub/chat.md").str,
        model=model
    )
    
    # One-shot workflow paths:
    # Path 1: organize -> select_metadata -> generate_sql -> retrieve -> chat -> end
    # Path 2: organize -> chat -> end  
    # Path 3: organize -> guide_question -> end
    
    start_action >> organize_action
    organize_action -"guide">> guide_question_action
    guide_question_action >> end_action
    organize_action -"select_metadata">> select_metadata_action
    select_metadata_action >> generate_sql_action
    generate_sql_action >> retrieve_action
    retrieve_action -"generate_sql">> generate_sql_action
    retrieve_action >> chat_action
    organize_action >> chat_action
    chat_action >> end_action
    
    return Flow(start_action=start_action, name="BroInsight One-Shot!")