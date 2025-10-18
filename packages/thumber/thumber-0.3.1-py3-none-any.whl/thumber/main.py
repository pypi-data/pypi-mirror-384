import argparse
import os

from PIL import Image, ImageFilter


def thumbnail(input_path, final_width, final_height, blur_radius=10):
    img = Image.open(input_path)

    if img.mode == "P" and isinstance(img.info.get("transparency"), bytes):
        img = img.convert("RGBA")

    orig_w, orig_h = img.size
    scale = max(final_width / orig_w, final_height / orig_h)
    bg_width = int(orig_w * scale)
    bg_height = int(orig_h * scale)

    bg = img.resize((bg_width, bg_height), Image.LANCZOS)
    crop_x = (bg_width - final_width) // 2
    crop_y = (bg_height - final_height) // 2
    bg = bg.crop((crop_x, crop_y, crop_x + final_width, crop_y + final_height))

    bg = bg.convert("RGB")

    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    fg = img.copy()
    fg.thumbnail((final_width, final_height), Image.LANCZOS)

    if fg.mode == "P":
        if "transparency" in fg.info:
            fg = fg.convert("RGBA")
        else:
            fg = fg.convert("RGB")

    final_img = bg.copy()
    paste_x = (final_width - fg.width) // 2
    paste_y = (final_height - fg.height) // 2
    final_img.paste(fg, (paste_x, paste_y), fg if fg.mode in ("RGBA", "LA") else None)

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}-thumbnail{ext}"

    final_img.save(output_path)
    print(f"Image saved as {output_path}")

    return final_img


def adapt_aspect_ratio(input_path: str, target_aspect: float, blur_radius: float = 10):
    cover_path = input_path

    cov_ext = os.path.splitext(cover_path)[1][1:]

    with Image.open(cover_path) as img:
        width, height = img.size

    print(f"Original Dimensions: {width} x {height}")

    current_ratio = width / height

    ratio = current_ratio
    is_ratio_right = ratio == target_aspect

    print(f"Current Ratio: {ratio} (Target: {target_aspect})")
    print(f"Correct aspect ratio: {is_ratio_right}")

    if not is_ratio_right:
        if target_aspect == 1:
            if current_ratio > 1:
                width = height
            else:
                height = width
        else:
            if current_ratio < 1:
                height = width

            width = height * target_aspect

        resize_width = int(width)
        resize_height = int(height)
        print(f"Resizing to: {resize_width} x {resize_height}")

        thumbnail(cover_path, resize_width, resize_height, blur_radius)

    else:
        print("Cover image already has the target aspect ratio. No changes made.")


def crop_image(input_path, crop_width=None, crop_height=None, target_ratio=None):
    img = Image.open(input_path)
    orig_width, orig_height = img.size

    if target_ratio is not None:
        # Calculate crop dimensions based on the target ratio.
        current_ratio = orig_width / orig_height

        if current_ratio > target_ratio:
            new_width = int(target_ratio * orig_height)
            new_height = orig_height
        else:
            new_width = orig_width
            new_height = int(orig_width / target_ratio)

        left = (orig_width - new_width) // 2
        top = (orig_height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        cropped_img = img.crop((left, top, right, bottom))

    elif crop_width is not None and crop_height is not None:
        # Scale the image so that it covers the desired crop dimensions.
        scale = max(crop_width / orig_width, crop_height / orig_height)
        new_size = (int(orig_width * scale), int(orig_height * scale))
        img_resized = img.resize(new_size, Image.LANCZOS)
        new_width, new_height = img_resized.size
        left = (new_width - crop_width) // 2
        top = (new_height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height
        cropped_img = img_resized.crop((left, top, right, bottom))

    else:
        print(
            "Error: Must provide either target_ratio or both crop_width and crop_height."
        )
        return None

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}-thumbnail{ext}"
    cropped_img.save(output_path)
    print(f"Cropped image saved as {output_path}")
    return cropped_img


def main():
    parser = argparse.ArgumentParser(
        description="Thumber: Choose dimensions or adapt to a target aspect ratio. Either crop or resize with blur."
    )
    subparsers = parser.add_subparsers(
        dest="mode", required=True, help="Mode of operation"
    )

    dimensions_parser = subparsers.add_parser(
        "dimensions", help="Resize an image to dimensions"
    )
    dimensions_parser.add_argument("input_path", help="Input image file path")
    dimensions_parser.add_argument("width", type=int, help="Final width in pixels")
    dimensions_parser.add_argument("height", type=int, help="Final height in pixels")
    dimensions_parser.add_argument(
        "--blur", type=float, default=10, help="Gaussian blur radius (default: 10)"
    )

    aspect_parser = subparsers.add_parser(
        "aspect", help="Adapt a cover image to a target aspect ratio with blur effect"
    )
    aspect_parser.add_argument("input_path", help="Input image file path")
    aspect_parser.add_argument(
        "target_aspect", type=float, help="Target aspect ratio (e.g., 1 or 1.78)"
    )
    aspect_parser.add_argument(
        "--blur", type=float, default=10, help="Gaussian blur radius (default: 10)"
    )

    # Crop (simple cropping without blur).
    crop_parser = subparsers.add_parser(
        "crop", help="Crop an image to specified dimensions or aspect ratio"
    )
    crop_parser.add_argument("input_path", help="Input image file path")
    crop_parser.add_argument(
        "--width", type=int, help="Crop width in pixels (if cropping by dimensions)"
    )
    crop_parser.add_argument(
        "--height", type=int, help="Crop height in pixels (if cropping by dimensions)"
    )
    crop_parser.add_argument(
        "--ratio",
        type=float,
        help="Target aspect ratio for cropping (width/height). "
        "If provided, takes precedence over width/height.",
    )

    args = parser.parse_args()

    if args.mode == "dimensions":
        thumbnail(
            input_path=args.input_path,
            final_width=args.width,
            final_height=args.height,
            blur_radius=args.blur,
        )

    elif args.mode == "aspect":
        adapt_aspect_ratio(
            input_path=args.input_path,
            target_aspect=args.target_aspect,
            blur_radius=args.blur,
        )

    elif args.mode == "crop":
        crop_image(
            input_path=args.input_path,
            crop_width=args.width,
            crop_height=args.height,
            target_ratio=args.ratio,
        )


if __name__ == "__main__":
    main()
