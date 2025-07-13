import os
import argparse

def split_concatenated_file(input_path, output_base="."):
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = content.split("===FILE_START=== ")
    for entry in entries:
        if not entry.strip():
            continue

        try:
            header, *code_lines = entry.split("\n")
            relative_path = header.strip().rstrip("/\\")  # Remove trailing slash/backslash

            # Skip directories or junk names
            # if not relative_path.endswith(".py"):
            #     print(f"⚠️ Skipping non-.py entry: {relative_path}")
            #     continue

            code = "\n".join(code_lines)
            output_path = os.path.join(output_base, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(code)
            print(f"✅ Restored: {output_path}")

        except Exception as e:
            print(f"❌ Error processing entry starting with {entry[:60]}...\n{e}")

def main():
    parser = argparse.ArgumentParser(description="Safely split concatenated .py file into original files.")
    parser.add_argument("input", help="Input file to split.")
    parser.add_argument("-o", "--output", default=".", help="Output base folder.")
    args = parser.parse_args()

    split_concatenated_file(args.input, args.output)

if __name__ == "__main__":
    main()
