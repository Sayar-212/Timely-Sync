from orchestrator.orchestrator import Orchestrator
from utils.logging_utils import get_logger

logger = get_logger("Main")

if __name__ == "__main__":
    nl_constraints = [
        "Prof. Sharma is only available on Mon S1,S2, Tue S1",
        "Math taught by Prof. Sharma needs 2 periods",
        "Sci taught by Prof. Rao needs 2 periods",
        "Eng taught by Prof. Iyer needs 2 periods",
        "Prefer Math on Mon:S1, Tue:S1",
    ]

    orch = Orchestrator()
    result = orch.run(nl_constraints)

    logger.info("Pipeline finished.")
    logger.info(f"Outputs: {result['outputs']}")
