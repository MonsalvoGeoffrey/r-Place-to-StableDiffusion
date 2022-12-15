import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline
from random import randint, choice
from typing import Any
import os

torch.set_default_tensor_type(torch.cuda.HalfTensor)








model_id = "CompVis/stable-diffusion-v1-4"
device = "cuda"


model_list = [
    "CompVis/stable-diffusion-v1-4",
    "./stable-diffusion-v1-4",
    "runwayml/stable-diffusion-v1-5",
    "./stable-diffusion-v1-5",
    #"prompthero/midjourney-v4-diffusion",
    #"./midjourney-v4-diffusion",
    "prompthero/openjourney",
    "./openjourney",
    ]


print("Model List".center(50, "-"))
print("1. Stable Diffusion 1.4 (from Huggingface)")
print("2. Stable Diffusion 1.4 (local)")
print("3. Stable Diffusion 1.5 (from Huggingface)")
print("4. Stable Diffusion 1.5 (local)")
print("5. Openjourney (from Huggingface)")
print("6. Openjourney (local)")
model_choice = int(input(f"Which model would you like to load ? [1-{len(model_list)}] "))
if model_choice < 1 or model_choice > len(model_list):
    raise ValueError(f"model_choice must be within 1 to {len(model_list)}. Not {model_choice}")
print("")
model_id = model_list[model_choice-1]
print(f"Model ID: {model_id}")
print("")

is_midjourney = model_choice in (5,6,)







### Load The Model
pipe: Any = StableDiffusionImg2ImgPipeline.from_pretrained(model_id, torch_dtype=torch.float16, revision="fp16", use_auth_token=True)

# pipe = pipe.to(device)
pipe.enable_attention_slicing() # required to fit in 4GB VRAM




### Disable NSFW filter (too many false positive)
def dummy(images, **kwargs): return images, False
pipe.safety_checker = dummy













### Load both final canvas of r/Place, converted to RGB since StableDiffusion doesn't support the alpha channel
places = (Image.open("place.png").convert("RGB"),Image.open("place2.png").convert("RGB"))






def slice_place(places: tuple[Image.Image, ...]):
    """Choose a random canvas from the argument, and return a random 64x64 slice from it resized to 512x512"""
    place = choice(places)
    original_size = place.size
    target_size = (32, 32)

    # Choose a random top-left coordinate for the slice
    sliced_image = (randint(0, original_size[0]-target_size[0]), randint(0, original_size[1]-target_size[1]))

    sliced_place = place.crop( (sliced_image[0], sliced_image[1], sliced_image[0]+target_size[0], sliced_image[1]+target_size[1]) )
    sliced_place = sliced_place.resize((512, 512), Image.Resampling.NEAREST)
    return sliced_place



def generate(init_image: Image.Image, recursion=0) -> Image.Image:
    """
        Generate an image from 'init_image' with no text prompt.
        If 'recursion' is over 0, the output will be passed as the next input that many times
    """
    image: Image.Image = pipe("mdjrny-v4 style" if is_midjourney else "", init_image=init_image, strengh=0.05, guidance_scale=7.5).images[0]
    if recursion > 0:
        return generate(image, recursion=recursion-1)
    return image





def stich_generate(init_image: Image.Image, recursion=0, stich=None):
    """
        Mimic the generate function, but also return an image containing each steps of the generation
    """
    if not stich:
        stich = init_image
    image = generate(init_image)

    # Add each output to the right of the stiched image
    new_stich = Image.new("RGB", (image.size[0]+stich.size[0], image.size[1]))
    new_stich.paste(stich, (0,0))
    new_stich.paste(image, (stich.size[0],0))

    if recursion > 0:
        return stich_generate(init_image=image, recursion=recursion-1, stich=new_stich)
    return image, new_stich






target_dir = "outputs"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)


def make_image():
    """
        Main function
        Generate an image from a random 32x32 slice of a r/place canvas
        Saves it as well as the original to the output directory
    """
    counter = len(os.listdir(target_dir)) // 3
    init_image = slice_place(places)
    init_image.save(f"{target_dir}/{counter}_original.png")
    image, stich = stich_generate(init_image, 0 if is_midjourney else 3)
    image.save(f"{target_dir}/{counter}_generated.png")
    stich.save(f"{target_dir}/{counter}_stich.png")



if __name__ == "__main__":
    while input("Would you like to generate an image? (y/N) ") not in "nN" :
        make_image()









