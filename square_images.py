from PIL import Image
import os

input_folder = "ipl_player_images_original"
output_folder = "ipl_player_images_final"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(
        output_folder,
        os.path.splitext(filename)[0] + ".png"
    )

    img = Image.open(input_path).convert("RGBA")

    width, height = img.size
    size = max(width, height)

    # White 1:1 canvas
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))

    # Keep player proportions unchanged
    x = (size - width) // 2
    y = (size - height) // 2

    canvas.alpha_composite(img, (x, y))

    canvas.convert("RGB").save(
        output_path,
        "PNG",
        optimize=True
    )

print("All images converted to white-background 1:1 format!")