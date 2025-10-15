## Installation

!!! note
    Ollama needs to be installed and running in order to use `oterm`. Please follow the [Ollama Installation Guide](https://github.com/ollama/ollama?tab=readme-ov-file#ollama).

Using `uvx`:

```bash
uvx oterm
```

Using `brew` for MacOS:

```bash
brew install oterm
```

!!! note

    Since version `0.13.1`, `oterm` is in the official `homebrew/core` repository. If you have installed `oterm` by tapping  `ggozad/formulas` you can now remove the tap and reinstall `oterm`.

Using `yay` (or any AUR helper) for Arch Linux, thanks goes to [Daniel Chesters](https://github.com/DanielChesters) for maintaining the package:

```bash
yay -S oterm
```

Using `nix-env` on NixOs, thanks goes to [Gaël James](https://github.com/gaelj) for maintaining the package:

```bash
nix-env -iA nixpkgs.oterm
```

Using `pip`:

```bash
pip install oterm
```

Using `pkg` for FreeBSD, thanks goes to [Nicola Vitale](https://github.com/nivit) for maintaining the package:

```bash
pkg install misc/py-oterm
```

Using [`x-cmd`](https://x-cmd.com/install/oterm):

```bash
x install oterm
```

## Updating oterm

To update oterm to the latest version, you can use the same method you used for installation:

Using `uvx`:

```bash
uvx oterm@latest
```

Using `brew` for MacOS:

```bash
brew upgrade oterm
```
Using 'yay' (or any AUR helper) for Arch Linux:

```bash
yay -Syu oterm
```
Using `pip`:

```bash
pip install --upgrade oterm
```

Using `pkg` for FreeBSD:

```bash
pkg upgrade misc/py-oterm
```
