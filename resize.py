import sys

from PIL import Image

new_width =104
i = Image.open(sys.argv[1])
i.resize((new_width, int(i.size[1] * new_width / i.size[0])), Image.Resampling.LANCZOS).save(
    sys.argv[2]
)
