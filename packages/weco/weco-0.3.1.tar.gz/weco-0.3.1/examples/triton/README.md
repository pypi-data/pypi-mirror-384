# Triton Optimization

This example demonstrates using Weco to optimize a causal multi-head self-attention mechanism, a core component of Transformer models, implemented in PyTorch. 
The optimization target is to leverage [Triton](https://github.com/triton-lang/triton) for writing highly efficient GPU code, to accelerate the operation.

## Setup

Install the CLI and dependencies for the example:
```bash
pip install weco torch triton
```

## Run Weco

Now run Weco to optimize your code using Triton:
```bash
weco run --source optimize.py \
     --eval-command "python evaluate.py --solution-path optimize.py" \
     --metric speedup \
     --goal maximize \
     --steps 50 \
     --model o4-mini \
     --additional-instructions "Use triton to optimize the code while ensuring a small max float diff. Maintain the same code format. Do not use any fallbacks. Assume any required dependencies are installed and data is already on the gpu."
```

### Explanation

*   `--source optimize.py`: Specifies the PyTorch self-attention implementation (`optimize.py`) that Weco will optimize.
*   `--eval-command "python evaluate.py --solution-path optimize.py"`: Defines the command to execute the evaluation script. This script benchmarks the generated solution in `optimize.py` against a baseline and outputs the `speedup`.
*   `--metric speedup`: Sets the metric Weco should focus on improving during optimization.
*   `--goal maximize`: Instructs Weco to aim for the highest possible speedup value.
*   `--steps 50`: Determines the number of optimization iterations Weco will perform.
*   `--model o4-mini`: Specifies the large language model to drive the optimization process.
*   `--additional-instructions "..."`: Provides specific guidance to the LLM.

Weco will iteratively modify `optimize.py`, incorporating Triton kernels, guided by the performance feedback (`speedup`) from the evaluation script and the instructions provided.

## Next Steps

After mastering Triton kernels, explore [CUDA Optimization](/examples/cuda/README.md) for even lower-level GPU programming, or check the [CLI Reference](https://docs.weco.ai/cli/cli-reference) to improve the results you get with Weco.
