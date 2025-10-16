from sinapsis_core.cli.run_agent_from_config import generic_agent_builder
import time

agent = generic_agent_builder("packages/sinapsis_dfine/src/sinapsis_dfine/configs/inference.yml")
agent.update_template_attribute("DFINEInference", "model_path", "ustc-community/dfine-xlarge-obj365")
agent.reset_state("DFINEInference")
time.sleep(10)