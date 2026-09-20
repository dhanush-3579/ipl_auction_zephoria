import os
from PIL import Image

image_folder = "ipl_player_images"
output_folder = "ipl_player_images_white_bg"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(image_folder):

    if filename.lower().endswith((".png", ".jpg", ".jpeg")):

        input_path = os.path.join(image_folder, filename)
        output_path = os.path.join(output_folder, filename)

        try:
            img = Image.open(input_path).convert("RGBA")

            white_background = Image.new(
                "RGBA",
                img.size,
                (255, 255, 255, 255)
            )

            final_image = Image.alpha_composite(
                white_background,
                img
            )

            final_image = final_image.convert("RGB")
            final_image.save(output_path)

            print(f"Processed: {filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("All images processed successfully!")