import os
import re
import sys
import base64
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def extract_number(description: str) -> str:
    match = re.search(r"\d+", description)
    return match.group(0) if match else "unknown"


def generate_prompt(description: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Create a detailed, vivid image generation prompt based on this description: {description}. Return only the prompt, no explanation.",
    )
    return response.text.strip()


def generate_image(prompt: str, number: str, output_dir: Path) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = part.inline_data.mime_type.split("/")[1]
            filename = output_dir / f"image_{number}.{ext}"
            image_data = base64.b64decode(part.inline_data.data)
            with open(filename, "wb") as f:
                f.write(image_data)
            return str(filename)

    raise RuntimeError("No image returned by Gemini")


def process_description(description: str, output_dir: Path) -> tuple[str, str | None, str | None]:
    description = description.strip()
    if not description:
        return description, None, None

    number = extract_number(description)
    try:
        prompt = generate_prompt(description)
        filename = generate_image(prompt, number, output_dir)
        return description, filename, None
    except Exception as e:
        return description, None, str(e)


def load_descriptions(source: str) -> list[str]:
    path = Path(source)
    if path.exists():
        lines = path.read_text().splitlines()
        return [l.strip() for l in lines if l.strip()]
    # treat as single inline description
    return [source]


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate.py descriptions.txt        # file with one description per line")
        print("  python generate.py 'a cat, image 5'        # single inline description")
        sys.exit(1)

    source = " ".join(sys.argv[1:])
    descriptions = load_descriptions(source)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    total = len(descriptions)
    print(f"Processing {total} description(s) → saving to '{output_dir}/'\n")

    results: list[tuple[str, str | None, str | None]] = []

    # Use up to 5 workers — Gemini rate limits are generous but not unlimited
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_description, desc, output_dir): desc
            for desc in descriptions
        }
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            desc, filename, error = future.result()
            number = extract_number(desc)
            if error:
                print(f"[{i}/{total}] FAILED  #{number} — {error}")
            else:
                print(f"[{i}/{total}] OK      #{number} → {filename}")
            results.append((desc, filename, error))

    success = sum(1 for _, f, _ in results if f)
    failed = total - success
    print(f"\nDone: {success} succeeded, {failed} failed.")


if __name__ == "__main__":
    main()
