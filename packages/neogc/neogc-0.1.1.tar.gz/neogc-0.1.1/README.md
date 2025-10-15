## NeoGC CLI

### What is the NeoGC CLI?

`neogc` (the NeoGC CLI) is a reimplementation of `ngc`, the CLI for NGC (NVIDIA GPU Cloud), using [Typer](https://github.com/fastapi/typer), a library *"for building CLI applications that users will love using and developers will love creating"*.

### Dependencies

Python version `3.13.x` has been used for the development of this project.

Additionally:
```
pip install ngcsdk
pip install typer
```

### Automatic Python venv loading on cd

#### macOS
```
brew install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bash_profile
cd neogvc/
```

### Configuring NeoGC CLI

```
neogc config set
```

### TODO

What improvements am I aiming at with NeoGC CLI over NGC CLI?
- porting to Typer, which is the core goal
- easier choice of output format, org, team and ace during `neogc config set` rather than the current way