import re
from typing import Any, Dict, List, Tuple
import random
from copy import deepcopy

from datasets import Dataset, load_dataset, concatenate_datasets

from genrl.data import DataManager
from genrl.logging_utils.global_defs import get_logger
from genrl.misc_utils.utils import generate_md5_hash_id
from genrl.state import GameState, WorldState
from genrl.communication.hivemind.hivemind_backend import HivemindBackend

SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "solver": "You are an expert coding assistant, your job is to provide the highest quality solution to a given problem.  The solution should be easily parseable by a computer. Do not include any additional keys or commentary. The solution must be valid python code. The solution should be executable python, with no other text. do not include any tests or verification, just the solution as a function"
}

def build_prompt(flattened_data: Any) -> Any:
    """
    Top-level mapping function to build prompts for the LLM.
    Defined at module scope to ensure picklability for datasets caching/fingerprinting.
    """
    prompt = [
        {"role": "system", "content": flattened_data["system_prompt"]},
        {"role": "user", "content": flattened_data["user_prompt"]},
    ]
    return {"prompt": prompt}

class CodeGenerationDataManager(DataManager):
    """Data Manager for Code Generation Datasets.

    This class integrates code generation datasets with genrl
    data management framework, providing infinite iteration through reseeding.
    """

    def __init__(
        self,
        system_prompt_id: str = "default",
        batch_size: int = 2,
        local_batch_size: int = 1,
        proposer_batch_size: int = 1,
        **kwargs,
    ):
        """Initialize the CodeGenerationDataManager.

        Args:
        """

        self.system_prompt = SYSTEM_PROMPTS.get(
            system_prompt_id, SYSTEM_PROMPTS["default"]
        )
        self.num_generations = kwargs.get("num_generations", None)
        self.num_transplant_trees = kwargs.get("num_transplant_trees", 1)
        assert self.num_transplant_trees >= 0

        self.local_dataset = load_dataset("google-research-datasets/mbpp", streaming=True)
        self.local_dataset = concatenate_datasets([self.local_dataset['train'], self.local_dataset['test']])

        self.local_batch_size = local_batch_size
        self.batch_size = batch_size
        self.proposer_batch_size = proposer_batch_size
        assert self.local_batch_size + self.proposer_batch_size == self.batch_size, f"Batch sizes must sum to total batch size, got {self.local_batch_size} and {self.proposer_batch_size}"

        self.local_dataset = self.local_dataset.batch(batch_size=self.local_batch_size)
        self.local_dataset_iter = iter(self.local_dataset)

    def initialize(self, backend: HivemindBackend):
        self.backend = backend
        self.peer_id = str(backend.get_id())

    # --- Helper Methods ---
    def state_to_user_prompt(self, state: WorldState) -> str:
        """Convert the state to a user prompt."""
        return state.environment_states["question"]

    def state_to_answer(self, state: WorldState) -> str:
        """Extract the answer from the state."""
        return state.environment_states["answer"]

    def flatten_tree(
        self, inputs: Dict[Any, Dict[Any, List[Tuple[Any]]]], stage: int
    ) -> Tuple[Dict[str, List[Any]], Dict[int, Tuple[int, int, int]]]:

        flattened_input = {
            "system_prompt": [],
            "user_prompt": [],
            "answer": [],
            "metadata": [],
        }
        index_mapping = {}
        cur_idx = 0
        for agent in inputs:
            for batch_id in inputs[agent]:
                for node_idx, state in enumerate(inputs[agent][batch_id]):
                    flattened_input["system_prompt"].append(self.system_prompt)
                    flattened_input["user_prompt"].append(self.state_to_user_prompt(state))
                    flattened_input["answer"].append(self.state_to_answer(state))
                    if "metadata" in state.environment_states:
                        flattened_input["metadata"].append(state.environment_states["metadata"])
                    elif state.metadata is not None:
                        flattened_input["metadata"].append(state.metadata)
                    else:
                        flattened_input["metadata"].append({})

                    index_mapping[cur_idx] = (agent, batch_id, node_idx)
                    cur_idx += 1
        return flattened_input, index_mapping

    def prepare_input(
            self, inputs: Dict[Any, Dict[Any, List[Tuple[Any]]]], stage: int = None
        ) -> Tuple[Dataset, Dict[int, Tuple[int, int, int]]]:
            input_flattened, index_mapping = self.flatten_tree(inputs, stage)
            input_flattened = Dataset.from_dict(input_flattened)
            input_prepared = input_flattened.map(build_prompt)
            return input_prepared, index_mapping

    def prepare_actions(
        self, outputs: Any, index_mapping: Dict[int, Tuple[Any]]
    ) -> Dict[Any, List[List[Any]]]:
        actions = {}
        for idx, model_output in enumerate(outputs):
            agent, batch_id, node_idx = index_mapping[idx]
            if agent not in actions:
                actions[agent] = {}
            if batch_id not in actions[agent]:
                actions[agent][batch_id] = {}
            actions[agent][batch_id][node_idx] = [parse_python_fence(output) for output in model_output]
        return actions

    def to_world_state(
        self,
        node_state: WorldState,
    ) -> WorldState:
        environment_state = node_state.environment_states
        environment_state["prior_stage_input_states"] = deepcopy(node_state)
        opponent_state = None
        personal_state = None
        world_state = WorldState(
            environment_states=environment_state,
            opponent_states=opponent_state,
            personal_states=personal_state,
        )
        return world_state

    def prepare_states(
        self, current_state: GameState, swarm_states: Dict[Any, Any]
    ) -> Dict[Any, Dict[Any, List[Tuple[Any]]]]:
        latest_state = current_state.get_latest_state()
        for agent in latest_state:
            for batch_id in latest_state[agent]:
                for node_idx, node_state in enumerate(latest_state[agent][batch_id]):
                    latest_state[agent][batch_id][node_idx] = (
                        self.to_world_state(node_state)
                    )
        return latest_state


    def prepare_states(
        self, current_state: GameState, swarm_states: Dict[Any, Any]
    ) -> Dict[Any, Dict[Any, List[Tuple[Any]]]]:
        if self.num_transplant_trees > 0:
            trees = current_state.trees
            transplants = self.transplant_trees(
                current_state, swarm_states, self.num_transplant_trees
            )
            for pair in transplants:
                agent, batch_id = pair
                if agent not in trees:
                    trees[agent] = {}
                if batch_id not in trees[agent]:
                    trees[agent][batch_id] = None
                payload = transplants[pair]
                received_states, received_actions, received_metadata = (
                    payload["world_state"],
                    payload["actions"],
                    payload["metadata"],
                )
                world_state = received_states.environment_states
                payload_batch_id = generate_md5_hash_id(world_state["question"])
                assert payload_batch_id == batch_id
                if (
                    trees[agent][batch_id] is None
                ):  # we don't have a tree for this batch item, make one and append actions
                    trees[agent][batch_id] = current_state.game_tree_factory(
                        received_states
                    )
                    trees[agent][batch_id].append_node_actions(
                        stage=current_state.stage, node_idx=0, actions=received_actions
                    )
                    trees[agent][batch_id][current_state.stage][0][
                        "metadata"
                    ] = received_metadata
                else:  # we already have this tree, and actions were appended in run_game_stage()
                    pass
        world_state = current_state.get_latest_state()
        return world_state

    def transplant_trees(
        self,
        current_state: GameState,
        swarm_states: Dict[Any, Any],
        num_transplants: int,
    ) -> Dict[Tuple[Any], Any]:
        # Loop through and return a set of num_transplant transplants to add
        transplants = {}
        for agent in swarm_states:
            if agent not in current_state.trees:
                for batch_id in swarm_states[agent]:
                    for payload in swarm_states[agent][batch_id]:
                        if (
                            self.num_generations
                            and hasattr(payload, "actions")
                            and payload.actions is not None
                            and isinstance(payload.actions, list)
                            and len(payload.actions) == self.num_generations
                        ):
                            transplants[(agent, batch_id)] = payload
        if len(transplants) >= num_transplants:
            keepers = random.sample(list(transplants), num_transplants)
        else:
            keepers = list(transplants)

        return {key: transplants[key] for key in keepers}

    def get_eval_data(self):
        pass

    def get_round_data(self):      

        if self.proposer_batch_size > 0:
            proposer_data = self.backend.get(sub_key="proposer".encode())
            proposer_data = prepare_proposer_batch(proposer_data, self.proposer_batch_size)
        else:
            proposer_data = []
        
        if self.local_batch_size > 0:
            try:
                local_data = next(self.local_dataset_iter)
            except StopIteration:
                self.local_dataset_iter = iter(self.local_dataset)
                local_data = next(self.local_dataset_iter)
            local_data = prepare_local_batch(local_data)
        else:
            local_data = []

        combined_data = local_data + proposer_data
        return combined_data

    def send_response(self, rewards, state):
        objs = []
        for agent_id in state:
            for batch_id in state[agent_id]:
                node_idx = 0 # don't need to send each generation
                node = state[agent_id][batch_id][node_idx]
                proposal_raw = node.personal_states
                dataset = node.environment_states['metadata']['dataset']
                batch_rewards = rewards[agent_id][batch_id][node_idx]

                if dataset != 'proposer':
                    continue
                obj = {
                    'proposal_raw': proposal_raw,
                    'reward': batch_rewards,
                    'dataset': dataset
                }
                objs.append(obj)
        self.backend.put(objs, sub_key="solver".encode())
        
       


