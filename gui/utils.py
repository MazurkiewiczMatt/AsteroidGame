from PIL import Image

def get_module_image_pil(module):
    """
    Loads the module image as a Pillow Image based on the module's type and level.
    """
    mod_name = module.name
    if mod_name.lower() in ["icepenetrator", "nerva", "explosiveslab", "warpdrive"]:
        mapping = {
            "icepenetrator": "Ice_penetrator",
            "nerva": "NERVA",
            "explosiveslab": "Explosives_lab",
            "warpdrive": "Warp_drive",
        }
        if module.level == 1:
            filename = mapping[mod_name.lower()] + ".png"
        else:
            filename = mapping[mod_name.lower()] + "_upgrade.png"
    else:
        if mod_name.lower() == "launchbay":
            filename = f"Launch_Bay{module.level}.png"
        else:
            filename = f"{mod_name}{module.level}.png"
    try:
        return Image.open(f"gui/modules/{filename}").convert("RGBA"), filename
    except Exception:
        return Image.open("gui/modules/Blank.png").convert("RGBA"), filename
