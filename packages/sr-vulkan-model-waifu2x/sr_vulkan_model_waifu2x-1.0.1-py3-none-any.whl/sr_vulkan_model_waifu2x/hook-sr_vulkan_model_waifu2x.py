import sr_vulkan_model_waifu2x
from pathlib import Path

sr_vulkan_path = Path(sr_vulkan_model_waifu2x.__file__).parent
models_path = sr_vulkan_path / "models"
datas = [(str(models_path), "sr_vulkan_model_waifu2x/models")]
