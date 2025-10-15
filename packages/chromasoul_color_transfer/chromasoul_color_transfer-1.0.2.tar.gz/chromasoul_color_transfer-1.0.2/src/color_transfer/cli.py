#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from color_transfer.libs import TransferFactory
from color_transfer.utils import ImageUtils


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Color Transfer Tool - Transfer color style from reference image to input image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with mean_std transfer method
  color_transfer --input input.jpg --reference reference.jpg --output result.jpg
  
  # Specify transfer method
  color_transfer --input input.jpg --reference reference.jpg --output result.jpg --method mean_std
  
  # Use short options
  color_transfer -i input.jpg -r reference.jpg -o result.jpg -m mean_std
  
  # Enable verbose output
  color_transfer -i input.jpg -r reference.jpg -o result.jpg -v
        """,
    )

    # Required arguments
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="Path to input image file"
    )

    parser.add_argument(
        "--reference",
        "-r",
        type=str,
        required=True,
        help="Path to reference image file (source of color style)",
    )

    parser.add_argument(
        "--output", "-o", type=str, required=True, help="Path to output image file"
    )

    # Optional arguments
    parser.add_argument(
        "--method",
        "-m",
        type=str,
        default="mean_std",
        choices=TransferFactory.transfer_map.keys(),
        help="Color transfer method to use (default: mean_std)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def validate_files(input_path, reference_path, output_dir):
    """Validate input and reference files exist, and output directory is writable."""

    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check if reference file exists
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference file not found: {reference_path}")

    # Check if output directory is writable
    output_dir = os.path.dirname(output_dir) or "."
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise PermissionError(f"Cannot create output directory: {output_dir} - {e}")

    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f"Output directory is not writable: {output_dir}")


def main():
    """Main function for color transfer command line tool."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Validate files
        validate_files(args.input, args.reference, args.output)

        if args.verbose:
            print(f"Starting color transfer...")
            print(f"Input image: {args.input}")
            print(f"Reference image: {args.reference}")
            print(f"Output image: {args.output}")
            print(f"Transfer method: {args.method}")

        # Initialize image transfer
        transfer = TransferFactory.create(args.method)

        # Load the images
        img_ref = ImageUtils.load_img(args.reference)
        img_input = ImageUtils.load_img(args.input)

        if args.verbose:
            print(f"Reference image shape: {img_ref.shape}")
            print(f"Input image shape: {img_input.shape}")

        # Extract color statistics from reference image
        transfer.extract(img_ref)

        # Apply color transfer to input image
        img_output = transfer.transfer(img_input)

        # Save the result
        ImageUtils.save_img(img_output, args.output)

        if args.verbose:
            print(f"Color transfer completed successfully!")
            print(f"Output saved to: {args.output}")
        else:
            print(f"Color transfer completed. Output saved to: {args.output}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during color transfer: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
