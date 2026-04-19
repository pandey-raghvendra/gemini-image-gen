# gemini-image-gen
Batch image generator using Google Gemini. Give it a list of descriptions and it generates a detailed prompt + image for each one, named by the number in the description.

How it works
Reads descriptions from a .txt file (one per line)
For each description, calls Gemini 2.0 Flash to expand it into a rich image prompt
Feeds that prompt to Gemini 2.0 Flash Preview Image Generation to produce the image
Saves each image to output/image_<number>.<ext> where <number> is extracted from the description
Processes up to 5 descriptions concurrently
Setup
pip install google-genai
export GEMINI_API_KEY=your_key_here
Usage
Batch (30–40 descriptions):

Create descriptions.txt with one description per line:

a serene forest at dawn, image 1
futuristic cityscape at night, image 2
a dog surfing a wave at sunset, image 3
Run:

python generate.py descriptions.txt
Single description:

python generate.py "a cat sitting on the moon, image 7"
Output
Images are saved to the output/ folder (created automatically):

output/
  image_1.png
  image_2.png
  image_3.png
Progress is printed live:

Processing 3 description(s) → saving to 'output/'
[1/3] OK      #1 → output/image_1.png
[2/3] OK      #2 → output/image_2.png
[3/3] FAILED  #3 — No image returned by Gemini
Done: 2 succeeded, 1 failed.
Notes
The number in the filename comes from the first number found in the description. Make sure each description has a unique number to avoid overwriting files.
Workers are capped at 5 to stay within Gemini rate limits. Adjust max_workers in generate.py if needed.
Requires Python 3.10+ (uses str | None union syntax).
