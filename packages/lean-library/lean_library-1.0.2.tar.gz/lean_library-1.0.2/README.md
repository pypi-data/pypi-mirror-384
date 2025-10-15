# LeanLibrary
To install LeanLibrary, run
``` sh
uv pip install lean-library
```
install Pantograph
``` sh
uv add git+https://github.com/stanford-centaur/PyPantograph
```
make sure you've installed CUDA-compiled torch,
``` sh
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```
export your Github access token,
``` sh
export GITHUB_ACCESS_TOKEN=<GITHUB_ACCESS_TOKEN>
```
## Example
``` python
from leanlibrary.agent.hf_agent import HFAgent
from leanlibrary.trainer.sft_trainer import SFTTrainer

url = "https://github.com/durant42040/lean4-example"
commit = "005de00d03f1aaa32cb2923d5e3cbaf0b954a192"

trainer = SFTTrainer(
    model_name="deepseek-ai/DeepSeek-Prover-V2-7B",
    output_dir="outputs-deepseek",
    epochs_per_repo=1,
    batch_size=2,
    lr=2e-5,
)

agent = HFAgent(trainer=trainer)
agent.setup_github_repository(url=url, commit=commit)
agent.train()
agent.prove()

```
