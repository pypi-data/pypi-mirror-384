from pathlib import Path

from rich import print

from tesseract_core import Tesseract

here = Path(__file__).parent.resolve()
input_path = Path("./testdata")
output_path = Path("./output")

# these are relative to input_path
data = [
    "sample_0.json",
    "sample_1.json",
    "sample_2.json",
    "sample_3.json",
    "sample_4.json",
    "sample_5.json",
    "sample_6.json",
    "sample_7.json",
    "sample_8.json",
    "sample_9.json",
]

with Tesseract.from_tesseract_api(
    "tesseract_api.py", input_path=input_path, output_path=output_path
) as tess:
    result = tess.apply({"data": data})
    print(result)
    assert all((output_path / p).exists() for p in result["data"])


with Tesseract.from_image(
    "filereference",
    input_path=input_path,
    output_path=output_path,
) as tess:
    result = tess.apply({"data": data})
    print(result)
    assert all((output_path / p).exists() for p in result["data"])
