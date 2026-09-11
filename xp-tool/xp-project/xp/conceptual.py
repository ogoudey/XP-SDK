import click
from . import auth
from . import questionary_helpers as q
from typing import Optional
from concepts.experience import SharedExperience
from concepts.experience import ExperienceStructure
from concepts.ego import HumanEgo
from concepts.experience_dna import ExperienceDNA
from concepts.experience_format import ExperienceFormat



from concepts.experience import Experiencer, HumanBrain
def generate_user_experiencer() -> Optional[Experiencer]:
    
    #  - maybe this is an experiencer
    logged_in = False
    user_experiencer_name = None
    if q.answer_yes_or_no("Are you an experiencer?"):
        token_data = auth.load_token()
        if not token_data:
            click.echo(f"Not logged in.")
            user_experiencer_name = q.ask_for_str(f"This experience will not be uploaded...\nWhat is your name?")
        else:
            click.echo(f"Logged in to XP as {token_data['user']['username']}...")
            if q.answer_yes_or_no(f"Are you {token_data['user']['username']}?"):
                logged_in = True
                user_experiencer_name = token_data['user']['username']
            else:
                user_experiencer_name = q.ask_for_str(f"This experience will not be uploaded...\nWhat is your name?")
        return Experiencer(
            ego=HumanEgo(
                name=user_experiencer_name,
                codebase="human_nature",
                experience_dna=ExperienceDNA(
                    value="human"
                )
            )
        )
        
    return None
from concepts.capability_model import RootIntegratedOutput, RootIntegratedInput
from .capability_model import ActionMapping, Input, Action

def generate_user_experience() -> SharedExperience:
    experiencer = generate_user_experience()
    if not experiencer:
        raise
    return SharedExperience(
        experiencers=[
            (experiencer, ExperienceFormat.UNKNOWN)
        ],
        structure=ExperienceStructure(
            compute_environment=HumanBrain(
                id=experiencer.ego.name
            ),
            inputs=[
                RootIntegratedInput(
                    description="perception, etc"
                )
            ],
            outputs=[
                RootIntegratedOutput(
                    description="infinitely internalist output"
                )
            ],
            action_mappings=[
                ActionMapping(
                    mapping=[
                        (Input(
                            description="the right-before heads"
                        ),
                        Action(
                            description="a specified and monitorable activity (e.g. finger curving)"
                        ))
                    ]
                )
            ]
        )
    )