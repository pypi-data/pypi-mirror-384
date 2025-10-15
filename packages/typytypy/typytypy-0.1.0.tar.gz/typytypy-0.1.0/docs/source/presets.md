# Available Presets

For use with the {py:func}`use_preset(preset_name) <typytypy.use_preset>` function:

| Preset | Base Delay (`base_delay`) | Delay Range (`delay_range`) | Description |
|--------|------------|-------------|-------------|
| `default` | 0.015s | 0.042s | Standard typing speed |
| `emphasis` | ~0.031s | ~0.099s | Moderate typing speed |
| `slow` | 0.300s | 0.300s | Deliberate, careful |
| `contemplative` | 0.150s | 0.300s | Thoughtful, reflective |
| `nervous` | 0.100s | 0.400s | Anxious, hesitant |
| `average` | 0.120s | 0.240s | Researched human average typing speed |
| `confident` | 0.080s | 0.160s | Steady, professional |
| `robotic` | 0.100s | 0.050s | Mechanical, consistent |
| `chaotic` | 0.007s | 0.993s | Distracted, erratic |

```{tip}
The predefined timing presets shown above, along with their configuration details *(excluding the "Description")*, are also discoverable via the {py:func}`get_available_presets() <typytypy.get_available_presets>` function.
```
