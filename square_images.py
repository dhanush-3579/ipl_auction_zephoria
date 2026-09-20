from PIL import Image
import os

input_folder = "ipl_player_images"
output_folder = "ipl_player_images_square"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)

    try:
        img = Image.open(input_path).convert("RGB")

        width, height = img.size
        size = max(width, height)

        square = Image.new("RGB", (size, size), "white")

        x = (size - width) // 2
        y = (size - height) // 2

        square.paste(img, (x, y))

        square.save(output_path, quality=95)

        print(f"Processed: {filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

print("\nAll images converted to 1:1 ratio successfully!")