def prepare_local_batch(batch) -> list[tuple[int, WorldState]]:
    prompts = batch['text']
    imports = batch['test_setup_code']
    test_lists = batch['test_list']

    tests = []
    for i in range(len(prompts)):
        test_imports, test_list = imports[i], test_lists[i]
        test = test_imports + "\n" + "\n".join(test_list)
        tests.append(test)

    local_data = []
    for prompt, test in zip(prompts, tests):
        # include tests in prompt so that the LM knows what to call its implementation. I know this is kind of cheating
        env_state = {
                    "question": prompt + '\nplease match the function name to the following test\n' + test, 
                    "answer": test,
                    "metadata": {'dataset': 'mbpp'}
        }
        world_state = WorldState(
            environment_states=env_state,
            opponent_states=None,
            personal_states=None,
        )
        proposal_id = generate_md5_hash_id(env_state["question"])
        local_data.append([proposal_id, world_state])

    return local_data

def prepare_proposer_batch(batch: dict[str, list[dict]], batch_size: int) -> list[tuple[int, WorldState]]:
    proposer_data = []
    for proposer_id in batch:
        proposal_list = batch[proposer_id]
        for proposal in proposal_list:
            proposal_question = proposal['proposal_question']
            proposal_tests = proposal['proposal_tests']
            proposal_raw = proposal['proposal_raw']

            env_state = {
                "question": proposal_question,
                "answer": proposal_tests,
                "metadata": {'dataset': 'proposer'}
            }
            world_state = WorldState(
                environment_states=env_state,
                opponent_states=None,
                personal_states=proposal_raw,
            )
            proposal_id = generate_md5_hash_id(env_state["question"])
        
            proposer_data.append([proposal_id, world_state])

            if len(proposer_data) >= batch_size:
                return proposer_data

    return proposer_data

def parse_python_fence(text):
    match = re.search(r'```python(.*?)```', text, re.DOTALL)
    if match:
        python_string = match.group(1).strip()
        return python_string
    return 'raise Exception("No python fence found")'


if __name__ == "__main__":
    dm = CodeGenerationDataManager(batch_size=2, local_batch_size=2, proposer_batch_size=0)
    for i in range(10000):
        batch = dm.get_round_data()
        print(batch)
