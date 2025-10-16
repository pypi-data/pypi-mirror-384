# Installation

## Prerequisites

**Python 3.11** or later is required to use the `breathe_design` package.

## Quickstart video

<!-- Wistia iFrame embed (responsive) -->
<div class="wistia_responsive_padding" style="padding:56.25% 0 0 0;position:relative;">
  <div class="wistia_responsive_wrapper" style="height:100%;left:0;position:absolute;top:0;width:100%;">
    <iframe
      src="https://fast.wistia.net/embed/iframe/ctf0z97jiv?videoFoam=true"
      allow="autoplay; fullscreen"
      allowfullscreen
      frameborder="0"
      scrolling="no"
      class="wistia_embed"
      name="wistia_embed"
      style="width:100%;height:100%;position:absolute;top:0;left:0;">
    </iframe>
  </div>
</div>
<script src="https://fast.wistia.net/assets/external/E-v1.js" async></script>

## Installation steps

- Open your terminal or command prompt.
- Navigate to the directory or create new one where you want to setup.
- Run the following command to clone our GitHub repository.

  ```bash
  git clone https://github.com/BreatheBatteries/breathe_design.git .
  ```

 To set up everything in one go, just run `.\setupEnvironment.ps1`

## Alternative installation

 Run following command to create the virtual environment:

  ```bash
  python -m venv myvenv
  ```

  Replace `myvenv` with the desired name for your virtual environment.

- Activate the virtual environment:
  - On **Windows**:
    ```cmd
    myvenv\Scripts\activate
    ```
  - On **macOS/Linux**:
    ```bash
    source myvenv/bin/activate
    ```

  After activating the virtual environment, you'll see `(myenv)` in your terminal prompt to indicate that the environment is active.

- Install the `breathe_design` package in the virtual environment:

  ```
  pip install breathe_design
  ```

## Verifying your installation

Once the installation is complete, you can verify that the package is installed correctly by running the following command in your terminal:

```
python -m pip show breathe_design
```

This will display information about the `breathe_design` package, including its version number.

You can also import the package in a Python script to ensure that it's working correctly:

```python
import breathe_design
```

If there are no errors, the package is imported successfully.
Now you can start using the breathe_design package in your Python in your projects!
