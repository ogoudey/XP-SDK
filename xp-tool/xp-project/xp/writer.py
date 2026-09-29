from concepts.experiencer import Experiencer
from concepts.experience_format import ExperienceFormat
from concepts.capability_model import CapabilityModel
from concepts.compute_environment import ComputeEnvironment
from concepts.ego import Ego, HumanEgo, FutureEgo
from concepts.experience_format import ExperienceFormat
from concepts.human import HumanBrain
from concepts.computer import Computer
from concepts.experience_dna import ExperienceDNA
from concepts.capability_model import RootIntegratedOutput, RootIntegratedInput
from concepts.capability_model import ActionMapping, Input, Action
from concepts.sovereignty import Sovereignty

from concepts.experience import SharedExperience, ComputeStructure, Experience

template_experience = SharedExperience(
    egos=[
        HumanEgo(
            codebase="human_nature",
            capability_claims=[
                "idk"
            ],
            id="olin2822"
        )
    ],
    data=[
        Experience(
            format=ExperienceFormat.METAPHYSICAL,
            dna=ExperienceDNA(
                value="regular human experience"
            ),
            sovereignties=[
                Sovereignty(
                    ego_id="olin2822",
                    role="owner (private)",
                )
            ]
        )            
    ],
    structure=ComputeStructure(
        compute_environments=[
            HumanBrain(
                id="olin2822",
                capability_models=[
                    CapabilityModel(
                        id="idk",
                        inputs=[
                            RootIntegratedInput(
                                description="everything that's an input to a human brain"
                            )
                        ],
                        outputs=[
                            RootIntegratedOutput(
                                description="everything that's an output of (root) human brain"
                            )
                        ],
                        action_mappings=[
                            ActionMapping(
                                mapping=[
                                    (Input(
                                        description="what I output"
                                    ),
                                    Action(
                                        description="that actually does anything (e.g. finger taps)"
                                    ))
                                ]
                            )
                        ]
                    )
                ]
            )
            
        ]
    )
)